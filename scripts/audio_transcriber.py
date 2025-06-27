#!/usr/bin/env python3
"""
Audio Transcription Module

Generates transcripts from audio files with speaker separation using Whisper and pyannote.audio.
Integrates with the existing podcast scraper to handle episodes without transcripts.
"""

import asyncio
import json
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import logging

import requests
import whisper
import torch
from pyannote.audio import Pipeline
from pydub import AudioSegment
from pydub.utils import which

logger = logging.getLogger(__name__)


class AudioTranscriber:
    """Handles audio transcription with speaker diarization"""
    
    def __init__(self, 
                 whisper_model: str = "base",
                 diarization_model: str = "pyannote/speaker-diarization-3.1",
                 use_auth_token: Optional[str] = None):
        """
        Initialize the audio transcriber
        
        Args:
            whisper_model: Whisper model size (tiny, base, small, medium, large)
            diarization_model: Pyannote model for speaker diarization
            use_auth_token: Hugging Face token for accessing pyannote models
        """
        self.whisper_model_name = whisper_model
        self.diarization_model_name = diarization_model
        self.use_auth_token = use_auth_token
        
        # Initialize models
        self.whisper_model = None
        self.diarization_pipeline = None
        
        # Check for ffmpeg
        if not which("ffmpeg"):
            logger.warning("ffmpeg not found. Audio conversion may fail.")
    
    def _load_models(self):
        """Lazy load models to avoid startup time"""
        if self.whisper_model is None:
            logger.info(f"Loading Whisper model: {self.whisper_model_name}")
            self.whisper_model = whisper.load_model(self.whisper_model_name)
        
        if self.diarization_pipeline is None:
            logger.info(f"Loading diarization model: {self.diarization_model_name}")
            try:
                self.diarization_pipeline = Pipeline.from_pretrained(
                    self.diarization_model_name,
                    use_auth_token=self.use_auth_token
                )
                # Use GPU if available
                if torch.cuda.is_available():
                    self.diarization_pipeline = self.diarization_pipeline.to(torch.device("cuda"))
            except Exception as e:
                logger.error(f"Failed to load diarization model: {e}")
                logger.info("Continuing without speaker diarization")
                self.diarization_pipeline = None
    
    async def download_audio(self, audio_url: str, output_path: str) -> bool:
        """
        Download audio file from URL
        
        Args:
            audio_url: URL to download audio from
            output_path: Local path to save audio file
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            logger.info(f"Downloading audio from: {audio_url}")
            
            # Use requests to download with streaming
            response = requests.get(audio_url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify file was downloaded
            if os.path.getsize(output_path) > 0:
                logger.info(f"Audio downloaded successfully: {os.path.getsize(output_path)} bytes")
                return True
            else:
                logger.error("Downloaded file is empty")
                return False
                
        except Exception as e:
            logger.error(f"Failed to download audio: {e}")
            return False
    
    def convert_to_wav(self, input_path: str, output_path: str) -> bool:
        """
        Convert audio file to WAV format for better compatibility
        
        Args:
            input_path: Path to input audio file
            output_path: Path to output WAV file
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            logger.info(f"Converting {input_path} to WAV format")
            
            # Load audio with pydub (handles many formats)
            audio = AudioSegment.from_file(input_path)
            
            # Convert to mono and standard sample rate for better processing
            audio = audio.set_channels(1).set_frame_rate(16000)
            
            # Export as WAV
            audio.export(output_path, format="wav")
            
            logger.info(f"Conversion successful: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Audio conversion failed: {e}")
            return False
    
    def transcribe_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio using Whisper
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with transcription results
        """
        self._load_models()
        
        try:
            logger.info(f"Transcribing audio: {audio_path}")
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                audio_path,
                verbose=False,
                word_timestamps=True
            )
            
            logger.info(f"Transcription completed. Duration: {result.get('duration', 0):.1f}s")
            
            return {
                'text': result['text'],
                'language': result.get('language', 'unknown'),
                'segments': result.get('segments', []),
                'duration': result.get('duration', 0)
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {
                'text': '',
                'language': 'unknown',
                'segments': [],
                'duration': 0,
                'error': str(e)
            }
    
    def diarize_audio(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Perform speaker diarization on audio
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of speaker segments with timing
        """
        if self.diarization_pipeline is None:
            logger.warning("Diarization pipeline not available")
            return []
        
        try:
            logger.info(f"Performing speaker diarization: {audio_path}")
            
            # Run diarization
            diarization = self.diarization_pipeline(audio_path)
            
            # Convert to list of segments
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    'speaker': speaker,
                    'start': turn.start,
                    'end': turn.end,
                    'duration': turn.end - turn.start
                })
            
            logger.info(f"Diarization completed. Found {len(set(s['speaker'] for s in segments))} speakers")
            
            return segments
            
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return []
    
    def combine_transcription_and_diarization(self, 
                                            transcription: Dict[str, Any], 
                                            diarization: List[Dict[str, Any]]) -> str:
        """
        Combine Whisper transcription with speaker diarization
        
        Args:
            transcription: Whisper transcription results
            diarization: Speaker diarization segments
            
        Returns:
            Formatted transcript with speaker labels
        """
        if not diarization:
            # No diarization available, return plain transcript
            return transcription.get('text', '')
        
        # Get transcription segments with timestamps
        transcript_segments = transcription.get('segments', [])
        if not transcript_segments:
            return transcription.get('text', '')
        
        # Combine transcription and diarization
        combined_segments = []
        
        for segment in transcript_segments:
            segment_start = segment.get('start', 0)
            segment_end = segment.get('end', 0)
            segment_text = segment.get('text', '').strip()
            
            if not segment_text:
                continue
            
            # Find overlapping speaker
            speaker = self._find_speaker_for_segment(segment_start, segment_end, diarization)
            
            combined_segments.append({
                'start': segment_start,
                'end': segment_end,
                'speaker': speaker,
                'text': segment_text
            })
        
        # Format as readable transcript
        return self._format_transcript(combined_segments)
    
    def _find_speaker_for_segment(self, start: float, end: float, diarization: List[Dict[str, Any]]) -> str:
        """
        Find the speaker for a given time segment
        
        Args:
            start: Segment start time
            end: Segment end time
            diarization: Speaker diarization data
            
        Returns:
            Speaker label
        """
        segment_mid = (start + end) / 2
        
        # Find speaker with maximum overlap
        best_speaker = "SPEAKER_UNKNOWN"
        max_overlap = 0
        
        for diar_segment in diarization:
            diar_start = diar_segment['start']
            diar_end = diar_segment['end']
            
            # Calculate overlap
            overlap_start = max(start, diar_start)
            overlap_end = min(end, diar_end)
            overlap = max(0, overlap_end - overlap_start)
            
            if overlap > max_overlap:
                max_overlap = overlap
                best_speaker = diar_segment['speaker']
        
        return best_speaker
    
    def _format_transcript(self, segments: List[Dict[str, Any]]) -> str:
        """
        Format combined segments into readable transcript
        
        Args:
            segments: List of segments with speaker and text
            
        Returns:
            Formatted transcript string
        """
        if not segments:
            return ""
        
        # Group consecutive segments by speaker
        grouped_segments = []
        current_speaker = None
        current_text = []
        
        for segment in segments:
            speaker = segment['speaker']
            text = segment['text']
            
            if speaker != current_speaker:
                # New speaker, save previous and start new
                if current_speaker and current_text:
                    grouped_segments.append({
                        'speaker': current_speaker,
                        'text': ' '.join(current_text).strip()
                    })
                
                current_speaker = speaker
                current_text = [text]
            else:
                # Same speaker, append text
                current_text.append(text)
        
        # Add final segment
        if current_speaker and current_text:
            grouped_segments.append({
                'speaker': current_speaker,
                'text': ' '.join(current_text).strip()
            })
        
        # Format as transcript
        lines = []
        for segment in grouped_segments:
            speaker = segment['speaker']
            text = segment['text']
            
            # Clean up speaker name
            speaker_name = speaker.replace('SPEAKER_', 'Speaker ')
            
            lines.append(f"{speaker_name}: {text}")
        
        return '\n\n'.join(lines)
    
    async def transcribe_from_url(self, audio_url: str, episode_number: int = 0) -> Dict[str, Any]:
        """
        Complete transcription workflow from audio URL
        
        Args:
            audio_url: URL to audio file
            episode_number: Episode number for logging
            
        Returns:
            Dictionary with transcription results
        """
        logger.info(f"Starting transcription for episode {episode_number}")
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Determine file extension from URL
            parsed_url = urlparse(audio_url)
            original_ext = Path(parsed_url.path).suffix or '.mp3'
            
            # Download audio
            download_path = temp_path / f"episode_{episode_number}{original_ext}"
            if not await self.download_audio(audio_url, str(download_path)):
                return {
                    'success': False,
                    'error': 'Failed to download audio file',
                    'transcript': '',
                    'metadata': {}
                }
            
            # Convert to WAV if needed
            wav_path = temp_path / f"episode_{episode_number}.wav"
            if original_ext.lower() != '.wav':
                if not self.convert_to_wav(str(download_path), str(wav_path)):
                    return {
                        'success': False,
                        'error': 'Failed to convert audio file',
                        'transcript': '',
                        'metadata': {}
                    }
            else:
                wav_path = download_path
            
            # Transcribe audio
            transcription = self.transcribe_audio(str(wav_path))
            
            if transcription.get('error'):
                return {
                    'success': False,
                    'error': f"Transcription failed: {transcription['error']}",
                    'transcript': '',
                    'metadata': {}
                }
            
            # Perform speaker diarization
            diarization = self.diarize_audio(str(wav_path))
            
            # Combine results
            final_transcript = self.combine_transcription_and_diarization(transcription, diarization)
            
            # Prepare metadata
            metadata = {
                'whisper_model': self.whisper_model_name,
                'language': transcription.get('language', 'unknown'),
                'duration': transcription.get('duration', 0),
                'speakers_detected': len(set(d['speaker'] for d in diarization)) if diarization else 0,
                'segments_count': len(transcription.get('segments', [])),
                'diarization_available': len(diarization) > 0,
                'audio_url': audio_url
            }
            
            logger.info(f"Transcription completed for episode {episode_number}. "
                       f"Duration: {metadata['duration']:.1f}s, "
                       f"Speakers: {metadata['speakers_detected']}, "
                       f"Length: {len(final_transcript)} chars")
            
            return {
                'success': True,
                'transcript': final_transcript,
                'metadata': metadata,
                'raw_transcription': transcription,
                'raw_diarization': diarization
            }


# Example usage
async def main():
    """Example usage of AudioTranscriber"""
    transcriber = AudioTranscriber(whisper_model="base")
    
    # Example audio URL (replace with actual URL)
    audio_url = "https://example.com/podcast-episode.mp3"
    
    result = await transcriber.transcribe_from_url(audio_url, episode_number=1)
    
    if result['success']:
        print("Transcription successful!")
        print(f"Transcript length: {len(result['transcript'])} characters")
        print(f"Speakers detected: {result['metadata']['speakers_detected']}")
        print(f"Language: {result['metadata']['language']}")
        print(f"Duration: {result['metadata']['duration']:.1f} seconds")
        print("\nTranscript preview:")
        print(result['transcript'][:500] + "..." if len(result['transcript']) > 500 else result['transcript'])
    else:
        print(f"Transcription failed: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())