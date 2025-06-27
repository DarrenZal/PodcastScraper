# CLAUDE.md - AI Assistant Documentation

This file provides context and guidance for AI assistants working with the Podcast Scraper project.

## Final Project Status: YonEarth Podcast Complete ✅

**🎉 Successfully scraped 172/172 episodes (100% completion)**
- **171 numbered episodes** (0-170) + 1 special guest episode (Greendreamer)
- **All episodes have complete transcripts** (avg. 38,731 characters each)  
- **Zero duplicates or data quality issues**
- **Total transcript content**: 6.6+ million characters across all episodes

### Key Technical Achievements

1. **Flexible URL Pattern Matching**: Enhanced scraper to handle both numbered (`/episode-123-title/`) and descriptive (`/guest-name-topic/`) URL formats
2. **Mixed Episode Number Handling**: Support for both integer and string episode identifiers
3. **Intelligent Skip Logic**: `--skip-existing` now checks transcript completeness, not just file existence
4. **Audio Transcription Integration**: Whisper + pyannote.audio for episodes without web transcripts
5. **External Audio Source Support**: Successfully transcribed 40-minute Greendreamer episode from Captivate.fm

### Transcript Extraction Fixes

The original transcript extraction had ~93% failure rate. Fixed issues:
- **Header Detection**: Now handles h1, h2, h3, h4 transcript headers
- **Content Boundaries**: Improved stop conditions to prevent premature cutoffs  
- **Dynamic Content**: Added proper wait times for JavaScript-loaded transcripts
- **Fallback Methods**: Multiple extraction strategies for different page layouts

**Results**: 99.4% transcript extraction success rate (171/172 episodes)

## Project Overview

This is a **configurable podcast web scraper** built with Crawl4AI that extracts episodes and transcripts from podcast websites. The default configuration is set up for the YonEarth Community Podcast, but it can be adapted for any podcast website.

## Key Technical Context

### Transcript Extraction Challenge (SOLVED)

**Issue**: Originally, ~93% of episodes (152/163) showed missing transcripts despite transcripts being available on the website.

**Root Cause**: The transcript extraction logic had several flaws:
1. Only looked for `<h2>` and `<h3>` transcript headers (missed `<h1>` headers)
2. Had overly broad stop conditions that prematurely cut off transcript content
3. Insufficient wait time for dynamic JavaScript content loading

**Solution**: Fixed transcript extraction logic that handles:
- Multiple header formats (`<h1>`, `<h2>`, `<h3>`, `<h4>`)
- Headerless transcripts (detected via podcast intro patterns)
- Proper wait times for dynamic content
- More precise stop conditions

**Results**: Successfully extracted 76,160+ characters of previously "missing" transcripts from test episodes.

### Architecture

```
PodcastScraper (main class)
├── Configuration system (podcast-specific settings)
├── Episode URL discovery (with pagination support)
├── Transcript extraction (multiple format support)
├── Metadata extraction (titles, dates, bios, related episodes)
└── Output generation (JSON, Markdown, CSV)
```

### Key Files

- `scripts/scraper.py` - Main scraper (currently YonEarth-specific, needs genericization)
- `scripts/fix_transcripts.py` - Utility to re-extract transcripts with improved logic
- `data/transcript_fix_report.json` - Analysis results from transcript fixing
- `requirements.txt` - Dependencies (Crawl4AI, pandas, beautifulsoup4, etc.)

## Configuration System

The scraper uses a configuration dictionary to adapt to different podcast websites:

```python
config = {
    "base_url": "https://podcast-site.com",
    "podcast_list_url": "https://podcast-site.com/episodes/",
    "episode_url_pattern": r'/episodes/\d+',
    "episode_link_selector": 'a.episode-link',
    "pagination_pages": 5,
    "podcast_name": "Podcast Name",
    "transcript_selectors": {
        "headers": ["h1", "h2", "h3", "h4"],
        "transcript_keywords": ["Transcript", "Full Transcript"],
        "podcast_intro_patterns": ["Welcome to...", "Host intro..."]
    }
}
```

## Development Guidelines

### When Working with this Project

1. **Always test transcript extraction** - Use the test episodes (144, 161, 163) to verify transcript extraction works
2. **Respect rate limits** - Include appropriate delays between requests
3. **Handle JavaScript content** - Many podcast sites use dynamic loading
4. **Validate configurations** - Test new podcast configurations thoroughly
5. **Check output completeness** - Verify JSON structure matches expected format

### Common Tasks

**Adding a new podcast configuration**:
1. Analyze the podcast website structure
2. Identify episode URL patterns and selectors
3. Test transcript extraction with sample episodes
4. Create configuration in `examples/` directory

**Debugging transcript extraction**:
1. Check if transcript exists on source webpage
2. Verify header detection and content extraction
3. Test with different wait times for dynamic content
4. Use debug logging to trace extraction process

**Performance optimization**:
1. Adjust batch sizes and delays
2. Implement caching for repeated requests
3. Use parallel processing where appropriate
4. Monitor memory usage for large datasets

### Code Quality Standards

- **Error handling**: Graceful handling of network errors, missing content, malformed HTML
- **Logging**: Comprehensive logging for debugging and monitoring
- **Type hints**: Use Python type hints for better code documentation
- **Documentation**: Clear docstrings for all public methods
- **Testing**: Include test cases for different podcast website structures

## Data Formats

### Episode JSON Structure
```json
{
  "title": "Episode Title",
  "audio_url": "https://audio-file-url",
  "publish_date": "Date string",
  "url": "Episode page URL",
  "episode_number": 123,
  "subtitle": "Episode subtitle/theme",
  "description": "Episode description",
  "about_sections": {
    "about_guest": "Guest biography"
  },
  "full_transcript": "Complete transcript text",
  "related_episodes": [...]
}
```

