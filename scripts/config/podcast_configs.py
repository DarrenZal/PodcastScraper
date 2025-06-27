"""
Podcast Configuration Templates

Collection of configurations for popular podcast platforms and individual podcasts.
Use these as starting points for adapting the scraper to new podcasts.
"""

from typing import Dict, Any


def get_yonearth_config() -> Dict[str, Any]:
    """Configuration for YonEarth Community Podcast (default)"""
    return {
        "base_url": "https://yonearth.org",
        "podcast_list_url": "https://yonearth.org/community-podcast/",
        "episode_url_pattern": r'/podcast/[^/]+/?$',  # Updated to handle both numbered and descriptive URLs
        "episode_link_selector": 'a.tve-dynamic-link',
        "episode_link_fallback_selector": 'a[href*="/podcast/"]',
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
        "wait_time": 3.0,
        "page_timeout": 30000,
        "max_transcript_paragraphs": 500
    }


def get_wordpress_podcast_config() -> Dict[str, Any]:
    """Generic configuration for WordPress-based podcasts"""
    return {
        "base_url": "https://example-podcast.com",
        "podcast_list_url": "https://example-podcast.com/episodes/",
        "episode_url_pattern": r'/\d{4}/\d{2}/episode-\d+',  # WordPress date-based URLs
        "episode_link_selector": 'a.podcast-episode',
        "episode_link_fallback_selector": 'a[href*="/episode"]',
        "pagination_pages": 5,
        "pagination_selector": '.page-numbers a',
        "podcast_name": "WordPress Podcast",
        "host_name": "Host Name",
        "transcript_selectors": {
            "headers": ["h1", "h2", "h3"],
            "transcript_keywords": ["Transcript", "Show Notes", "Full Text"],
            "podcast_intro_patterns": [
                "Welcome to",
                "This is",
                "I'm your host"
            ],
            "stop_patterns": [
                "about the host",
                "show notes",
                "related episodes",
                "comments"
            ],
            "skip_patterns": [
                "subscribe", "share", "download", "itunes", "spotify"
            ]
        },
        "wait_time": 2.0,
        "page_timeout": 30000
    }


def get_squarespace_podcast_config() -> Dict[str, Any]:
    """Generic configuration for Squarespace-based podcasts"""
    return {
        "base_url": "https://example-podcast.squarespace.com",
        "podcast_list_url": "https://example-podcast.squarespace.com/episodes",
        "episode_url_pattern": r'/episodes/episode-\d+',
        "episode_link_selector": 'a.list-item-link',
        "episode_link_fallback_selector": 'a[href*="/episodes/"]',
        "pagination_pages": 3,
        "pagination_selector": '.pagination a',
        "podcast_name": "Squarespace Podcast",
        "host_name": "Host Name",
        "transcript_selectors": {
            "headers": ["h1", "h2", "h3"],
            "transcript_keywords": ["Transcript", "Episode Transcript"],
            "podcast_intro_patterns": [
                "Welcome to",
                "Hello and welcome"
            ],
            "stop_patterns": [
                "about", "contact", "subscribe"
            ],
            "skip_patterns": [
                "social media", "follow us", "rate and review"
            ]
        },
        "wait_time": 2.5,
        "page_timeout": 25000
    }


def get_simple_podcast_config() -> Dict[str, Any]:
    """Minimal configuration for simple podcast websites"""
    return {
        "base_url": "https://simple-podcast.com",
        "podcast_list_url": "https://simple-podcast.com/episodes.html",
        "episode_url_pattern": r'/ep\d+\.html',
        "episode_link_selector": 'a.episode',
        "pagination_pages": 1,  # No pagination
        "podcast_name": "Simple Podcast",
        "transcript_selectors": {
            "headers": ["h2"],
            "transcript_keywords": ["Transcript"],
            "podcast_intro_patterns": ["Welcome"],
            "stop_patterns": ["contact"],
            "skip_patterns": ["subscribe"]
        },
        "wait_time": 1.0,
        "page_timeout": 15000
    }


def get_anchor_fm_config() -> Dict[str, Any]:
    """Configuration for Anchor.fm hosted podcasts"""
    return {
        "base_url": "https://anchor.fm",
        "podcast_list_url": "https://anchor.fm/podcast-name/episodes",
        "episode_url_pattern": r'/podcast-name/episodes/[^/]+',
        "episode_link_selector": 'a[href*="/episodes/"]',
        "pagination_pages": 5,
        "pagination_selector": 'button[aria-label="Next page"]',
        "podcast_name": "Anchor.fm Podcast",
        "transcript_selectors": {
            "headers": ["h1", "h2"],
            "transcript_keywords": ["Transcript", "Episode transcript"],
            "podcast_intro_patterns": [
                "Welcome to",
                "This is"
            ],
            "stop_patterns": [
                "episode notes",
                "powered by anchor"
            ],
            "skip_patterns": [
                "share episode", "embed", "sponsor"
            ]
        },
        "wait_time": 3.0,
        "page_timeout": 30000
    }


