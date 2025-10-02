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

    def merge_short_segments(self, segments, min_duration=1.2, max_chars=60):
        """Merge short segments for better readability with improved timing for better sync"""
        merged_segments = []
        current_segment = None

        for segment in segments:
            duration = segment['end'] - segment['start']

            if current_segment is None:
                current_segment = segment.copy()
            elif (duration < min_duration and
                  len(current_segment['text'] + ' ' + segment['text']) <= max_chars and
                  segment['start'] - current_segment['end'] < 0.5):  # Smaller gap for better sync
                # Merge with current segment
                current_segment['text'] += ' ' + segment['text']
                current_segment['end'] = segment['end']

                # More conservative timing based on actual speech patterns
                word_count = len(current_segment['text'].split())
                reading_speed = 2.5  # Slower reading speed for better sync
                optimal_duration = max(min_duration, word_count / reading_speed)

                # Keep original timing but ensure minimum duration
                if current_segment['end'] - current_segment['start'] < optimal_duration:
                    # Extend end time slightly but respect original audio timing
                    extension = min(0.3, optimal_duration - (current_segment['end'] - current_segment['start']))
                    current_segment['end'] += extension
            else:
                # Save current segment and start new one
                merged_segments.append(current_segment)
                current_segment = segment.copy()

        if current_segment:
            merged_segments.append(current_segment)

        return merged_segments

    def split_long_segments(self, segments, max_chars=60, max_duration=4.0):
        """Split long segments for better readability with preserved original timing"""
        split_segments = []

        for segment in segments:
            text = segment['text']
            duration = segment['end'] - segment['start']

            if len(text) <= max_chars and duration <= max_duration:
                # Keep original timing for segments that don't need splitting
                split_segments.append(segment.copy())
                continue

            # Split long text while preserving original timing proportions
            words = text.split()
            current_text = ""
            word_positions = []

            # Calculate word positions within the original segment timing
            for i, word in enumerate(words):
                word_start_ratio = i / len(words)
                word_end_ratio = (i + 1) / len(words)

                word_start_time = segment['start'] + (duration * word_start_ratio)
                word_end_time = segment['start'] + (duration * word_end_ratio)

                word_positions.append({
                    'word': word,
                    'start': word_start_time,
                    'end': word_end_time
                })

            # Group words into appropriately sized segments
            current_words = []
            current_start_time = None

            for word_info in word_positions:
                test_text = current_text + (' ' + word_info['word'] if current_text else word_info['word'])

                if len(test_text) <= max_chars:
                    current_text = test_text
                    current_words.append(word_info)
                    if current_start_time is None:
                        current_start_time = word_info['start']
                else:
                    if current_words:
                        # Create segment with original timing
                        current_end_time = current_words[-1]['end']

                        split_segments.append({
                            'start': current_start_time,
                            'end': current_end_time,
                            'text': current_text.strip(),
                            'original_text': segment.get('original_text', text),
                            'confidence': segment.get('confidence', 0.0)
                        })

                        # Start new segment
                        current_text = word_info['word']
                        current_words = [word_info]
                        current_start_time = word_info['start']

            # Add final segment if any words remain
            if current_words:
                current_end_time = current_words[-1]['end']

                split_segments.append({
                    'start': current_start_time,
                    'end': current_end_time,
                    'text': current_text.strip(),
                    'original_text': segment.get('original_text', text),
                    'confidence': segment.get('confidence', 0.0)
                })

        # Minimal timing optimization to prevent overlaps only
        return self._preserve_original_timing(split_segments)

    def _preserve_original_timing(self, segments):
        """Preserve original timing while preventing overlaps minimally"""
        if not segments:
            return segments

        optimized = []

        for i, segment in enumerate(segments):
            current_segment = segment.copy()

            # Only fix overlaps, preserve original timing as much as possible
            if optimized and current_segment['start'] < optimized[-1]['end']:
                # Minimal adjustment - just prevent overlap
                gap = 0.02  # Very small gap (20ms)
                current_segment['start'] = optimized[-1]['end'] + gap

                # Maintain original duration if possible
                original_duration = segment['end'] - segment['start']
                current_segment['end'] = current_segment['start'] + original_duration

            # Prevent overlap with next segment with minimal adjustment
            if i < len(segments) - 1:
                next_start = segments[i + 1]['start']
                if current_segment['end'] > next_start - 0.02:
                    current_segment['end'] = next_start - 0.02

            optimized.append(current_segment)

        return optimized

    def _optimize_single_segment_timing(self, segment):
        """Minimal optimization - preserve original timing"""
        return segment.copy()

    def _optimize_segment_timing(self, segments):
        """Legacy method - use _preserve_original_timing instead"""
        return self._preserve_original_timing(segments)