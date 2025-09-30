#!/usr/bin/env python3
"""
Direct video processing script - Process your video with real English subtitles
"""

import os
import sys
import time
from utils.video_processor import VideoProcessor
from utils.transcriber import Transcriber
from utils.translator import Translator
from utils.subtitle_generator import SubtitleGenerator

def process_video_with_subtitles(video_path, output_path):
    """Process video and add English subtitles"""

    print(f"Processing video: {os.path.basename(video_path)}")
    print("=" * 60)

    try:
        # Initialize processors
        print("Initializing processors...")
        video_processor = VideoProcessor()
        transcriber = Transcriber()
        translator = Translator()
        subtitle_generator = SubtitleGenerator()

        # Step 1: Extract audio
        print("Step 1/5: Extracting audio from video...")
        audio_path = video_processor.extract_audio(video_path)
        print(f"Audio extracted to: {audio_path}")

        # Step 2: Transcribe speech
        print("Step 2/5: Transcribing speech (this may take a few minutes)...")
        print("   Using OpenAI Whisper for Indonesian speech recognition...")
        transcription = transcriber.transcribe(audio_path, source_language="id")
        print(f"Found {len(transcription)} speech segments")

        # Show sample transcription
        if transcription:
            print(f"   Sample: '{transcription[0]['text'][:50]}...'")

        # Step 3: Translate to English
        print("Step 3/5: Translating to English...")
        translated_segments = translator.translate_segments(transcription)
        print(f"Translated {len(translated_segments)} segments")

        # Show sample translation
        if translated_segments:
            print(f"   Sample translation: '{translated_segments[0]['text'][:50]}...'")

        # Step 4: Generate subtitle file
        print("Step 4/5: Generating subtitle file...")
        srt_path = subtitle_generator.create_srt(translated_segments, "final")
        print(f"Subtitle file created: {srt_path}")

        # Step 5: Add subtitles to video
        print("Step 5/5: Adding subtitles to video...")
        final_output = video_processor.add_subtitles(video_path, srt_path, "final")

        # Move to desired output location
        if output_path != final_output:
            import shutil
            shutil.move(final_output, output_path)

        # Cleanup temporary files
        if os.path.exists(audio_path):
            os.remove(audio_path)

        print("=" * 60)
        print(f"SUCCESS! Video with English subtitles saved to:")
        print(f"   {output_path}")
        print("=" * 60)

        return output_path

    except Exception as e:
        print(f"Error processing video: {str(e)}")
        return None

def main():
    # Your video file
    input_video = "video/bandicam 2025-09-29 09-33-08-967.mp4"
    output_video = "video/bandicam_with_english_subtitles.mp4"

    if not os.path.exists(input_video):
        print(f"Video file not found: {input_video}")
        return

    print("Starting English Subtitle Generation")
    print(f"Input:  {input_video}")
    print(f"Output: {output_video}")
    print()

    start_time = time.time()
    result = process_video_with_subtitles(input_video, output_video)
    end_time = time.time()

    if result:
        duration = int(end_time - start_time)
        print(f"Total processing time: {duration//60}m {duration%60}s")
        print()
        print("Your video now has English subtitles for every spoken word!")
        print("   You can play it in any video player that supports embedded subtitles.")
    else:
        print("Processing failed. Check the error messages above.")

if __name__ == "__main__":
    main()