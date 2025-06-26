#!/usr/bin/env python3
"""
Example Usage of Podcast Scraper

This file demonstrates how to use the generic podcast scraper
with different configurations for various podcast platforms.
"""

import asyncio
import sys
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).parent.parent / "scripts"))

from generic_scraper import PodcastScraper
from config.podcast_configs import get_config, create_custom_config


async def example_yonearth_scraping():
    """Example: Scrape YonEarth podcast (default configuration)"""
    print("=== YonEarth Podcast Scraping (Default) ===")
    
    # Use default configuration
    scraper = PodcastScraper()
    
    # Test with limited episodes
    episodes = await scraper.scrape_all_episodes(limit=3)
    print(f"Scraped {len(episodes)} episodes from YonEarth podcast")


async def example_custom_config_scraping():
    """Example: Use a custom configuration"""
    print("\n=== Custom Configuration Example ===")
    
    # Create a custom configuration
    custom_config = create_custom_config(
        base_url="https://example-podcast.com",
        podcast_list_url="https://example-podcast.com/episodes/",
        podcast_name="Example Podcast",
        episode_url_pattern=r'/episodes/\d+',
        host_name="Jane Doe",
        pagination_pages=3,
        transcript_keywords=["Transcript", "Show Notes"],
        intro_patterns=["Welcome to Example Podcast", "This is Jane"],
        wait_time=2.5
    )
    
    # Initialize scraper with custom config
    scraper = PodcastScraper(config=custom_config)
    
    print(f"Configured for: {custom_config['podcast_name']}")
    print(f"Base URL: {custom_config['base_url']}")
    print(f"Host: {custom_config['host_name']}")
    
    # Note: This would fail since the URL doesn't exist
    # episodes = await scraper.scrape_all_episodes(limit=1)


async def example_template_config():
    """Example: Use a configuration template"""
    print("\n=== Template Configuration Example ===")
    
    # Get a template configuration
    wordpress_config = get_config("wordpress")
    
    # Customize it for a specific podcast
    wordpress_config.update({
        "base_url": "https://my-wordpress-podcast.com",
        "podcast_list_url": "https://my-wordpress-podcast.com/episodes/",
        "podcast_name": "My WordPress Podcast",
        "host_name": "John Smith"
    })
    
    scraper = PodcastScraper(config=wordpress_config)
    
    print(f"Using WordPress template for: {wordpress_config['podcast_name']}")
    print(f"Episode URL pattern: {wordpress_config['episode_url_pattern']}")


def example_configuration_analysis():
    """Example: Analyze and compare configurations"""
    print("\n=== Configuration Analysis ===")
    
    from config.podcast_configs import list_available_configs
    
    configs = list_available_configs()
    print(f"Available configuration templates: {', '.join(configs)}")
    
    # Compare different configurations
    for config_name in ["yonearth", "wordpress", "anchor"]:
        config = get_config(config_name)
        print(f"\n{config_name.title()} Configuration:")
        print(f"  Podcast: {config['podcast_name']}")
        print(f"  Pagination: {config['pagination_pages']} pages")
        print(f"  Wait time: {config['wait_time']}s")
        print(f"  Transcript headers: {config['transcript_selectors']['headers']}")


async def example_transcript_fixing():
    """Example: Fix missing transcripts"""
    print("\n=== Transcript Fixing Example ===")
    
    # Import the transcript fixer
    from fix_transcripts import TranscriptFixer
    
    # Initialize with default configuration
    fixer = TranscriptFixer()
    
    # Fix specific episodes (example episodes that we know have transcript issues)
    print("Fixing transcripts for test episodes...")
    results = await fixer.fix_transcripts(episode_numbers=[144, 163], limit=2)
    
    # Show results
    for result in results:
        status = result.get('status', 'Unknown')
        episode_num = result.get('episode_number', '?')
        improvement = result.get('improvement', 0)
        
        print(f"Episode {episode_num}: {status}")
        if improvement > 0:
            print(f"  Improved by {improvement} characters")


def example_batch_processing():
    """Example: Set up batch processing with custom settings"""
    print("\n=== Batch Processing Configuration ===")
    
    # Create scraper with custom batch settings
    scraper = PodcastScraper()
    
    # Customize batch processing
    scraper.batch_size = 3  # Process 3 episodes at a time
    scraper.batch_delay = 5.0  # Wait 5 seconds between batches
    
    print(f"Batch size: {scraper.batch_size}")
    print(f"Batch delay: {scraper.batch_delay}s")
    print("This configuration is more conservative and respectful to the server")


async def main():
    """Run all examples"""
    print("Podcast Scraper Examples")
    print("=" * 50)
    
    # Configuration examples (these don't require network access)
    example_configuration_analysis()
    example_batch_processing()
    
    # Network examples (comment out if you don't want to make actual requests)
    try:
        await example_yonearth_scraping()
        await example_transcript_fixing()
    except Exception as e:
        print(f"Network examples skipped due to error: {e}")
    
    # Configuration examples that don't make network requests
    await example_custom_config_scraping()
    await example_template_config()
    
    print("\n" + "=" * 50)
    print("Examples complete!")
    print("\nTo use the scraper with your own podcast:")
    print("1. Create a custom configuration using create_custom_config()")
    print("2. Test with a small limit first: scraper.scrape_all_episodes(limit=3)")
    print("3. Adjust configuration based on the podcast's website structure")
    print("4. Run the full scrape once configuration is working")


if __name__ == "__main__":
    asyncio.run(main())