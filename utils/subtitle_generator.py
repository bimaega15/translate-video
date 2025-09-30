import os
from datetime import timedelta

class SubtitleGenerator:
    def __init__(self):
        self.output_dir = 'static/processed'
        os.makedirs(self.output_dir, exist_ok=True)

    def create_srt(self, translated_segments, task_id):
        """Create SRT subtitle file from translated segments"""
        srt_filename = f"subtitles_{task_id}.srt"
        srt_path = os.path.join(self.output_dir, srt_filename)

        with open(srt_path, 'w', encoding='utf-8') as srt_file:
            for i, segment in enumerate(translated_segments, 1):
                # Format timestamps
                start_time = self._seconds_to_srt_time(segment['start'])
                end_time = self._seconds_to_srt_time(segment['end'])

                # Write SRT entry
                srt_file.write(f"{i}\n")
                srt_file.write(f"{start_time} --> {end_time}\n")
                srt_file.write(f"{segment['text']}\n\n")

        return srt_path

    def create_vtt(self, translated_segments, task_id):
        """Create VTT subtitle file from translated segments"""
        vtt_filename = f"subtitles_{task_id}.vtt"
        vtt_path = os.path.join(self.output_dir, vtt_filename)

        with open(vtt_path, 'w', encoding='utf-8') as vtt_file:
            vtt_file.write("WEBVTT\n\n")

            for segment in translated_segments:
                # Format timestamps for VTT
                start_time = self._seconds_to_vtt_time(segment['start'])
                end_time = self._seconds_to_vtt_time(segment['end'])

                # Write VTT entry
                vtt_file.write(f"{start_time} --> {end_time}\n")
                vtt_file.write(f"{segment['text']}\n\n")

        return vtt_path

    def _seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds % 1) * 1000)

        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d},{milliseconds:03d}"

    def _seconds_to_vtt_time(self, seconds):
        """Convert seconds to VTT time format (HH:MM:SS.mmm)"""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = int((seconds % 1) * 1000)

        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}.{milliseconds:03d}"

    def merge_short_segments(self, segments, min_duration=1.0, max_chars=80):
        """Merge short segments for better readability"""
        merged_segments = []
        current_segment = None

        for segment in segments:
            duration = segment['end'] - segment['start']

            if current_segment is None:
                current_segment = segment.copy()
            elif (duration < min_duration and
                  len(current_segment['text'] + ' ' + segment['text']) <= max_chars and
                  segment['start'] - current_segment['end'] < 2.0):
                # Merge with current segment
                current_segment['text'] += ' ' + segment['text']
                current_segment['end'] = segment['end']
            else:
                # Save current segment and start new one
                merged_segments.append(current_segment)
                current_segment = segment.copy()

        if current_segment:
            merged_segments.append(current_segment)

        return merged_segments

    def split_long_segments(self, segments, max_chars=80, max_duration=5.0):
        """Split long segments for better readability"""
        split_segments = []

        for segment in segments:
            text = segment['text']
            duration = segment['end'] - segment['start']

            if len(text) <= max_chars and duration <= max_duration:
                split_segments.append(segment)
                continue

            # Split long text
            words = text.split()
            current_text = ""
            current_start = segment['start']
            word_duration = duration / len(words)

            for i, word in enumerate(words):
                if len(current_text + ' ' + word) <= max_chars:
                    current_text += (' ' + word) if current_text else word
                else:
                    if current_text:
                        current_end = current_start + (len(current_text.split()) * word_duration)
                        split_segments.append({
                            'start': current_start,
                            'end': current_end,
                            'text': current_text,
                            'original_text': segment.get('original_text', text)
                        })
                        current_start = current_end
                        current_text = word

            if current_text:
                split_segments.append({
                    'start': current_start,
                    'end': segment['end'],
                    'text': current_text,
                    'original_text': segment.get('original_text', text)
                })

        return split_segments