#!/usr/bin/env python3
"""
Transcribe a single episode by file path or URL

This utility allows transcribing individual episodes that may have been missed
or need re-transcription, including episodes from external sources.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.audio_transcriber import AudioTranscriber


async def transcribe_single_episode(
    json_path: str,
    audio_url: Optional[str] = None,
    whisper_model: str = "base",
    hf_token: Optional[str] = None
):
    """
    Transcribe a single episode from its JSON file
    
    Args:
        json_path: Path to the episode JSON file
        audio_url: Optional audio URL override (if not in JSON)
        whisper_model: Whisper model size (tiny, base, small, medium, large)
        hf_token: Hugging Face token for speaker diarization
    """
    
    json_path = Path(json_path)
    if not json_path.exists():
        print(f"Error: File not found: {json_path}")
        return
    
    # Load episode data
    with open(json_path, 'r', encoding='utf-8') as f:
        episode_data = json.load(f)
    
    # Get audio URL
    if audio_url:
        episode_data['audio_url'] = audio_url
    elif not episode_data.get('audio_url'):
        print("Error: No audio URL found in episode data and none provided")
        return
    
    print(f"Transcribing: {episode_data.get('title', 'Unknown')}")
    print(f"Audio URL: {episode_data['audio_url']}")
    
    # Initialize transcriber
    transcriber = AudioTranscriber(
        whisper_model=whisper_model,
        use_auth_token=hf_token or os.getenv('HF_TOKEN')
    )
    
    # Get episode identifier
    episode_id = episode_data.get('episode_number', json_path.stem)
    
    # Transcribe
    result = await transcriber.transcribe_from_url(
        episode_data['audio_url'],
        str(episode_id)
    )
    
    if result['success']:
        print(f"✓ Transcription successful: {len(result['transcript'])} characters")
        
        # Update episode data
        episode_data['full_transcript'] = result['transcript']
        episode_data['audio_transcription_metadata'] = result['metadata']
        
        # Save back to file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(episode_data, f, indent=2, ensure_ascii=False)
        
        print(f"Updated: {json_path}")
        
        # Update markdown if it exists
        md_path = json_path.parent.parent / 'markdown' / f"{json_path.stem}.md"
        if md_path.exists():
            md_content = f"""# {episode_data.get('title', 'Episode')}

**Published:** {episode_data.get('publish_date', 'Unknown')}  
**URL:** {episode_data.get('url', '')}  
**Audio:** {episode_data.get('audio_url', '')}

## Description

{episode_data.get('description', '')}

## Transcript

{result['transcript']}
"""
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            print(f"Updated: {md_path}")
    
    else:
        print(f"✗ Transcription failed: {result['error']}")


def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Transcribe a single podcast episode from audio'
    )
    parser.add_argument(
        'json_file',
        help='Path to episode JSON file'
    )
    parser.add_argument(
        '--audio-url',
        help='Override audio URL (if not in JSON file)'
    )
    parser.add_argument(
        '--whisper-model',
        default='base',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        help='Whisper model size (default: base)'
    )
    parser.add_argument(
        '--hf-token',
        help='Hugging Face token for speaker diarization'
    )
    
    args = parser.parse_args()
    
    # Run transcription
    asyncio.run(transcribe_single_episode(
        args.json_file,
        args.audio_url,
        args.whisper_model,
        args.hf_token
    ))


if __name__ == "__main__":
    main()