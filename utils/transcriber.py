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
            print("Loading Whisper tiny model for faster processing...")
            self.model = whisper.load_model("tiny", device=self.device)
            print("Whisper model loaded successfully")

    def _load_audio_with_pydub(self, audio_path):
        """Load audio using pydub as alternative to FFmpeg"""
        try:
            from pydub import AudioSegment
            print(f"Loading audio with pydub: {audio_path}")

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

            print(f"Audio loaded: duration={len(audio_data)/16000:.2f}s, shape={audio_data.shape}")
            return audio_data
        except Exception as e:
            print(f"Error loading audio with pydub: {e}")
            return None

    def transcribe(self, audio_path, source_language="auto"):
        """Transcribe audio file to text with timestamps"""
        try:
            # Ensure model is loaded
            self._ensure_model_loaded()

            if not os.path.exists(audio_path):
                raise Exception(f"Audio file not found: {audio_path}")

            print(f"Transcribing audio file: {audio_path}")
            print(f"Source language: {source_language}")

            # Load audio manually to avoid FFmpeg dependency
            audio_data = self._load_audio_with_pydub(audio_path)
            if audio_data is None:
                raise Exception("Could not load audio file")

            # Set language parameter
            language_param = None if source_language == "auto" else source_language

            # Process audio in chunks for better performance
            print("Starting transcription with manual audio loading...")
            segments = []
            chunk_size = 16000 * 30  # 30 seconds at 16kHz

            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]

                if len(chunk) == 0:
                    continue

                # Pad chunk if needed
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)))

                print(f"Processing chunk {i//chunk_size + 1}...")

                try:
                    # Use Whisper's internal mel spectrogram
                    mel = whisper.log_mel_spectrogram(chunk, self.model.dims.n_mels)

                    # Detect language if auto
                    if language_param is None:
                        _, probs = self.model.detect_language(mel)
                        detected_lang = max(probs, key=probs.get)
                        print(f"Detected language: {detected_lang}")
                    else:
                        detected_lang = language_param

                    # Decode
                    options = whisper.DecodingOptions(
                        language=detected_lang,
                        without_timestamps=False,
                        task="transcribe"
                    )
                    result_chunk = whisper.decode(self.model, mel, options)

                    if result_chunk.text.strip():
                        start_time = i / 16000
                        end_time = min((i + chunk_size) / 16000, len(audio_data) / 16000)

                        segments.append({
                            "start": start_time,
                            "end": end_time,
                            "text": result_chunk.text.strip(),
                            "language": detected_lang
                        })
                        print(f"  Transcribed: {result_chunk.text.strip()[:50]}...")

                except Exception as chunk_error:
                    print(f"Error processing chunk: {chunk_error}")
                    continue

            print(f"Transcription completed. Found {len(segments)} segments")
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