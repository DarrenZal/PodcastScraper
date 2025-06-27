#!/usr/bin/env python3
"""
Generic Podcast Scraper

A configurable web scraper for extracting podcast episodes and transcripts from any podcast website.
Built with Crawl4AI for robust JavaScript-enabled crawling.

Default configuration: YonEarth Community Podcast
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import re
from typing import List, Dict, Any, Optional

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import pandas as pd
from bs4 import BeautifulSoup


class PodcastScraper:
    """Generic podcast scraper with configurable settings for different podcast websites"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the podcast scraper with configuration
        
        Args:
            config: Dictionary containing podcast-specific configuration.
                   If None, uses default YonEarth configuration.
        """
        if config is None:
            # Default configuration for YonEarth Community Podcast
            config = self._get_yonearth_config()
        
        self.config = config
        self.data_dir = Path(__file__).parent.parent / "data"
        self.episode_urls = []
        self.batch_size = 5
        self.batch_delay = 2.0  # seconds
        
        # Create necessary directories
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / "json").mkdir(exist_ok=True)
        (self.data_dir / "markdown").mkdir(exist_ok=True)
        (self.data_dir / "csv").mkdir(exist_ok=True)
        (self.data_dir / "fixed_transcripts").mkdir(exist_ok=True)
    
    def _get_yonearth_config(self) -> Dict[str, Any]:
        """Default configuration for YonEarth Community Podcast"""
        return {
            "base_url": "https://yonearth.org",
            "podcast_list_url": "https://yonearth.org/community-podcast/",
            "episode_url_pattern": r'/podcast/episode-\d+',
            "episode_link_selector": 'a.tve-dynamic-link',
            "episode_link_fallback_selector": 'a[href*="/podcast/episode-"]',
            "pagination_pages": 10,
            "pagination_selector": '.tcb-pagination-number a',
            "podcast_name": "YonEarth Community Podcast",
            "host_name": "Aaron William Perry",
            "transcript_selectors": {
                "headers": ["h1", "h2", "h3", "h4"],
                "transcript_keywords": ["Transcript", "Full Transcript"],
                "podcast_intro_patterns": [
                    "Welcome to the Y on Earth Community podcast",
                    "I'm your host, Aaron William Perry"
                ],
                "stop_patterns": [
                    "aaron william perryis a writer",
                    "aaron william perry author", 
                    "resources & related episodes",
                    "leave a reply",
                    "required fields are marked",
                    "your email address will not be published"
                ],
                "skip_patterns": [
                    "comments are closed", "subscribe to the podcast",
                    "apple podcasts", "spotify podcasts", "google podcasts",
                    "stitcher", "embed this episode", "share this episode"
                ]
            },
            "wait_time": 3.0,  # seconds to wait for dynamic content
            "page_timeout": 30000  # milliseconds
        }
    
    async def discover_episode_urls(self) -> List[str]:
        """Discover all episode URLs from the main podcast page and pagination"""
        print(f"Discovering episode URLs from {self.config['podcast_name']}...")
        
        browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Scrape main page first (page 1)
            await self._scrape_page_with_js(crawler, self.config['podcast_list_url'], 1)
            
            # Use JavaScript to navigate through pagination if configured
            pagination_pages = self.config.get('pagination_pages', 1)
            if pagination_pages > 1:
                for page_num in range(2, pagination_pages + 1):
                    await self._scrape_page_with_js(crawler, self.config['podcast_list_url'], page_num)
                
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
                const pagination = document.querySelector('{self.config.get('pagination_selector', '.pagination')}');
                if (pagination) {{
                    resolve();
                }} else {{
                    setTimeout(checkPagination, 100);
                }}
            }};
            checkPagination();
        }});
        
        // Find and click the page {page_num} button
        const pageButtons = document.querySelectorAll('{self.config.get('pagination_selector', '.pagination')} a');
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
        }}
        """
        
        config = CrawlerRunConfig(
            js_code=js_code if page_num > 1 else None,
            wait_until="domcontentloaded",
            delay_before_return_html=self.config.get('wait_time', 3.0),
            cache_mode=CacheMode.BYPASS,
            page_timeout=self.config.get('page_timeout', 30000)
        )
        
        result = await crawler.arun(base_url, config=config)
        
        if result.success:
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Find all episode links using the configured selectors
            episode_links = soup.find_all('a', {
                'href': re.compile(self.config['episode_url_pattern']),
                'class': self.config.get('episode_link_selector', '').replace('a.', '')
            })
            
            # Fallback to any episode links if the main selector doesn't work
            if not episode_links:
                fallback_selector = self.config.get('episode_link_fallback_selector')
                if fallback_selector:
                    episode_links = soup.select(fallback_selector)
                else:
                    episode_links = soup.find_all('a', href=re.compile(self.config['episode_url_pattern']))
            
            page_urls = []
            for link in episode_links:
                url_found = link.get('href')
                if url_found and not url_found.startswith('http'):
                    url_found = self.config['base_url'] + url_found
                if url_found and url_found not in self.episode_urls:
                    self.episode_urls.append(url_found)
                    page_urls.append(url_found)
            
            print(f"Found {len(page_urls)} episode URLs on page {page_num}")
                
        else:
            print(f"Failed to crawl page {page_num}: {getattr(result, 'error_message', 'Unknown error')}")
    
    def extract_transcript_from_soup(self, soup: BeautifulSoup, episode_num: int) -> str:
        """
        Universal transcript extraction that handles multiple formats:
        1. Episodes with explicit transcript headers (h1, h2, h3, h4)
        2. Episodes with no heading but transcript content (intro-based detection)
        3. Identifies episodes with no transcript available
        """
        transcript_content = []
        transcript_config = self.config.get('transcript_selectors', {})
        
        # Method 1: Look for explicit transcript headings
        transcript_header = None
        headers = transcript_config.get('headers', ['h1', 'h2', 'h3', 'h4'])
        keywords = transcript_config.get('transcript_keywords', ['Transcript'])
        
        # Debug: Check for any text containing "transcript" (case insensitive)
        all_text_with_transcript = soup.find_all(string=lambda text: text and 'transcript' in text.lower())
        if all_text_with_transcript:
            print(f"Episode {episode_num}: Found {len(all_text_with_transcript)} text elements containing 'transcript':")
            for i, text_elem in enumerate(all_text_with_transcript[:5]):  # Show first 5
                print(f"  {i+1}: '{text_elem.strip()[:100]}...'")
        else:
            print(f"Episode {episode_num}: No text elements found containing 'transcript'")
        
        for level in headers:
            for keyword in keywords:
                transcript_header = soup.find(level, string=lambda text: text and keyword in text)
                if transcript_header:
                    print(f"Episode {episode_num}: Found {level} transcript header with keyword '{keyword}'")
                    break
            if transcript_header:
                break
        
        # Method 1.5: Look for non-header elements containing just "Transcript:" or similar
        if not transcript_header:
            # Look for any element containing "Transcript:" (including <p>, <div>, etc.)
            for text_elem in all_text_with_transcript:
                stripped_text = text_elem.strip()
                # Check if it's likely a transcript label
                if (stripped_text.lower() in ['transcript:', 'transcript', 'full transcript:', 'full transcript'] or
                    (len(stripped_text) < 20 and 'transcript' in stripped_text.lower() and ':' in stripped_text)):
                    
                    # Find the parent element
                    parent = text_elem.parent
                    if parent:
                        print(f"Episode {episode_num}: Found transcript label in {parent.name}: '{stripped_text}'")
                        # Check if content follows this element
                        next_elem = parent.find_next_sibling()
                        if next_elem and next_elem.name == 'p':
                            transcript_header = parent
                            print(f"Episode {episode_num}: Using {parent.name} element as transcript start")
                            break
        
        if transcript_header:
            # Extract content after the header
            current = transcript_header.find_next_sibling()
            para_count = 0
            max_paragraphs = self.config.get('max_transcript_paragraphs', 500)
            
            while current and para_count < max_paragraphs:
                if current.name == 'p' and current.get_text(strip=True):
                    text = current.get_text(strip=True)
                    # Skip obvious non-transcript content
                    skip_patterns = transcript_config.get('skip_patterns', [
                        'leave a reply', 'comments are closed', 'subscribe to',
                        'required fields are marked', 'your email address will not be published'
                    ])
                    
                    if not any(skip in text.lower() for skip in skip_patterns) and len(text) > 5:
                        transcript_content.append(text) 
                        para_count += 1
                elif current.name in headers and current.get_text(strip=True):
                    # Stop at next major heading that's clearly not transcript
                    heading_text = current.get_text(strip=True).lower()
                    stop_headings = ['leave a reply', 'advising', 'subscribe', 'recent posts',
                                   'kits & bundles', 'books', 'consulting']
                    if any(stop in heading_text for stop in stop_headings):
                        break
                current = current.find_next_sibling()
            
            print(f"Episode {episode_num}: Extracted {len(transcript_content)} paragraphs after transcript header")
        
        # Method 2: Look for transcript content without explicit heading (intro-based)
        if not transcript_content:
            print(f"Episode {episode_num}: No transcript header found, looking for podcast intro...")
            all_paras = soup.find_all('p')
            transcript_started = False
            
            intro_patterns = transcript_config.get('podcast_intro_patterns', [])
            stop_patterns = transcript_config.get('stop_patterns', [])
            skip_patterns = transcript_config.get('skip_patterns', [])
            
            for p in all_paras:
                text = p.get_text(strip=True)
                
                # Start collecting when we find podcast intro
                if not transcript_started and text and any(pattern in text for pattern in intro_patterns):
                    transcript_started = True
                    transcript_content.append(text)
                    print(f"Episode {episode_num}: Found podcast intro, starting transcript collection")
                    continue
                
                # If we've started, keep collecting substantial content
                if transcript_started and text and len(text) > 20:
                    # Check stop conditions
                    should_stop = any(stop_phrase in text.lower() for stop_phrase in stop_patterns)
                    
                    if should_stop:
                        print(f"Episode {episode_num}: Reached end section, stopping collection")
                        break
                    
                    # Check skip conditions
                    should_skip = any(skip_phrase in text.lower() for skip_phrase in skip_patterns)
                    
                    if should_skip:
                        continue
                    
                    transcript_content.append(text)
            
            print(f"Episode {episode_num}: Collected {len(transcript_content)} paragraphs via intro method")
        
        final_transcript = '\n\n'.join(transcript_content) if transcript_content else ''
        print(f"Episode {episode_num}: Final transcript length: {len(final_transcript)} characters")
        return final_transcript
    
    async def scrape_episode(self, url: str) -> Optional[Dict[str, Any]]:
        """Scrape a single episode and extract all available data"""
        print(f"Scraping episode: {url}")
        
        browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            config = CrawlerRunConfig(
                wait_until="domcontentloaded",
                delay_before_return_html=self.config.get('wait_time', 3.0),
                cache_mode=CacheMode.BYPASS,
                page_timeout=self.config.get('page_timeout', 30000)
            )
            
            result = await crawler.arun(url, config=config)
            
            if not result.success:
                print(f"Failed to scrape {url}: {getattr(result, 'error_message', 'Unknown error')}")
                return None
            
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Extract basic episode data
            episode_data = {
                'url': url,
                'scraped_date': datetime.now().isoformat()
            }
            
            # Extract episode number from URL
            episode_match = re.search(self.config['episode_url_pattern'], url)
            if episode_match:
                # First try to find a number in the URL (for episode-123 format)
                episode_num_match = re.search(r'episode-(\d+)', url)
                if episode_num_match:
                    episode_data['episode_number'] = int(episode_num_match.group(1))
                else:
                    # For descriptive URLs, use the slug as episode identifier
                    slug = url.split('/podcast/')[-1].rstrip('/')
                    episode_data['episode_number'] = slug
            
            # Extract title
            title_tag = soup.find('h1')
            if title_tag:
                episode_data['title'] = title_tag.get_text(strip=True)
            
            # Extract publish date (customize based on site structure)
            date_patterns = [
                lambda s: s.find('p', string=re.compile(r'\d{4}.*(?:pm|am)', re.I)),
                lambda s: s.find('time'),
                lambda s: s.find(class_='date'),
                lambda s: s.find(class_='publish-date')
            ]
            
            for pattern in date_patterns:
                date_elem = pattern(soup)
                if date_elem:
                    episode_data['publish_date'] = date_elem.get_text(strip=True)
                    break
            else:
                episode_data['publish_date'] = 'Unknown'
            
            # Extract audio URL
            audio_patterns = [
                lambda s: s.find('audio'),
                lambda s: s.find('source', type='audio/mpeg'),
                lambda s: s.find('a', href=re.compile(r'\.mp3', re.I))
            ]
            
            for pattern in audio_patterns:
                audio_elem = pattern(soup)
                if audio_elem:
                    audio_url = audio_elem.get('src') or audio_elem.get('href')
                    if audio_url:
                        episode_data['audio_url'] = audio_url
                        break
            
            # Extract subtitle/description
            h2_tags = soup.find_all('h2')
            if h2_tags:
                episode_data['subtitle'] = h2_tags[0].get_text(strip=True)
                
                # Look for description after subtitle
                desc_p = h2_tags[0].find_next_sibling('p')
                if desc_p:
                    episode_data['description'] = desc_p.get_text(strip=True)
            
            # Extract guest bios (About sections)
            about_sections = {}
            about_headings = soup.find_all(['h2', 'h3'], string=re.compile(r'About', re.I))
            
            for heading in about_headings:
                section_name = heading.get_text(strip=True).replace('About ', '').lower().replace(' ', '_')
                next_p = heading.find_next_sibling('p')
                if next_p and next_p.get_text(strip=True):
                    about_sections[f'about_{section_name}'] = next_p.get_text(strip=True)
            
            episode_data['about_sections'] = about_sections
            
            # Extract full transcript using improved logic
            episode_num = episode_data.get('episode_number', 0)
            episode_data['full_transcript'] = self.extract_transcript_from_soup(soup, episode_num)
            
            # Extract related episodes
            related_episodes = []
            related_links = soup.find_all('a', href=re.compile(self.config['episode_url_pattern']))
            
            for link in related_links[:6]:  # Limit to first 6 related episodes
                if link.get('href') != url:  # Don't include current episode
                    related_episodes.append({
                        'title': link.get_text(strip=True),
                        'url': link.get('href')
                    })
            
            episode_data['related_episodes'] = related_episodes
            
            return episode_data
    
    async def scrape_all_episodes(self, limit: Optional[int] = None):
        """Scrape all discovered episodes"""
        if not self.episode_urls:
            await self.discover_episode_urls()
        
        episodes_to_scrape = self.episode_urls[:limit] if limit else self.episode_urls
        print(f"Scraping {len(episodes_to_scrape)} episodes...")
        
        episodes = []
        
        # Process episodes in batches
        for i in range(0, len(episodes_to_scrape), self.batch_size):
            batch = episodes_to_scrape[i:i + self.batch_size]
            batch_number = i // self.batch_size + 1
            print(f"Processing batch {batch_number} ({len(batch)} episodes)...")
            
            batch_episodes = []
            for url in batch:
                episode_data = await self.scrape_episode(url)
                if episode_data:
                    batch_episodes.append(episode_data)
                    
                    # Save individual episode
                    episode_num = episode_data.get('episode_number', len(episodes))
                    self.save_episode_data(episode_data, episode_num)
                
                # Small delay between episodes
                await asyncio.sleep(0.5)
            
            episodes.extend(batch_episodes)
            
            # Delay between batches
            if i + self.batch_size < len(episodes_to_scrape):
                print(f"Waiting {self.batch_delay}s before next batch...")
                await asyncio.sleep(self.batch_delay)
        
        # Generate summary outputs
        self.save_summary_data(episodes)
        
        print(f"Scraping complete! Processed {len(episodes)} episodes.")
        return episodes
    
    def save_episode_data(self, episode_data: Dict[str, Any], episode_num: int):
        """Save episode data in multiple formats"""
        # Save JSON
        json_file = self.data_dir / "json" / f"episode_{episode_num}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(episode_data, f, indent=2, ensure_ascii=False)
        
        # Save Markdown
        md_file = self.data_dir / "markdown" / f"episode_{episode_num}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(self.format_episode_markdown(episode_data))
    
    def format_episode_markdown(self, episode: Dict[str, Any]) -> str:
        """Format episode data as Markdown"""
        md = f"# {episode.get('title', 'Unknown Title')}\n\n"
        
        if episode.get('subtitle'):
            md += f"**{episode['subtitle']}**\n\n"
        
        if episode.get('publish_date'):
            md += f"**Published:** {episode['publish_date']}\n\n"
        
        if episode.get('audio_url'):
            md += f"**Audio:** [Download]({episode['audio_url']})\n\n"
        
        if episode.get('description'):
            md += f"## Description\n\n{episode['description']}\n\n"
        
        # About sections
        for key, value in episode.get('about_sections', {}).items():
            section_title = key.replace('about_', '').replace('_', ' ').title()
            md += f"## About {section_title}\n\n{value}\n\n"
        
        # Transcript
        if episode.get('full_transcript'):
            md += f"## Transcript\n\n{episode['full_transcript']}\n\n"
        
        return md
    
    def save_summary_data(self, episodes: List[Dict[str, Any]]):
        """Save summary data and metadata"""
        # Create CSV summary
        summary_data = []
        for ep in episodes:
            summary_data.append({
                'episode_number': ep.get('episode_number'),
                'title': ep.get('title'),
                'publish_date': ep.get('publish_date'),
                'has_transcript': bool(ep.get('full_transcript')),
                'transcript_length': len(ep.get('full_transcript', '')),
                'has_audio': bool(ep.get('audio_url')),
                'url': ep.get('url')
            })
        
        df = pd.DataFrame(summary_data)
        csv_file = self.data_dir / "csv" / "episodes_summary.csv"
        df.to_csv(csv_file, index=False)
        
        # Save metadata
        metadata = {
            'scrape_date': datetime.now().isoformat(),
            'podcast_name': self.config['podcast_name'],
            'total_episodes': len(episodes),
            'episodes_with_transcripts': sum(1 for e in episodes if e.get('full_transcript')),
            'total_transcript_chars': sum(len(e.get('full_transcript', '')) for e in episodes),
            'config_used': self.config
        }
        
        metadata_file = self.data_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)


# Example configurations for other podcasts
def get_example_configs():
    """Example configurations for popular podcast platforms"""
    return {
        "custom_podcast_example": {
            "base_url": "https://example-podcast.com",
            "podcast_list_url": "https://example-podcast.com/episodes/",
            "episode_url_pattern": r'/episodes/\d+',
            "episode_link_selector": 'a.episode-link',
            "pagination_pages": 5,
            "podcast_name": "Example Podcast",
            "host_name": "Host Name",
            "transcript_selectors": {
                "headers": ["h1", "h2", "h3"],
                "transcript_keywords": ["Transcript", "Show Notes"],
                "podcast_intro_patterns": [
                    "Welcome to Example Podcast",
                    "I'm your host"
                ]
            }
        }
    }


async def main():
    """Main function - can be customized for different podcasts"""
    # Use default YonEarth configuration
    scraper = PodcastScraper()
    
    # Or use a custom configuration:
    # custom_config = get_example_configs()["custom_podcast_example"]
    # scraper = PodcastScraper(config=custom_config)
    
    # Scrape all episodes (or limit for testing)
    await scraper.scrape_all_episodes(limit=None)  # Remove limit for full scrape


if __name__ == "__main__":
    asyncio.run(main())