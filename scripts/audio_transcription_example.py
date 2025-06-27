#!/usr/bin/env python3
"""
Audio Transcription Example

Example script showing how to use the audio transcription functionality
to generate transcripts with speaker separation for episodes without existing transcripts.
"""

import asyncio
import json
from pathlib import Path

from fix_transcripts import TranscriptFixer


async def example_audio_transcription():
    """Example of using audio transcription for episodes without transcripts"""
    
    print("Audio Transcription Example")
    print("=" * 50)
    
    # Initialize the transcript fixer with audio transcription enabled
    fixer = TranscriptFixer(
        enable_audio_transcription=True,
        whisper_model="base",  # You can use: tiny, base, small, medium, large
        hf_token=None  # Add your Hugging Face token here if you have one
    )
    
    # Load existing episodes to find ones without transcripts
    episodes = fixer.load_existing_episodes()
    
    if not episodes:
        print("No existing episodes found. Please run the main scraper first.")
        return
    
    # Find episodes without transcripts that have audio URLs
    episodes_without_transcripts = []
    for episode in episodes:
        if (not episode.get('full_transcript') or len(episode.get('full_transcript', '')) < 100) and episode.get('audio_url'):
            episodes_without_transcripts.append(episode)
    
    print(f"Found {len(episodes_without_transcripts)} episodes without transcripts that have audio URLs")
    
    if not episodes_without_transcripts:
        print("No episodes found that need audio transcription.")
        return
    
    # Show first few episodes
    print("\nEpisodes that could benefit from audio transcription:")
    for i, episode in enumerate(episodes_without_transcripts[:5]):
        episode_num = episode.get('episode_number', 'Unknown')
        title = episode.get('title', 'Unknown Title')
        audio_url = episode.get('audio_url', 'No URL')
        print(f"  {i+1}. Episode {episode_num}: {title[:50]}...")
        print(f"     Audio URL: {audio_url[:80]}...")
    
    if len(episodes_without_transcripts) > 5:
        print(f"     ... and {len(episodes_without_transcripts) - 5} more episodes")
    
    # Ask user if they want to proceed
    print(f"\nNote: Audio transcription requires significant computational resources and time.")
    print(f"Each episode may take 2-10 minutes depending on length and your hardware.")
    print(f"GPU acceleration will be used if available.")
    
    proceed = input(f"\nDo you want to transcribe the first episode? (y/N): ").lower().strip()
    
    if proceed != 'y':
        print("Audio transcription cancelled.")
        return
    
    # Transcribe the first episode as an example
    test_episode = episodes_without_transcripts[0]
    episode_num = test_episode.get('episode_number', 0)
    
    print(f"\nTranscribing Episode {episode_num}...")
    print(f"Title: {test_episode.get('title', 'Unknown')}")
    print(f"Audio URL: {test_episode.get('audio_url', 'Unknown')}")
    
    # Run the transcription
    results = await fixer.fix_transcripts(episode_numbers=[episode_num])
    
    if results:
        result = results[0]
        if result.get('status') == 'AUDIO_TRANSCRIPT_GENERATED':
            print(f"\n✓ Audio transcription successful!")
            print(f"Generated transcript length: {len(result.get('audio_transcript', ''))} characters")
            print(f"Speakers detected: {result.get('audio_metadata', {}).get('speakers_detected', 0)}")
            print(f"Language detected: {result.get('audio_metadata', {}).get('language', 'unknown')}")
            print(f"Duration: {result.get('audio_metadata', {}).get('duration', 0):.1f} seconds")
            
            # Show transcript preview
            transcript = result.get('audio_transcript', '')
            if transcript:
                print(f"\nTranscript Preview (first 500 characters):")
                print("-" * 50)
                print(transcript[:500] + ("..." if len(transcript) > 500 else ""))
                print("-" * 50)
            
            # Show where the files were saved
            data_dir = fixer.data_dir
            json_file = data_dir / "json" / f"episode_{episode_num}.json"
            md_file = data_dir / "markdown" / f"episode_{episode_num}.md"
            
            print(f"\nFiles updated:")
            print(f"  JSON: {json_file}")
            print(f"  Markdown: {md_file}")
            
        else:
            print(f"\n✗ Audio transcription failed:")
            print(f"Status: {result.get('status', 'Unknown')}")
            if result.get('error'):
                print(f"Error: {result.get('error')}")
    
    print(f"\nTo transcribe all episodes without transcripts, run:")
    print(f"python fix_transcripts.py --enable-audio-transcription")
    print(f"\nTo transcribe specific episodes, run:")
    print(f"python fix_transcripts.py --enable-audio-transcription --episodes {episode_num}")


if __name__ == "__main__":
    asyncio.run(example_audio_transcription())