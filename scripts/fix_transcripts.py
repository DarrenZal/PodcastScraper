#!/usr/bin/env python3
"""
Transcript Fixing Utility

Re-extracts transcripts from existing episode data using improved extraction logic.
Useful for recovering transcripts that were missed by previous scraping runs.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, CacheMode
from bs4 import BeautifulSoup

from generic_scraper import PodcastScraper


class TranscriptFixer:
    """Utility to fix missing or incomplete transcripts"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with podcast configuration"""
        self.scraper = PodcastScraper(config)
        self.data_dir = self.scraper.data_dir
        self.results = []
    
    def load_existing_episodes(self) -> List[Dict[str, Any]]:
        """Load all existing episode data"""
        episodes = []
        json_dir = self.data_dir / "json"
        
        if not json_dir.exists():
            print("No existing episode data found. Run the main scraper first.")
            return episodes
        
        for json_file in json_dir.glob("episode_*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    episode = json.load(f)
                    episodes.append(episode)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        return sorted(episodes, key=lambda x: x.get('episode_number', 0))
    
    async def fix_episode_transcript(self, episode: Dict[str, Any]) -> Dict[str, Any]:
        """Fix transcript for a single episode"""
        url = episode['url']
        episode_num = episode.get('episode_number', 0)
        current_transcript = episode.get('full_transcript', '')
        
        print(f"Fixing episode {episode_num}...")
        
        browser_config = BrowserConfig(
            headless=True,
            java_script_enabled=True
        )
        
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                config = CrawlerRunConfig(
                    wait_until="domcontentloaded",
                    delay_before_return_html=self.scraper.config.get('wait_time', 3.0),
                    cache_mode=CacheMode.BYPASS,
                    page_timeout=self.scraper.config.get('page_timeout', 30000)
                )
                
                result = await crawler.arun(url, config=config)
                
                if result.success:
                    soup = BeautifulSoup(result.html, 'html.parser')
                    
                    # Check for transcript mentions
                    transcript_mentions = soup.find_all(string=lambda text: text and 'transcript' in text.lower())
                    has_transcript_mention = len(transcript_mentions) > 0
                    
                    # Check for podcast intro
                    intro_patterns = self.scraper.config.get('transcript_selectors', {}).get('podcast_intro_patterns', [])
                    has_podcast_intro = any(pattern in result.html for pattern in intro_patterns)
                    
                    # Try improved extraction
                    extracted_transcript = self.scraper.extract_transcript_from_soup(soup, episode_num)
                    
                    # Determine status
                    if extracted_transcript and len(extracted_transcript) > 500:
                        status = "TRANSCRIPT_EXTRACTED"
                        needs_whisper = False
                        improvement = len(extracted_transcript) - len(current_transcript)
                    elif has_transcript_mention:
                        status = "TRANSCRIPT_HEADER_FOUND_BUT_EXTRACTION_FAILED"
                        needs_whisper = False
                        improvement = 0
                    elif has_podcast_intro:
                        status = "PODCAST_INTRO_FOUND_BUT_NO_TRANSCRIPT_HEADER"
                        needs_whisper = False
                        improvement = 0
                    else:
                        status = "NO_TRANSCRIPT_AVAILABLE"
                        needs_whisper = True
                        improvement = 0
                    
                    result_data = {
                        'episode_number': episode_num,
                        'url': url,
                        'title': episode.get('title', ''),
                        'current_transcript_length': len(current_transcript),
                        'extracted_transcript_length': len(extracted_transcript),
                        'improvement': improvement,
                        'has_transcript_mention': has_transcript_mention,
                        'has_podcast_intro': has_podcast_intro,
                        'status': status,
                        'needs_whisper': needs_whisper,
                        'transcript_mentions_count': len(transcript_mentions),
                        'extracted_transcript': extracted_transcript
                    }
                    
                    return result_data
                else:
                    return {
                        'episode_number': episode_num,
                        'url': url,
                        'title': episode.get('title', ''),
                        'status': 'CRAWL_FAILED',
                        'error': result.error_message,
                        'needs_whisper': False
                    }
        except Exception as e:
            return {
                'episode_number': episode_num,
                'url': url,
                'title': episode.get('title', ''),
                'status': 'ANALYSIS_FAILED', 
                'error': str(e),
                'needs_whisper': False
            }
    
    async def fix_transcripts(self, episode_numbers: Optional[List[int]] = None, 
                            limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fix transcripts for specified episodes or all episodes"""
        
        episodes = self.load_existing_episodes()
        
        if not episodes:
            print("No episodes found to process")
            return []
        
        # Filter episodes if specific numbers requested
        if episode_numbers:
            episodes = [ep for ep in episodes if ep.get('episode_number') in episode_numbers]
        
        # Apply limit if specified
        if limit:
            episodes = episodes[:limit]
        
        print(f"Processing {len(episodes)} episodes for transcript fixing...")
        
        results = []
        improved_count = 0
        
        for i, episode in enumerate(episodes):
            print(f"Progress: {i+1}/{len(episodes)}")
            
            result = await self.fix_episode_transcript(episode)
            results.append(result)
            
            # Update episode file if transcript was improved
            if result.get('status') == 'TRANSCRIPT_EXTRACTED' and result.get('improvement', 0) > 0:
                self.update_episode_file(episode, result['extracted_transcript'])
                improved_count += 1
                print(f"✓ Episode {result['episode_number']}: Improved by {result['improvement']} characters")
            elif result.get('status') == 'NO_TRANSCRIPT_AVAILABLE':
                print(f"⚠ Episode {result['episode_number']}: Needs Whisper transcription")
            elif result.get('status') in ['CRAWL_FAILED', 'ANALYSIS_FAILED']:
                print(f"✗ Episode {result['episode_number']}: {result.get('error', 'Failed')}")
            else:
                print(f"- Episode {result['episode_number']}: No improvement")
            
            # Rate limiting
            await asyncio.sleep(1)
        
        # Generate report
        self.generate_report(results)
        
        print(f"\nTranscript fixing complete!")
        print(f"Episodes processed: {len(results)}")
        print(f"Episodes improved: {improved_count}")
        print(f"Episodes needing Whisper: {sum(1 for r in results if r.get('needs_whisper'))}")
        
        return results
    
    def update_episode_file(self, episode: Dict[str, Any], new_transcript: str):
        """Update episode file with improved transcript"""
        episode_num = episode.get('episode_number', 0)
        
        # Update the episode data
        episode['full_transcript'] = new_transcript
        episode['transcript_fixed_date'] = datetime.now().isoformat()
        
        # Save updated JSON
        json_file = self.data_dir / "json" / f"episode_{episode_num}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(episode, f, indent=2, ensure_ascii=False)
        
        # Save to fixed_transcripts directory for comparison
        fixed_file = self.data_dir / "fixed_transcripts" / f"episode_{episode_num}.json"
        with open(fixed_file, 'w', encoding='utf-8') as f:
            json.dump(episode, f, indent=2, ensure_ascii=False)
        
        # Update Markdown file
        md_file = self.data_dir / "markdown" / f"episode_{episode_num}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(self.scraper.format_episode_markdown(episode))
    
    def generate_report(self, results: List[Dict[str, Any]]):
        """Generate a comprehensive report of transcript fixing results"""
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_processed': len(results),
            'improved': len([r for r in results if r.get('status') == 'TRANSCRIPT_EXTRACTED' and r.get('improvement', 0) > 0]),
            'needs_whisper': len([r for r in results if r.get('needs_whisper', False)]),
            'no_improvement': len([r for r in results if r.get('status') == 'TRANSCRIPT_EXTRACTED' and r.get('improvement', 0) == 0]),
            'extraction_failed': len([r for r in results if r.get('status') == 'TRANSCRIPT_HEADER_FOUND_BUT_EXTRACTION_FAILED']),
            'crawl_failed': len([r for r in results if r.get('status') == 'CRAWL_FAILED']),
            'analysis_failed': len([r for r in results if r.get('status') == 'ANALYSIS_FAILED']),
            'results': results,
            'statistics': {
                'total_characters_added': sum(r.get('improvement', 0) for r in results),
                'avg_improvement': sum(r.get('improvement', 0) for r in results) / len(results) if results else 0,
                'success_rate': len([r for r in results if r.get('status') == 'TRANSCRIPT_EXTRACTED']) / len(results) if results else 0
            }
        }
        
        # Save report
        report_file = self.data_dir / "transcript_fix_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n{'='*60}")
        print("TRANSCRIPT FIXING SUMMARY")
        print(f"{'='*60}")
        print(f"Total processed: {report['total_processed']}")
        print(f"Improved: {report['improved']}")
        print(f"Need Whisper: {report['needs_whisper']}")
        print(f"No improvement: {report['no_improvement']}")
        print(f"Extraction failed: {report['extraction_failed']}")
        print(f"Crawl failed: {report['crawl_failed']}")
        print(f"Analysis failed: {report['analysis_failed']}")
        
        if report['statistics']['total_characters_added'] > 0:
            print(f"\nTotal characters added: {report['statistics']['total_characters_added']:,}")
            print(f"Average improvement: {report['statistics']['avg_improvement']:.1f} characters")
        
        whisper_episodes = [r for r in results if r.get('needs_whisper', False)]
        if whisper_episodes:
            print(f"\nEpisodes needing Whisper transcription:")
            for r in whisper_episodes[:10]:  # Show first 10
                print(f"  Episode {r['episode_number']}: {r.get('title', 'Unknown')[:50]}...")
            if len(whisper_episodes) > 10:
                print(f"  ... and {len(whisper_episodes) - 10} more")
        
        print(f"\nReport saved to: {report_file}")


async def main():
    """Main function for transcript fixing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix missing podcast transcripts')
    parser.add_argument('--episodes', type=int, nargs='+', 
                       help='Specific episode numbers to fix (e.g., --episodes 144 163)')
    parser.add_argument('--limit', type=int, 
                       help='Limit number of episodes to process')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: fix only episodes 144, 161, 163')
    
    args = parser.parse_args()
    
    # Initialize fixer with default YonEarth configuration
    fixer = TranscriptFixer()
    
    if args.test:
        # Test mode with known episodes
        print("Running in test mode with episodes 144, 161, 163")
        await fixer.fix_transcripts(episode_numbers=[144, 161, 163])
    elif args.episodes:
        # Fix specific episodes
        print(f"Fixing transcripts for episodes: {args.episodes}")
        await fixer.fix_transcripts(episode_numbers=args.episodes)
    else:
        # Fix all episodes
        print("Fixing transcripts for all episodes")
        await fixer.fix_transcripts(limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())