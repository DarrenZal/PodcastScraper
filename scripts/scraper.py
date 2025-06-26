import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import re
from typing import List, Dict, Any

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import pandas as pd
from bs4 import BeautifulSoup


class YonEarthPodcastScraper:
    def __init__(self):
        self.base_url = "https://yonearth.org"
        self.podcast_list_url = "https://yonearth.org/community-podcast/"
        self.data_dir = Path(__file__).parent.parent / "data"
        self.episode_urls = []
        
        # Create necessary directories
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "json").mkdir(exist_ok=True)
        (self.data_dir / "markdown").mkdir(exist_ok=True)
        (self.data_dir / "csv").mkdir(exist_ok=True)
        
    async def discover_episode_urls(self) -> List[str]:
        """Discover all episode URLs from the main podcast page and pagination"""
        print("Discovering episode URLs...")
        
        # Configure browser with JavaScript enabled
        browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Scrape main page first (page 1)
            await self._scrape_page_with_js(crawler, self.podcast_list_url, 1)
            
            # Use JavaScript to navigate through pagination
            # Based on analysis, we need to check multiple pages to get all episodes
            for page_num in range(2, 10):  # Check pages 2-9 to be thorough
                await self._scrape_page_with_js(crawler, self.podcast_list_url, page_num)
                
        print(f"Found {len(self.episode_urls)} total unique episode URLs")
        
        # Save URLs for reference
        with open(self.data_dir / 'episode_urls.json', 'w') as f:
            json.dump(self.episode_urls, f, indent=2)
                
        return self.episode_urls
    
    async def _scrape_page_with_js(self, crawler, base_url: str, page_num: int):
        """Helper method to scrape a page using JavaScript pagination"""
        print(f"Scraping page {page_num} using JavaScript navigation")
        
        # JavaScript to click the pagination button for the specific page
        js_code = f"""
        // Wait for pagination to be available
        await new Promise(resolve => {{
            const checkPagination = () => {{
                const pagination = document.querySelector('.tcb-pagination');
                if (pagination) {{
                    resolve();
                }} else {{
                    setTimeout(checkPagination, 100);
                }}
            }};
            checkPagination();
        }});
        
        // Find and click the page {page_num} button
        const pageButtons = document.querySelectorAll('.tcb-pagination-number a');
        let targetButton = null;
        
        for (let button of pageButtons) {{
            if (button.textContent.trim() === '{page_num}') {{
                targetButton = button;
                break;
            }}
        }}
        
        if (targetButton) {{
            targetButton.click();
            
            // Wait for content to load after clicking
            await new Promise(resolve => {{
                setTimeout(resolve, 3000);
            }});
            
            // Wait for new content to appear
            await new Promise(resolve => {{
                const checkContent = () => {{
                    const articles = document.querySelectorAll('.tcb-post-list article');
                    if (articles.length > 0) {{
                        resolve();
                    }} else {{
                        setTimeout(checkContent, 100);
                    }}
                }};
                checkContent();
            }});
        }}
        """
        
        config = CrawlerRunConfig(
            wait_for=".tcb-post-list article",  # Wait for podcast articles to appear
            wait_until="domcontentloaded",
            delay_before_return_html=2.0,
            js_code=js_code if page_num > 1 else None,  # Only use JS for pages > 1
            cache_mode=CacheMode.BYPASS,
            verbose=True
        )
        
        result = await crawler.arun(base_url, config=config)
        
        if result.success:
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Find all episode links using the actual site structure
            episode_links = soup.find_all('a', {
                'href': re.compile(r'/podcast/episode-\d+'),
                'class': 'tve-dynamic-link'
            })
            
            # Fallback to any episode links if the main selector doesn't work
            if not episode_links:
                episode_links = soup.find_all('a', href=re.compile(r'/podcast/episode-\d+'))
            
            page_urls = []
            for link in episode_links:
                url_found = link.get('href')
                if url_found and not url_found.startswith('http'):
                    url_found = self.base_url + url_found
                if url_found and url_found not in self.episode_urls:
                    self.episode_urls.append(url_found)
                    page_urls.append(url_found)
            
            print(f"Found {len(page_urls)} episode URLs on page {page_num}")
                
        else:
            print(f"Failed to crawl page {page_num}: {getattr(result, 'error_message', 'Unknown error')}")
            print(f"Status code: {getattr(result, 'status_code', 'Unknown')}")
            print(f"Success: {result.success}")
    
    def get_episode_extraction_schema(self) -> dict:
        """Define the extraction schema for episode pages based on actual HTML structure"""
        return {
            "name": "episode_data",
            "baseSelector": "body",  # Use body as base since content is scattered
            "fields": [
                {
                    "name": "title",
                    "selector": "h1",  # First h1 contains episode title
                    "type": "text"
                },
                {
                    "name": "audio_url",
                    "selector": "audio.clip source",
                    "type": "attribute",
                    "attribute": "src"
                },
                {
                    "name": "publish_date",
                    "selector": "p",  # Will parse this manually
                    "type": "text"
                }
            ]
        }
    
    async def scrape_episode(self, url: str) -> Dict[str, Any]:
        """Scrape a single episode page"""
        browser_config = BrowserConfig(headless=True)
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(
                    schema=self.get_episode_extraction_schema()
                ),
                wait_until="domcontentloaded",
                delay_before_return_html=2.0,  # Wait 2 seconds
                cache_mode=CacheMode.BYPASS
            )
            
            result = await crawler.arun(url, config=config)
            
            if result.success and result.extracted_content:
                extracted_data = json.loads(result.extracted_content)
                
                # Handle case where extraction returns a list
                if isinstance(extracted_data, list) and extracted_data:
                    episode_data = extracted_data[0]
                elif isinstance(extracted_data, dict):
                    episode_data = extracted_data
                else:
                    print(f"Unexpected data format for {url}: {type(extracted_data)}")
                    return None
                    
                episode_data['url'] = url
                
                # Extract episode number from URL if not found in title
                if not episode_data.get('episode_number'):
                    match = re.search(r'episode-(\d+)', url)
                    if match:
                        episode_data['episode_number'] = int(match.group(1))
                
                # Extract detailed content using BeautifulSoup for better parsing
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Extract publish date
                date_p = soup.find('p', string=lambda text: text and ('2024' in text or '2023' in text) and ('pm' in text or 'am' in text))
                if date_p:
                    episode_data['publish_date'] = date_p.get_text(strip=True)
                else:
                    episode_data['publish_date'] = 'Unknown'
                
                # Extract episode subtitle/theme and description with enhanced fallbacks
                episode_data['subtitle'] = ''
                episode_data['description'] = ''
                
                # Method 1: Look for the subtitle (first h2 heading)
                first_h2 = soup.find('h2')
                if first_h2:
                    subtitle_text = first_h2.get_text(strip=True)
                    episode_data['subtitle'] = subtitle_text
                    
                    # Method 1a: Get description paragraph immediately after subtitle
                    desc_p = first_h2.find_next_sibling('p')
                    if desc_p and desc_p.get_text(strip=True):
                        episode_data['description'] = desc_p.get_text(strip=True)
                    else:
                        # Method 1b: Look for next paragraph within a few siblings
                        current = first_h2.find_next_sibling()
                        attempts = 0
                        while current and attempts < 5:
                            if current.name == 'p' and current.get_text(strip=True):
                                text = current.get_text(strip=True)
                                if len(text) > 50 and 'cart' not in text.lower():
                                    episode_data['description'] = text
                                    break
                            current = current.find_next_sibling()
                            attempts += 1
                
                # Method 2: Alternative subtitle extraction if first method failed
                if not episode_data['subtitle']:
                    # Look for h2 with specific classes or patterns
                    alt_h2 = soup.find('h2', class_='wp-block-heading') or soup.find('h2', {'id': re.compile(r'.*episode.*', re.I)})
                    if alt_h2:
                        episode_data['subtitle'] = alt_h2.get_text(strip=True)
                
                # Method 3: Enhanced description fallback search
                if not episode_data['description']:
                    # Look for substantial paragraphs in the main content area
                    content_divs = soup.find_all('div', class_=['entry-content', 'post-content', 'content', 'tcb-post-content'])
                    for div in content_divs:
                        paras = div.find_all('p')
                        for p in paras:
                            text = p.get_text(strip=True)
                            # More specific filtering for description paragraphs
                            if (text and len(text) > 100 and 
                                'cart' not in text.lower() and 
                                'comments' not in text.lower() and
                                'transcript' not in text.lower() and
                                'sponsors' not in text.lower() and
                                not text.startswith('About ') and
                                ':' in text):  # Often descriptions have time stamps or colons
                                episode_data['description'] = text
                                break
                        if episode_data['description']:
                            break
                    
                    # Last resort: any substantial paragraph
                    if not episode_data['description']:
                        all_paras = soup.find_all('p')
                        for p in all_paras:
                            text = p.get_text(strip=True)
                            if (text and len(text) > 100 and 
                                'cart' not in text.lower() and 
                                'comments' not in text.lower() and
                                'podcast' in text.lower()):  # Likely episode description
                                episode_data['description'] = text
                                break
                
                # Extract About sections with enhanced fallback logic
                about_sections = {}
                
                # Method 1: Standard about headings with wp-block-heading class
                about_headings = soup.find_all('h2', class_='wp-block-heading', string=lambda text: text and 'About' in text)
                
                # Method 2: Fallback - any h2 with 'About' in text (different class or no class)
                if not about_headings:
                    about_headings = soup.find_all('h2', string=lambda text: text and 'About' in text)
                
                # Method 3: Look for h3 or h4 About headings as fallback
                if not about_headings:
                    about_headings = soup.find_all(['h3', 'h4'], string=lambda text: text and 'About' in text)
                
                for heading in about_headings:
                    section_name = heading.get_text(strip=True).replace('About ', '').lower().replace(' ', '_')
                    
                    # Method 1: Look for immediate next paragraph sibling
                    next_p = heading.find_next_sibling('p')
                    if next_p and next_p.get_text(strip=True):
                        about_sections[f'about_{section_name}'] = next_p.get_text(strip=True)
                    else:
                        # Method 2: Look for paragraph within next few siblings
                        current = heading.find_next_sibling()
                        attempts = 0
                        while current and attempts < 5:
                            if current.name == 'p' and current.get_text(strip=True):
                                text = current.get_text(strip=True)
                                if len(text) > 20:  # Reasonable about section length
                                    about_sections[f'about_{section_name}'] = text
                                    break
                            elif current.name in ['div', 'span'] and current.get_text(strip=True):
                                # Sometimes content is in div containers
                                text = current.get_text(strip=True)
                                if len(text) > 20:
                                    about_sections[f'about_{section_name}'] = text
                                    break
                            current = current.find_next_sibling()
                            attempts += 1
                            
                        # Method 3: If still not found, look for content in parent container
                        if f'about_{section_name}' not in about_sections:
                            parent = heading.parent
                            if parent:
                                # Look for text content after the heading within the same container
                                heading_index = list(parent.children).index(heading)
                                for i, sibling in enumerate(list(parent.children)[heading_index+1:]):
                                    if hasattr(sibling, 'get_text') and sibling.get_text(strip=True):
                                        text = sibling.get_text(strip=True)
                                        if len(text) > 20:
                                            about_sections[f'about_{section_name}'] = text
                                            break
                
                episode_data['about_sections'] = about_sections
                
                # Extract sponsors section
                sponsors_header = soup.find('h2', class_='wp-block-heading', string=lambda text: text and 'Sponsors' in text)
                if sponsors_header:
                    sponsors_p = sponsors_header.find_next_sibling('p')
                    if sponsors_p:
                        episode_data['sponsors'] = sponsors_p.get_text(strip=True)
                
                # Extract full transcript with enhanced fallback logic
                episode_data['full_transcript'] = ''
                
                # Method 1: Standard transcript header with wp-block-heading class
                transcript_header = soup.find('h2', class_='wp-block-heading', string=lambda text: text and 'Transcript' in text)
                
                # Method 2: Fallback - any h2 with 'Transcript' in text
                if not transcript_header:
                    transcript_header = soup.find('h2', string=lambda text: text and 'Transcript' in text)
                
                # Method 3: Look for h3 transcript headers
                if not transcript_header:
                    transcript_header = soup.find('h3', string=lambda text: text and 'Transcript' in text)
                
                if transcript_header:
                    transcript_paras = []
                    current = transcript_header.find_next_sibling()
                    
                    # Extract all paragraphs after transcript header until next heading
                    while current:
                        if current.name == 'p' and current.get_text(strip=True):
                            text = current.get_text(strip=True)
                            # Filter out navigation/UI text that might be mixed in
                            if (len(text) > 10 and 
                                'cart' not in text.lower() and 
                                'comments' not in text.lower() and
                                'related episodes' not in text.lower()):
                                transcript_paras.append(text)
                        elif current.name in ['h2', 'h3', 'h4'] and current.get_text(strip=True):
                            # Stop at next heading
                            break
                        elif current.name == 'div' and current.get_text(strip=True):
                            # Sometimes transcript content is in div blocks
                            text = current.get_text(strip=True)
                            if len(text) > 50:  # Substantial content
                                transcript_paras.append(text)
                        current = current.find_next_sibling()
                    
                    if transcript_paras:
                        episode_data['full_transcript'] = '\n\n'.join(transcript_paras)
                
                # Method 4: Alternative transcript extraction - look for content with speaker patterns
                if not episode_data['full_transcript']:
                    # Look for paragraphs that contain common transcript patterns
                    all_paras = soup.find_all('p')
                    transcript_candidates = []
                    
                    for p in all_paras:
                        text = p.get_text(strip=True)
                        # Check for transcript-like patterns (timestamps, speaker names, etc.)
                        if (text and len(text) > 50 and
                            (re.search(r'\d{1,2}:\d{2}', text) or  # Timestamps like 12:34
                             re.search(r'[A-Z][a-z]+ [A-Z][a-z]+:', text) or  # Speaker names like "John Smith:"
                             re.search(r'[A-Z]{2,}:', text) or  # Abbreviated names like "JS:"
                             'Aaron William Perry:' in text or  # Host name
                             text.count(':') >= 2)):  # Multiple colons suggesting dialogue
                            transcript_candidates.append(text)
                    
                    # If we found transcript-like content, use it
                    if len(transcript_candidates) >= 5:  # Need substantial content
                        episode_data['full_transcript'] = '\n\n'.join(transcript_candidates)
                
                # Extract related episodes
                resources_header = soup.find('h2', class_='wp-block-heading', string=lambda text: text and 'Resources' in text)
                if resources_header:
                    related_episodes = []
                    current = resources_header.find_next_sibling()
                    while current and current.name == 'p':
                        links = current.find_all('a', href=lambda href: href and '/episode-' in href)
                        for link in links:
                            related_episodes.append({
                                'title': link.get_text(strip=True),
                                'url': link.get('href')
                            })
                        current = current.find_next_sibling()
                        if current and current.name == 'h2':
                            break
                    episode_data['related_episodes'] = related_episodes
                
                # Debug logging for problematic episodes
                if not episode_data.get('description') or not episode_data.get('full_transcript'):
                    print(f"⚠️  Episode {episode_data.get('episode_number', 'unknown')} missing content:")
                    if not episode_data.get('description'):
                        print(f"   - Description missing")
                    if not episode_data.get('full_transcript'):
                        print(f"   - Transcript missing")
                    if not any(episode_data.get('about_sections', {}).values()):
                        print(f"   - About sections empty")
                
                return episode_data
            else:
                print(f"Failed to scrape {url}: {getattr(result, 'error_message', 'Unknown error')}")
                return None
    
    async def scrape_all_episodes(self, limit: int = None):
        """Scrape all episodes with rate limiting"""
        if not self.episode_urls:
            await self.discover_episode_urls()
        
        urls_to_scrape = self.episode_urls[:limit] if limit else self.episode_urls
        print(f"Scraping {len(urls_to_scrape)} episodes...")
        
        # Process in batches to avoid overwhelming the server
        batch_size = 5
        all_episodes = []
        
        for i in range(0, len(urls_to_scrape), batch_size):
            batch = urls_to_scrape[i:i + batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(len(urls_to_scrape) + batch_size - 1)//batch_size}")
            
            # Create tasks for parallel processing
            tasks = [self.scrape_episode(url) for url in batch]
            episodes = await asyncio.gather(*tasks)
            
            # Filter out None results and save valid episodes
            for episode in episodes:
                if episode:
                    all_episodes.append(episode)
                    await self.save_episode(episode)
            
            # Rate limiting between batches
            if i + batch_size < len(urls_to_scrape):
                await asyncio.sleep(2)
        
        # Save summary
        await self.save_summary(all_episodes)
        print(f"Scraping complete! Scraped {len(all_episodes)} episodes.")
    
    async def save_episode(self, episode_data: Dict[str, Any]):
        """Save episode data in multiple formats"""
        episode_num = episode_data.get('episode_number', 'unknown')
        
        # Save JSON
        json_path = self.data_dir / 'json' / f'episode_{episode_num}.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(episode_data, f, indent=2, ensure_ascii=False)
        
        # Save Markdown
        md_content = self.format_episode_as_markdown(episode_data)
        md_path = self.data_dir / 'markdown' / f'episode_{episode_num}.md'
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
    
    def format_episode_as_markdown(self, episode: Dict[str, Any]) -> str:
        """Format episode data as markdown"""
        md = f"# {episode.get('title', 'Unknown Title')}\n\n"
        md += f"**Episode Number:** {episode.get('episode_number', 'Unknown')}\n"
        md += f"**Date:** {episode.get('publish_date', 'Unknown')}\n"
        md += f"**URL:** {episode.get('url', '')}\n\n"
        
        # Add subtitle if present
        if episode.get('subtitle'):
            md += f"## {episode['subtitle']}\n\n"
        
        if episode.get('description'):
            md += f"{episode['description']}\n\n"
        
        # Add About sections
        if episode.get('about_sections'):
            for section_key, content in episode['about_sections'].items():
                section_title = section_key.replace('about_', '').replace('_', ' ').title()
                md += f"## About {section_title}\n\n{content}\n\n"
        
        # Add Sponsors section
        if episode.get('sponsors'):
            md += f"## Sponsors & Supporters\n\n{episode['sponsors']}\n\n"
        
        if episode.get('full_transcript'):
            md += "## Transcript\n\n"
            md += episode['full_transcript']
            md += "\n\n"
        
        if episode.get('resources'):
            md += "## Resources\n\n"
            for resource in episode['resources']:
                md += f"- {resource}\n"
        
        return md
    
    async def save_summary(self, episodes: List[Dict[str, Any]]):
        """Save a summary of all episodes"""
        summary_data = []
        
        for episode in episodes:
            summary_data.append({
                'episode_number': episode.get('episode_number'),
                'title': episode.get('title'),
                'date': episode.get('date'),
                'url': episode.get('url'),
                'has_transcript': bool(episode.get('full_transcript')),
                'transcript_length': len(episode.get('full_transcript', ''))
            })
        
        # Save as CSV
        df = pd.DataFrame(summary_data)
        df.sort_values('episode_number', inplace=True)
        df.to_csv(self.data_dir / 'csv' / 'episodes_summary.csv', index=False)
        
        # Save metadata
        metadata = {
            'scrape_date': datetime.now().isoformat(),
            'total_episodes': len(episodes),
            'episodes_with_transcripts': sum(1 for e in episodes if e.get('full_transcript')),
            'total_transcript_chars': sum(len(e.get('full_transcript', '')) for e in episodes)
        }
        
        with open(self.data_dir / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)


async def main():
    scraper = YonEarthPodcastScraper()
    
    # Scrape all episodes
    await scraper.scrape_all_episodes()


if __name__ == "__main__":
    asyncio.run(main())