### Transcript Extraction Patterns

1. **Header-based**: `<h1>Transcript</h1>` followed by content
2. **Intro-based**: Detect "Welcome to [Podcast Name]" patterns
3. **Structured**: Content within specific container elements
4. **Generated**: Auto-generated transcripts with disclaimers

## Performance Considerations

- **Memory**: Large transcripts can consume significant memory
- **Network**: Respectful crawling to avoid overwhelming servers
- **Storage**: JSON files can become large with full transcripts
- **Processing time**: Transcript extraction can be CPU-intensive

## Audio Transcription (NEW)

### Overview
The system now supports automatic audio transcription with speaker separation for episodes without existing transcripts. This feature uses:
- **OpenAI Whisper** for speech-to-text transcription
- **pyannote.audio** for speaker diarization (speaker separation)
- **Automatic fallback** when no web transcript is found

### Usage

#### Basic Usage
```bash
# Enable audio transcription for all episodes without transcripts
python fix_transcripts.py --enable-audio-transcription

# Use specific Whisper model (tiny, base, small, medium, large)
python fix_transcripts.py --enable-audio-transcription --whisper-model medium

# Transcribe specific episodes
python fix_transcripts.py --enable-audio-transcription --episodes 144 163

# With Hugging Face token for better speaker diarization
python fix_transcripts.py --enable-audio-transcription --hf-token your_token_here
```

#### Example Script
```bash
# Run the interactive example
python audio_transcription_example.py
```

### Features

1. **Automatic Detection**: Detects episodes with `NO_TRANSCRIPT_AVAILABLE` status
2. **Audio Download**: Downloads audio files from episode URLs
3. **Format Conversion**: Converts various audio formats to WAV for processing
4. **Speech Recognition**: Uses Whisper models (tiny to large) for transcription
5. **Speaker Separation**: Identifies and labels different speakers in the conversation
6. **Formatted Output**: Generates clean transcripts with speaker labels (e.g., "Speaker 1:", "Speaker 2:")

### Dependencies
```
openai-whisper>=20231117
pyannote.audio>=3.1.0
torch>=2.0.0
torchaudio>=2.0.0
pydub>=0.25.1
```

### Configuration Options

- **whisper_model**: Model size (tiny, base, small, medium, large)
  - `tiny`: Fastest, least accurate (~1GB VRAM)
  - `base`: Good balance (~2GB VRAM) 
  - `medium`: Better accuracy (~5GB VRAM)
  - `large`: Best accuracy (~10GB VRAM)

- **use_auth_token**: Hugging Face token for pyannote models (optional but recommended)

### Performance Considerations

- **Processing Time**: 2-10 minutes per episode depending on length and hardware
- **GPU Acceleration**: Automatically uses CUDA if available
- **Memory Usage**: Varies by model size (1-10GB VRAM)
- **Disk Space**: Temporary audio files are cleaned up automatically

### Output Format

Generated transcripts include:
- Speaker labels (Speaker 1, Speaker 2, etc.)
- Clean formatting with speaker changes
- Metadata about the transcription process
- Language detection
- Speaker count and timing information

### Integration

The audio transcription is fully integrated into the existing `fix_transcripts.py` workflow:
- Episodes are first checked for web-based transcripts
- If no transcript found, audio transcription is attempted
- Results are saved in the same format as web-extracted transcripts
- Metadata includes both web and audio transcription information

## Future Enhancements

### Planned Features
- [x] Whisper integration for audio-only episodes ✓ COMPLETED
- [ ] Automatic podcast structure detection
- [ ] Real-time monitoring for new episodes
- [ ] Transcript quality validation
- [ ] Multi-language support
- [ ] Custom speaker name mapping
- [ ] Transcript quality scoring

### Integration Opportunities
- [ ] RSS feed integration
- [ ] Database storage options
- [ ] API endpoints for scraped data
- [ ] Search functionality across transcripts
- [ ] Analytics and reporting tools

## Troubleshooting Guide

### Common Issues

1. **No episodes found**: Check URL patterns and selectors
2. **Missing transcripts**: Verify transcript extraction logic
3. **Rate limiting**: Adjust delays and batch sizes
4. **JavaScript errors**: Ensure proper browser configuration
5. **Memory issues**: Implement streaming for large datasets

### Debug Steps

1. Test with small episode limits first
2. Enable verbose logging
3. Check network requests in browser dev tools
4. Validate HTML structure with BeautifulSoup
5. Test individual components in isolation

## Dependencies

- **Crawl4AI**: Core web crawling with JavaScript support
- **BeautifulSoup4**: HTML parsing and content extraction
- **pandas**: Data manipulation and CSV generation
- **asyncio**: Asynchronous processing for performance
- **pathlib**: Modern file path handling

## Security Considerations

- **Respect robots.txt**: Check website crawling policies
- **Rate limiting**: Avoid overwhelming target servers
- **Content usage**: Respect copyright and fair use policies
- **Data storage**: Consider privacy implications of stored transcripts
- **Dependencies**: Keep packages updated for security patches

## Contributing

When contributing to this project:

1. **Test thoroughly** with multiple podcast configurations
2. **Document changes** in both code and CLAUDE.md
3. **Maintain backwards compatibility** with existing configurations
4. **Add example configurations** for new supported podcasts
5. **Update README** with new features and usage instructions

## Known Limitations

- **Website structure changes**: May break existing configurations
- **Dynamic content**: Some transcripts may require complex JavaScript execution
- **Audio-only episodes**: Requires Whisper or similar transcription service
- **Rate limiting**: Some sites may have strict crawling restrictions
- **Content variations**: Different podcast platforms use various formats

This documentation should help AI assistants understand the project structure, key challenges, and development guidelines for working with the Podcast Scraper effectively.