import whisper
import os
import torch
import numpy as np

class Transcriber:
    def __init__(self):
        # Use GPU if available, otherwise CPU
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")

        # Load Whisper model (base model for good balance of speed and accuracy)
        print("Loading Whisper model...")
        self.model = None

    def _ensure_model_loaded(self):
        """Lazy load the model to avoid initialization issues"""
        if self.model is None:
            print("Loading Whisper base model for better accuracy and timing...")
            self.model = whisper.load_model("base", device=self.device)
            print("Whisper model loaded successfully")

    def _load_audio_with_soundfile(self, audio_path):
        """Load audio using soundfile - no FFmpeg dependency required"""
        try:
            import soundfile as sf
            import librosa
            print(f"Loading audio with soundfile: {audio_path}")

            # Validate file exists and has content
            if not os.path.exists(audio_path):
                raise Exception(f"Audio file does not exist: {audio_path}")

            file_size = os.path.getsize(audio_path)
            if file_size == 0:
                raise Exception(f"Audio file is empty: {audio_path}")

            print(f"Audio file size: {file_size} bytes")

            try:
                # Load audio with soundfile
                audio_data, sample_rate = sf.read(audio_path, dtype='float32')
                print(f"Audio loaded: sample_rate={sample_rate}Hz, channels={audio_data.ndim}, shape={audio_data.shape}")

                # Convert to mono if stereo
                if audio_data.ndim > 1:
                    print("Converting stereo to mono")
                    audio_data = np.mean(audio_data, axis=1)

                # Resample to 16kHz for Whisper if needed
                if sample_rate != 16000:
                    print(f"Resampling from {sample_rate}Hz to 16000Hz")
                    audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)

                # Ensure audio is in proper range [-1, 1]
                if audio_data.max() > 1.0 or audio_data.min() < -1.0:
                    print("Normalizing audio to [-1, 1] range")
                    audio_data = audio_data / np.max(np.abs(audio_data))

                duration = len(audio_data) / 16000
                print(f"Audio processed successfully: duration={duration:.2f}s, shape={audio_data.shape}, range=[{audio_data.min():.3f}, {audio_data.max():.3f}]")

                if duration < 0.1:
                    raise Exception(f"Audio too short: {duration:.2f}s")

                return audio_data

            except Exception as sf_error:
                print(f"Soundfile failed: {sf_error}")
                # Fallback to librosa
                try:
                    print("Trying with librosa as fallback...")
                    audio_data, sample_rate = librosa.load(audio_path, sr=16000, mono=True)
                    duration = len(audio_data) / 16000
                    print(f"Librosa fallback successful: duration={duration:.2f}s, shape={audio_data.shape}")
                    return audio_data
                except Exception as librosa_error:
                    raise Exception(f"Both soundfile and librosa failed: {librosa_error}")

        except Exception as e:
            print(f"Error loading audio: {e}")
            import traceback
            traceback.print_exc()
            return None

    def transcribe(self, audio_path, source_language="auto"):
        """Transcribe audio file to text with word-level timestamps for better sync"""
        try:
            # Ensure model is loaded
            self._ensure_model_loaded()

            if not os.path.exists(audio_path):
                raise Exception(f"Audio file not found: {audio_path}")

            print(f"Transcribing audio file: {audio_path}")
            print(f"Source language: {source_language}")

            # Set language parameter
            language_param = None if source_language == "auto" else source_language

            # Check if file exists and is accessible
            if not os.path.isfile(audio_path):
                raise Exception(f"Audio file does not exist: {audio_path}")

            # Load audio manually to avoid FFmpeg dependency issues
            print("Loading audio with soundfile for Whisper compatibility...")
            audio_data = self._load_audio_with_soundfile(audio_path)
            if audio_data is None:
                raise Exception("Could not load audio file")

            print("Starting transcription with loaded audio data...")

            try:
                # Transcribe with word timestamps using audio array
                result = self.model.transcribe(
                    audio_data,
                    language=language_param,
                    word_timestamps=True,
                    temperature=0.0,
                    best_of=1,
                    beam_size=1,
                    patience=1.0,
                    length_penalty=1.0,
                    suppress_tokens="-1",
                    initial_prompt=None,
                    condition_on_previous_text=True,
                    fp16=torch.cuda.is_available(),
                    compression_ratio_threshold=2.4,
                    logprob_threshold=-1.0,
                    no_speech_threshold=0.6
                )
                print("Transcription with word timestamps successful")
            except Exception as transcribe_error:
                print(f"Error during word-level transcription: {transcribe_error}")
                # Fallback to basic transcription without word timestamps
                print("Falling back to basic transcription without word timestamps...")
                try:
                    result = self.model.transcribe(
                        audio_data,
                        language=language_param,
                        word_timestamps=False
                    )
                    print("Basic transcription successful")
                except Exception as basic_error:
                    print(f"Error during basic transcription: {basic_error}")
                    raise Exception(f"Both word-level and basic transcription failed: {basic_error}")

            segments = []

            # Process each segment from Whisper result
            for segment in result['segments']:
                # If word-level timestamps are available, use them for better accuracy
                if 'words' in segment and segment['words']:
                    # Group words into phrases for better readability
                    current_phrase = []
                    phrase_start = None

                    for word_info in segment['words']:
                        word_text = word_info.get('word', '').strip()
                        word_start = word_info.get('start', 0)
                        word_end = word_info.get('end', 0)

                        if not word_text:
                            continue

                        if phrase_start is None:
                            phrase_start = word_start

                        current_phrase.append(word_text)

                        # End phrase on punctuation or when reaching optimal length
                        phrase_text = ' '.join(current_phrase)
                        should_end_phrase = (
                            word_text.endswith(('.', '!', '?', ',', ';')) or
                            len(phrase_text) > 50 or
                            len(current_phrase) >= 8
                        )

                        if should_end_phrase and current_phrase:
                            segments.append({
                                "start": phrase_start,
                                "end": word_end,
                                "text": phrase_text.strip(),
                                "language": result.get('language', 'unknown'),
                                "confidence": segment.get('avg_logprob', 0.0)
                            })

                            current_phrase = []
                            phrase_start = None

                    # Add remaining words as final phrase
                    if current_phrase and phrase_start is not None:
                        final_phrase = ' '.join(current_phrase)
                        # Use the last word's end time or segment end time
                        final_end = segment['words'][-1].get('end', segment['end'])

                        segments.append({
                            "start": phrase_start,
                            "end": final_end,
                            "text": final_phrase.strip(),
                            "language": result.get('language', 'unknown'),
                            "confidence": segment.get('avg_logprob', 0.0)
                        })
                else:
                    # Fallback to segment-level timestamps if word-level not available
                    segments.append({
                        "start": segment['start'],
                        "end": segment['end'],
                        "text": segment['text'].strip(),
                        "language": result.get('language', 'unknown'),
                        "confidence": segment.get('avg_logprob', 0.0)
                    })

            print(f"Transcription completed. Found {len(segments)} segments with precise timing")

            # Sort segments by start time to ensure proper order
            segments.sort(key=lambda x: x['start'])

            return segments

        except Exception as e:
            raise Exception(f"Error transcribing audio: {str(e)}")

    def get_supported_languages(self):
        """Get list of supported languages"""
        return {
            "auto": "Auto-detect",
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "ru": "Russian",
            "ja": "Japanese",
            "ko": "Korean",
            "zh": "Chinese",
            "ar": "Arabic",
            "hi": "Hindi",
            "id": "Indonesian",
            "ms": "Malay",
            "th": "Thai",
            "vi": "Vietnamese",
            "tr": "Turkish",
            "pl": "Polish",
            "nl": "Dutch",
            "sv": "Swedish",
            "da": "Danish",
            "no": "Norwegian",
            "fi": "Finnish"
        }