def get_buzzsprout_config() -> Dict[str, Any]:
    """Configuration for Buzzsprout hosted podcasts"""
    return {
        "base_url": "https://podcast-name.buzzsprout.com",
        "podcast_list_url": "https://podcast-name.buzzsprout.com/",
        "episode_url_pattern": r'/\d+/[^/]+',
        "episode_link_selector": 'a.episode-title-link',
        "pagination_pages": 10,
        "pagination_selector": '.pagination a',
        "podcast_name": "Buzzsprout Podcast",
        "transcript_selectors": {
            "headers": ["h1", "h2"],
            "transcript_keywords": ["Transcript", "Show transcript"],
            "podcast_intro_patterns": [
                "Welcome",
                "Today on"
            ],
            "stop_patterns": [
                "powered by buzzsprout",
                "episode notes"
            ],
            "skip_patterns": [
                "subscribe", "share", "download"
            ]
        },
        "wait_time": 2.0,
        "page_timeout": 25000
    }


def get_libsyn_config() -> Dict[str, Any]:
    """Configuration for Libsyn hosted podcasts"""
    return {
        "base_url": "https://podcast-name.libsyn.com",
        "podcast_list_url": "https://podcast-name.libsyn.com/podcast",
        "episode_url_pattern": r'/[^/]+-\d+$',
        "episode_link_selector": 'a.libsyn-episode-title',
        "pagination_pages": 8,
        "pagination_selector": '.pagination a',
        "podcast_name": "Libsyn Podcast",
        "transcript_selectors": {
            "headers": ["h1", "h2", "h3"],
            "transcript_keywords": ["Transcript", "Full episode transcript"],
            "podcast_intro_patterns": [
                "Welcome to",
                "Hello everyone"
            ],
            "stop_patterns": [
                "powered by libsyn",
                "show notes"
            ],
            "skip_patterns": [
                "share this episode", "download episode"
            ]
        },
        "wait_time": 2.5,
        "page_timeout": 30000
    }


# Registry of all available configurations
PODCAST_CONFIGS = {
    "yonearth": get_yonearth_config,
    "wordpress": get_wordpress_podcast_config,
    "squarespace": get_squarespace_podcast_config,
    "simple": get_simple_podcast_config,
    "anchor": get_anchor_fm_config,
    "buzzsprout": get_buzzsprout_config,
    "libsyn": get_libsyn_config,
}


def get_config(config_name: str) -> Dict[str, Any]:
    """Get a configuration by name"""
    if config_name not in PODCAST_CONFIGS:
        available = ", ".join(PODCAST_CONFIGS.keys())
        raise ValueError(f"Unknown config '{config_name}'. Available: {available}")
    
    return PODCAST_CONFIGS[config_name]()


def list_available_configs() -> list:
    """List all available configuration names"""
    return list(PODCAST_CONFIGS.keys())


def create_custom_config(
    base_url: str,
    podcast_list_url: str,
    podcast_name: str,
    episode_url_pattern: str = r'/episode-\d+',
    **kwargs
) -> Dict[str, Any]:
    """
    Create a custom configuration with required parameters
    
    Args:
        base_url: Base URL of the podcast website
        podcast_list_url: URL of the episodes listing page
        podcast_name: Name of the podcast
        episode_url_pattern: Regex pattern for episode URLs
        **kwargs: Additional configuration options
    """
    config = {
        "base_url": base_url,
        "podcast_list_url": podcast_list_url,
        "podcast_name": podcast_name,
        "episode_url_pattern": episode_url_pattern,
        "episode_link_selector": kwargs.get("episode_link_selector", "a"),
        "pagination_pages": kwargs.get("pagination_pages", 1),
        "host_name": kwargs.get("host_name", "Host"),
        "transcript_selectors": {
            "headers": kwargs.get("transcript_headers", ["h1", "h2", "h3"]),
            "transcript_keywords": kwargs.get("transcript_keywords", ["Transcript"]),
            "podcast_intro_patterns": kwargs.get("intro_patterns", ["Welcome to"]),
            "stop_patterns": kwargs.get("stop_patterns", ["about", "contact"]),
            "skip_patterns": kwargs.get("skip_patterns", ["subscribe", "share"])
        },
        "wait_time": kwargs.get("wait_time", 2.0),
        "page_timeout": kwargs.get("page_timeout", 30000)
    }
    
    # Add any additional kwargs
    for key, value in kwargs.items():
        if key not in config:
            config[key] = value
    
    return config


# Example usage:
if __name__ == "__main__":
    # List available configurations
    print("Available configurations:")
    for config_name in list_available_configs():
        print(f"  - {config_name}")
    
    # Get a specific configuration
    yonearth_config = get_config("yonearth")
    print(f"\nYonEarth config: {yonearth_config['podcast_name']}")
    
    # Create a custom configuration
    custom_config = create_custom_config(
        base_url="https://my-podcast.com",
        podcast_list_url="https://my-podcast.com/episodes",
        podcast_name="My Custom Podcast",
        episode_url_pattern=r'/ep\d+',
        host_name="John Doe",
        pagination_pages=5
    )
    print(f"\nCustom config: {custom_config['podcast_name']}")