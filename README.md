# Podcast Scraper

A powerful, configurable web scraper for extracting podcast episodes and transcripts from podcast websites. Built with Crawl4AI for robust JavaScript-enabled crawling.

## Features

- **Universal podcast scraping** - Configurable for any podcast website
- **Smart transcript extraction** - Handles multiple transcript formats (h1, h2, h3 headers, headerless content)
- **Audio transcription with speaker separation** - Automatic Whisper + pyannote.audio for episodes without web transcripts
- **Flexible episode discovery** - Handles both numbered and descriptive URLs (e.g., `/episode-123-title/` and `/guest-name-topic/`)
- **Rich metadata extraction** - Episode titles, dates, descriptions, guest bios, related episodes
- **Multiple output formats** - JSON, Markdown, CSV
- **Intelligent incremental scraping** - Skip complete episodes but reprocess those missing transcripts
- **Transcript fixing** - Built-in tools to re-extract missing transcripts
- **Rate limiting** - Respectful crawling with configurable delays
- **No API keys required** - Works directly with website HTML

## Project Status: YonEarth Podcast Complete ✅

**🎉 Successfully scraped 172/172 episodes (100% completion)**
- **171 numbered episodes** (0-170) + 1 special guest episode
- **All episodes have complete transcripts** (avg. 38,731 characters each)
- **Zero duplicates or data quality issues**
- **Total transcript content**: 6.6+ million characters across all episodes

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

# Install system dependencies for audio transcription (optional)
# On macOS:
brew install ffmpeg
# On Ubuntu/Debian:
# sudo apt update && sudo apt install ffmpeg
# On Windows:
# Download from https://ffmpeg.org/download.html
```

### 2. Basic Usage

For YonEarth podcast (default configuration):
```bash
# Basic scraping
python scripts/scraper.py

# Skip existing episodes (incremental scraping)
python scripts/scraper.py --skip-existing

# Enable audio transcription for episodes without web transcripts
python scripts/scraper.py --enable-audio-transcription --skip-existing

# Use better Whisper model with speaker separation (requires HF token)
python scripts/scraper.py --enable-audio-transcription --whisper-model medium --hf-token YOUR_HF_TOKEN --skip-existing

# Test with limited episodes
python scripts/scraper.py --limit 10 --skip-existing
```

### 3. Audio Transcription Setup (Optional)

For episodes without existing transcripts, the scraper can generate them using Whisper + speaker diarization:

1. **Get Hugging Face Token:**
   - Visit https://huggingface.co/settings/tokens
   - Create a new token (read access sufficient)

2. **Accept Model License:**
   - Go to https://huggingface.co/pyannote/speaker-diarization-3.1
   - Click "Agree and access repository"

3. **Use with token:**
   ```bash
   python scripts/scraper.py --enable-audio-transcription --hf-token YOUR_TOKEN --skip-existing
   ```

### 4. Command Line Options

- `--skip-existing` - Skip episodes that have already been scraped
- `--enable-audio-transcription` - Generate transcripts from audio using Whisper + speaker diarization
- `--whisper-model` - Model size: tiny, base, small, medium, large (default: base)
- `--hf-token` - Hugging Face token for better speaker diarization (required for audio transcription)
- `--limit N` - Process only the first N episodes (useful for testing)

### 5. Transcribe Individual Episodes

For episodes with external audio or special cases:

```bash
# Transcribe a single episode with external audio URL
python scripts/transcribe_single_episode.py data/json/episode_greendreamer.json \
  --audio-url "https://example.com/audio.mp3" \
  --whisper-model medium \
  --hf-token YOUR_TOKEN

# Transcribe using audio URL already in JSON
python scripts/transcribe_single_episode.py data/json/episode_123.json
```

### 6. Fix Missing Transcripts

```bash
# Basic transcript fixing
python scripts/fix_transcripts.py

# With audio transcription enabled
python scripts/fix_transcripts.py --enable-audio-transcription

# Fix specific episodes
python scripts/fix_transcripts.py --episodes 144 161 163

# Interactive example
python scripts/audio_transcription_example.py
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
│   ├── scraper.py        # Main scraper with audio transcription support
│   ├── fix_transcripts.py # Transcript fixing utility  
│   ├── generic_scraper.py # Universal podcast scraping logic
│   ├── audio_transcriber.py # Audio transcription with speaker separation
│   ├── audio_transcription_example.py # Interactive example
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

### 3. Audio Transcription (NEW)
- **Automatic fallback** - When no web transcript exists, generates from audio
- **Speaker separation** - Uses pyannote.audio for speaker diarization  
- **Multiple Whisper models** - From tiny (fast) to large (accurate)
- **Clean formatting** - Outputs "Speaker 1:", "Speaker 2:", etc.
- **Metadata tracking** - Language detection, speaker count, duration

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

## Audio Transcription Setup

### Requirements
```bash
# Additional dependencies for audio transcription
pip install openai-whisper pyannote.audio torch torchaudio pydub
```

### Hardware Recommendations
- **CPU only**: Use `--whisper-model tiny` or `base`
- **GPU with 4GB+ VRAM**: Use `--whisper-model medium` 
- **GPU with 10GB+ VRAM**: Use `--whisper-model large`

### Hugging Face Token (Optional)
For better speaker diarization, get a free token from [huggingface.co](https://huggingface.co/settings/tokens):
```bash
python scripts/scraper.py --enable-audio-transcription --hf-token your_token_here
```

### Performance
- **Processing time**: 2-10 minutes per episode
- **GPU acceleration**: Automatically detected
- **Temporary files**: Auto-cleaned after processing

## Recent Improvements ✅

### Fixed Issues
- [x] **Episode Discovery**: Now finds all 170+ episodes (was missing 7)
- [x] **Transcript Extraction**: Improved logic recovers 90%+ of "missing" transcripts  
- [x] **Audio Transcription**: Automatic Whisper + speaker separation for episodes without web transcripts
- [x] **Incremental Scraping**: `--skip-existing` prevents duplicate work
- [x] **Command Line Interface**: Full argument support for all features

### Quality Improvements  
- [x] Universal transcript detection (h1, h2, h3, h4 headers + intro patterns)
- [x] Better content filtering (removes navigation, comments, etc.)
- [x] Audio fallback when web transcripts unavailable
- [x] Comprehensive metadata tracking
- [x] Progress indicators and error handling

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