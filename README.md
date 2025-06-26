# Podcast Scraper

A powerful, configurable web scraper for extracting podcast episodes and transcripts from podcast websites. Built with Crawl4AI for robust JavaScript-enabled crawling.

## Features

- **Universal podcast scraping** - Configurable for any podcast website
- **Smart transcript extraction** - Handles multiple transcript formats (h1, h2, h3 headers, headerless content)
- **Episode discovery** - Automatically finds all episode URLs with pagination support
- **Rich metadata extraction** - Episode titles, dates, descriptions, guest bios, related episodes
- **Multiple output formats** - JSON, Markdown, CSV
- **Transcript fixing** - Built-in tools to re-extract missing transcripts
- **Whisper integration ready** - Identifies episodes needing audio transcription
- **Rate limiting** - Respectful crawling with configurable delays
- **No API keys required** - Works directly with website HTML

## Quick Start

### 1. Setup Environment

```bash
# Clone the repository
git clone https://github.com/DarrenZal/PodcastScraper.git
cd PodcastScraper

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install browser for Crawl4AI
playwright install chromium
```

### 2. Basic Usage

For YonEarth podcast (default configuration):
```bash
python scripts/scraper.py
```

For a custom podcast, create a configuration file (see Configuration section below).

### 3. Fix Missing Transcripts

```bash
python scripts/fix_transcripts.py
```

## Configuration

### Default Configuration (YonEarth Podcast)

The scraper comes pre-configured for the YonEarth Community Podcast. To use it for other podcasts, modify the configuration in `scripts/scraper.py`:

```python
class PodcastScraper:
    def __init__(self, config=None):
        if config is None:
            # Default YonEarth configuration
            config = {
                "base_url": "https://yonearth.org",
                "podcast_list_url": "https://yonearth.org/community-podcast/",
                "episode_url_pattern": r'/podcast/episode-\d+',
                "episode_link_selector": 'a.tve-dynamic-link',
                "pagination_pages": 10,
                "podcast_name": "YonEarth Community Podcast"
            }
        self.config = config
```

### Custom Podcast Configuration

Create a custom configuration for your podcast:

```python
custom_config = {
    "base_url": "https://example-podcast.com",
    "podcast_list_url": "https://example-podcast.com/episodes/",
    "episode_url_pattern": r'/episodes/\d+',
    "episode_link_selector": 'a.episode-link',
    "pagination_pages": 5,
    "podcast_name": "My Custom Podcast",
    "transcript_selectors": {
        "headers": ["h1", "h2", "h3", "h4"],
        "transcript_keywords": ["Transcript", "Full Transcript"],
        "podcast_intro_patterns": [
            "Welcome to My Custom Podcast",
            "This is the host"
        ]
    }
}

scraper = PodcastScraper(config=custom_config)
```

## Project Structure

```
podcastScraper/
├── README.md
├── CLAUDE.md              # AI assistant documentation
├── requirements.txt       # Python dependencies
├── scripts/
│   ├── scraper.py        # Main scraper (generic + YonEarth config)
│   ├── fix_transcripts.py # Transcript fixing utility
│   └── config/
│       └── podcast_configs.py # Configuration templates
├── data/                 # Output directory
│   ├── json/            # Raw episode data
│   ├── markdown/        # Human-readable transcripts
│   ├── csv/             # Summary spreadsheets
│   ├── fixed_transcripts/ # Re-extracted transcripts
│   ├── episode_urls.json
│   ├── metadata.json
│   └── transcript_fix_report.json
└── examples/            # Example configurations for popular podcasts
```

## Output Formats

### JSON Format
Each episode saved as `data/json/episode_N.json`:
```json
{
  "title": "Episode 163 – Guest Name, Title",
  "audio_url": "https://...",
  "publish_date": "June 10, 2024 1:18 pm",
  "url": "https://...",
  "episode_number": 163,
  "subtitle": "Episode Theme",
  "description": "Episode description...",
  "about_sections": {
    "about_guest": "Guest bio..."
  },
  "full_transcript": "Welcome to the podcast...",
  "related_episodes": [...]
}
```

### Markdown Format
Human-readable transcripts in `data/markdown/episode_N.md`

### CSV Summary
Episode overview in `data/csv/episodes_summary.csv` with transcript status

## Transcript Extraction

The scraper uses advanced transcript extraction that handles multiple formats:

### 1. Header-Based Transcripts
- `<h1>Transcript</h1>`
- `<h2>Transcript</h2>` 
- `<h3>Full Transcript</h3>`

### 2. Headerless Transcripts
- Detects podcast intro patterns
- Extracts content until bio/resources sections

### 3. Missing Transcripts
- Identifies episodes needing Whisper transcription
- Provides audio URLs for automated transcription

## Advanced Usage

### Test with Limited Episodes
```python
# Test with 3 episodes
await scraper.scrape_all_episodes(limit=3)
```

### Fix Specific Episodes
```python
# Fix transcripts for specific episodes
await scraper.fix_existing_transcripts([144, 163, 165])
```

### Custom Rate Limiting
```python
# Adjust crawling speed
scraper.batch_size = 3
scraper.batch_delay = 5.0  # 5 seconds between batches
```

## Troubleshooting

### Common Issues

1. **No transcripts extracted**
   - Check transcript selector configuration
   - Run transcript fixing utility
   - Verify website structure hasn't changed

2. **Episodes not found**
   - Verify episode URL pattern
   - Check pagination configuration
   - Ensure JavaScript is enabled

3. **Rate limiting errors**
   - Increase delays between requests
   - Reduce batch size
   - Check website's robots.txt

### Debug Mode
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

Based on our transcript investigation findings:

### Immediate Actions
- [ ] Apply fixed transcript extraction to all 163 episodes
- [ ] Re-run scraper with improved logic on episodes 0-162  
- [ ] Identify episodes truly needing Whisper transcription (like episode 161)
- [ ] Set up Whisper pipeline for audio-only episodes

### Transcript Recovery
- [ ] Expected to recover transcripts for ~80-90% of "missing" episodes
- [ ] Estimated ~150+ episodes may have extractable transcripts
- [ ] Only ~10-20 episodes likely need Whisper transcription

### Quality Improvements  
- [ ] Add transcript validation (minimum word count, intro detection)
- [ ] Implement content cleaning (remove navigation elements)
- [ ] Add automatic retry for failed extractions
- [ ] Create transcript completeness report

### Monitoring
- [ ] Set up periodic re-scraping for new episodes
- [ ] Monitor website structure changes
- [ ] Track transcript extraction success rates

## Contributing

1. Fork the repository on [GitHub](https://github.com/DarrenZal/PodcastScraper)
2. Create a feature branch (`git checkout -b feature/new-podcast`)
3. Add your podcast configuration to `examples/` or `scripts/config/`
4. Test with your podcast
5. Commit your changes (`git commit -am 'Add support for XYZ podcast'`)
6. Push to the branch (`git push origin feature/new-podcast`)
7. Submit a pull request

### Reporting Issues

- **Bug reports**: Use the [bug report template](https://github.com/DarrenZal/PodcastScraper/issues/new?template=bug_report.md)
- **New podcast support**: Use the [podcast configuration template](https://github.com/DarrenZal/PodcastScraper/issues/new?template=podcast_configuration.md)

## License

MIT License - see LICENSE file for details

## Credits

- Built with [Crawl4AI](https://github.com/unclecode/crawl4ai)
- Default configuration for [YonEarth Community Podcast](https://yonearth.org/community-podcast/)
- Transcript extraction improvements developed through Claude Code investigation