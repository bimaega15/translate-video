#!/usr/bin/env python3
"""
Manual subtitle creation script - Generate subtitles from extracted audio
"""

import os
import numpy as np
import subprocess
import whisper
from utils.translator import Translator
from utils.subtitle_generator import SubtitleGenerator

def load_audio_with_librosa(audio_path):
    """Load audio using librosa as alternative to FFmpeg"""
    try:
        import librosa
        # Load audio with librosa (alternative to FFmpeg)
        audio, sr = librosa.load(audio_path, sr=16000, mono=True)
        return audio
    except ImportError:
        print("librosa not available, trying pydub...")
        return load_audio_with_pydub(audio_path)

def load_audio_with_pydub(audio_path):
    """Load audio using pydub as alternative"""
    try:
        from pydub import AudioSegment
        import numpy as np

        # Load with pydub
        audio_segment = AudioSegment.from_wav(audio_path)

        # Convert to mono if stereo
        if audio_segment.channels > 1:
            audio_segment = audio_segment.set_channels(1)

        # Convert to 16kHz
        audio_segment = audio_segment.set_frame_rate(16000)

        # Convert to numpy array
        audio_data = np.array(audio_segment.get_array_of_samples())

        # Normalize to [-1, 1] range
        audio_data = audio_data.astype(np.float32) / 32768.0

        return audio_data
    except Exception as e:
        print(f"Error loading audio with pydub: {e}")
        return None

def transcribe_audio_manual(audio_path, language="id"):
    """Transcribe audio without FFmpeg dependency"""
    print(f"Loading audio manually: {audio_path}")

    # Try to load audio with alternative methods
    audio_data = load_audio_with_pydub(audio_path)

    if audio_data is None:
        raise Exception("Could not load audio file")

    print("Audio loaded successfully")
    print(f"Audio shape: {audio_data.shape}")
    print(f"Audio duration: {len(audio_data) / 16000:.2f} seconds")

    # Load Whisper model
    print("Loading Whisper model...")
    model = whisper.load_model("tiny")  # Use tiny model for faster processing

    # Create a custom transcribe using the loaded audio
    print("Transcribing with Whisper...")

    # Pad or trim to 30 seconds chunks for better processing
    chunk_size = 16000 * 30  # 30 seconds at 16kHz
    segments = []

    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i+chunk_size]

        # Ensure chunk is not empty
        if len(chunk) == 0:
            continue

        # Pad chunk to chunk_size if needed
        if len(chunk) < chunk_size:
            chunk = np.pad(chunk, (0, chunk_size - len(chunk)))

        print(f"Processing chunk {i//chunk_size + 1}...")

        # Transcribe chunk
        try:
            # Use Whisper's internal mel spectrogram
            mel = whisper.log_mel_spectrogram(chunk, model.dims.n_mels)

            # Detect language
            _, probs = model.detect_language(mel)
            detected_lang = max(probs, key=probs.get)
            print(f"Detected language: {detected_lang}")

            # Decode
            options = whisper.DecodingOptions(
                language=language,
                without_timestamps=False,
                task="transcribe"
            )
            result = whisper.decode(model, mel, options)

            if result.text.strip():
                start_time = i / 16000
                end_time = min((i + chunk_size) / 16000, len(audio_data) / 16000)

                segments.append({
                    'start': start_time,
                    'end': end_time,
                    'text': result.text.strip(),
                    'language': detected_lang
                })
                print(f"  Transcribed: {result.text.strip()[:50]}...")
        except Exception as e:
            print(f"Error processing chunk: {e}")
            continue

    return segments

def main():
    audio_file = "temp/audio_bandicam 2025-09-29 09-33-08-967.wav"

    if not os.path.exists(audio_file):
        print(f"Audio file not found: {audio_file}")
        print("Please run the video processor first to extract audio.")
        return

    print("=" * 60)
    print("MANUAL SUBTITLE GENERATION")
    print(f"Audio file: {audio_file}")
    print("=" * 60)

    try:
        # Step 1: Transcribe audio
        print("Step 1: Transcribing audio...")
        segments = transcribe_audio_manual(audio_file, language="id")
        print(f"Found {len(segments)} segments")

        if not segments:
            print("No speech found in audio")
            return

        # Step 2: Translate to English
        print("Step 2: Translating to English...")
        translator = Translator()
        translated_segments = translator.translate_segments(segments)
        print(f"Translated {len(translated_segments)} segments")

        # Step 3: Generate subtitle file
        print("Step 3: Generating subtitle file...")
        subtitle_generator = SubtitleGenerator()
        srt_path = subtitle_generator.create_srt(translated_segments, "manual")

        print("=" * 60)
        print(f"SUCCESS! Subtitle file created: {srt_path}")
        print("=" * 60)

        # Show sample subtitles
        print("Sample subtitles:")
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content[:500] + "..." if len(content) > 500 else content)

        print("\nTo add these subtitles to your video:")
        print("1. Use any video editor (like VLC, DaVinci Resolve, etc.)")
        print("2. Import both your video and the .srt file")
        print("3. The subtitles will appear automatically")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()