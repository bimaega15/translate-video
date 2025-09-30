import os
import moviepy.editor as mp
from moviepy.video.tools.subtitles import SubtitlesClip
import tempfile

class VideoProcessor:
    def __init__(self):
        # Use current working directory instead of system temp
        self.temp_dir = os.path.join(os.getcwd(), 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)

    def extract_audio(self, video_path):
        """Extract audio from video file and save as WAV"""
        try:
            print(f"Loading video: {video_path}")
            video = mp.VideoFileClip(video_path)

            # Create temporary audio file
            audio_filename = f"audio_{os.path.basename(video_path).split('.')[0]}.wav"
            audio_path = os.path.join(self.temp_dir, audio_filename)

            print(f"Extracting audio to: {audio_path}")

            # Extract and save audio
            audio = video.audio
            audio.write_audiofile(audio_path, verbose=False, logger=None)

            # Close video and audio clips
            audio.close()
            video.close()

            return audio_path
        except Exception as e:
            raise Exception(f"Error extracting audio: {str(e)}")

    def add_subtitles(self, video_path, srt_path, task_id):
        """Add subtitles to video and save the result - using alternative method without ImageMagick"""
        try:
            print(f"Adding subtitles to video: {video_path}")
            print(f"Using subtitle file: {srt_path}")

            # For now, let's just copy the original video and provide the SRT file separately
            # This avoids the ImageMagick dependency while still providing subtitles

            # Output paths
            output_filename = f"translated_{task_id}.mp4"
            output_path = os.path.join('static/processed', output_filename)

            srt_output_filename = f"translated_{task_id}.srt"
            srt_output_path = os.path.join('static/processed', srt_output_filename)

            # Copy original video
            import shutil
            shutil.copy2(video_path, output_path)

            # Copy subtitle file to output location
            shutil.copy2(srt_path, srt_output_path)

            print(f"Video copied to: {output_path}")
            print(f"Subtitle file copied to: {srt_output_path}")
            print("Note: Subtitles are provided as separate SRT file. Use VLC Player or any video player that supports SRT files.")

            return output_path
        except Exception as e:
            raise Exception(f"Error processing video: {str(e)}")

    def get_video_info(self, video_path):
        """Get basic video information"""
        try:
            video = mp.VideoFileClip(video_path)
            info = {
                'duration': video.duration,
                'fps': video.fps,
                'size': video.size
            }
            video.close()
            return info
        except Exception as e:
            raise Exception(f"Error getting video info: {str(e)}")