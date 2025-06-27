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

from generic_scraper import PodcastScraper
from audio_transcriber import AudioTranscriber


class YonEarthPodcastScraper:
    def __init__(self, enable_audio_transcription=False, whisper_model="base", hf_token=None, skip_existing=False):
        self.base_url = "https://yonearth.org"
        self.podcast_list_url = "https://yonearth.org/community-podcast/"
        self.data_dir = Path(__file__).parent.parent / "data"
        self.episode_urls = []
        self.skip_existing = skip_existing
        
        # Create necessary directories
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "json").mkdir(exist_ok=True)
        (self.data_dir / "markdown").mkdir(exist_ok=True)
        (self.data_dir / "csv").mkdir(exist_ok=True)
        
        # Initialize improved transcript extraction
        self.generic_scraper = PodcastScraper()
        
        # Audio transcription setup
        self.enable_audio_transcription = enable_audio_transcription
        self.audio_transcriber = None
        if enable_audio_transcription:
            self.audio_transcriber = AudioTranscriber(
                whisper_model=whisper_model,
                use_auth_token=hf_token
            )
        
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
            # Stop when we find no new episodes (intelligent pagination)
            max_pages = 50  # Safety limit
            consecutive_empty_pages = 0
            max_empty_pages = 2  # Stop after 2 consecutive empty pages
            
            for page_num in range(2, max_pages + 1):
                episodes_before = len(self.episode_urls)
                await self._scrape_page_with_js(crawler, self.podcast_list_url, page_num)
                episodes_after = len(self.episode_urls)
                
                # Check if we found new episodes
                if episodes_after == episodes_before:
                    consecutive_empty_pages += 1
                    print(f"  No new episodes found on page {page_num} ({consecutive_empty_pages}/{max_empty_pages} empty pages)")
                    
                    if consecutive_empty_pages >= max_empty_pages:
                        print(f"  Stopping pagination after {consecutive_empty_pages} consecutive empty pages")
                        break
                else:
                    consecutive_empty_pages = 0  # Reset counter when we find episodes
                
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
                'href': re.compile(r'/podcast/[^/]+/?$'),
                'class': 'tve-dynamic-link'
            })
            
            # Fallback to any episode links if the main selector doesn't work
            if not episode_links:
                episode_links = soup.find_all('a', href=re.compile(r'/podcast/[^/]+/?$'))
            
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
                    # First try the standard episode-number format
                    match = re.search(r'episode-(\d+)', url)
                    if match:
                        episode_data['episode_number'] = int(match.group(1))
                    else:
                        # For URLs without explicit numbers, extract from slug
                        slug = url.split('/podcast/')[-1].rstrip('/')
                        episode_data['episode_number'] = slug
                
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
                
                # Extract full transcript using improved logic from generic_scraper
                episode_num = episode_data.get('episode_number', 0)
                episode_data['full_transcript'] = self.generic_scraper.extract_transcript_from_soup(soup, episode_num)
                
                # Try audio transcription if enabled and no web transcript found
                if (not episode_data['full_transcript'] or len(episode_data['full_transcript']) < 100) and \
                   self.enable_audio_transcription and self.audio_transcriber and episode_data.get('audio_url'):
                    
                    print(f"  No web transcript found for episode {episode_num}, attempting audio transcription...")
                    try:
                        audio_result = await self.audio_transcriber.transcribe_from_url(
                            episode_data['audio_url'], 
                            episode_num
                        )
                        
                        if audio_result['success']:
                            episode_data['full_transcript'] = audio_result['transcript']
                            episode_data['audio_transcription_metadata'] = audio_result['metadata']
                            print(f"  ✓ Audio transcription successful: {len(audio_result['transcript'])} characters")
                        else:
                            print(f"  ✗ Audio transcription failed: {audio_result['error']}")
                    except Exception as e:
                        print(f"  ✗ Audio transcription error: {e}")
                
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
        
        # Filter out existing episodes if skip_existing is enabled
        if self.skip_existing:
            filtered_urls = []
            skipped_count = 0
            for url in urls_to_scrape:
                if not self._episode_files_exist(url):
                    filtered_urls.append(url)
                else:
                    skipped_count += 1
            
            urls_to_scrape = filtered_urls
            if skipped_count > 0:
                print(f"Skipping {skipped_count} existing episodes")
        
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
    
    def _episode_files_exist(self, url: str) -> bool:
        """Check if episode files already exist and have complete content"""
        # Extract episode number from URL
        match = re.search(r'episode-(\d+)', url)
        if not match:
            return False
        
        episode_num = match.group(1)
        
        # Check if both JSON and Markdown files exist
        json_path = self.data_dir / 'json' / f'episode_{episode_num}.json'
        md_path = self.data_dir / 'markdown' / f'episode_{episode_num}.md'
        
        if not (json_path.exists() and md_path.exists()):
            return False
        
        # If audio transcription is enabled, also check if transcript is missing
        if self.enable_audio_transcription:
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    episode_data = json.load(f)
                    transcript = episode_data.get('full_transcript', '')
                    # Consider episode incomplete if transcript is missing or very short
                    if not transcript or len(transcript.strip()) < 100:
                        return False
            except (json.JSONDecodeError, FileNotFoundError, KeyError):
                return False
        
        return True
    
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
        # Sort by episode number, handling mixed int/string types
        df['sort_key'] = df['episode_number'].apply(lambda x: (0, x) if isinstance(x, int) else (1, str(x)))
        df.sort_values('sort_key', inplace=True)
        df.drop('sort_key', axis=1, inplace=True)
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
    import argparse
    
    parser = argparse.ArgumentParser(description='YonEarth Podcast Scraper')
    parser.add_argument('--enable-audio-transcription', action='store_true',
                       help='Enable audio transcription for episodes without transcripts')
    parser.add_argument('--whisper-model', type=str, default='base',
                       choices=['tiny', 'base', 'small', 'medium', 'large'],
                       help='Whisper model size (default: base)')
    parser.add_argument('--hf-token', type=str,
                       help='Hugging Face token for pyannote models')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip episodes that have already been scraped')
    parser.add_argument('--limit', type=int,
                       help='Limit number of episodes to process')
    
    args = parser.parse_args()
    
    scraper = YonEarthPodcastScraper(
        enable_audio_transcription=args.enable_audio_transcription,
        whisper_model=args.whisper_model,
        hf_token=args.hf_token,
        skip_existing=args.skip_existing
    )
    
    # Scrape all episodes
    await scraper.scrape_all_episodes(limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())