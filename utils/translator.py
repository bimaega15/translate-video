import time
import re
import requests
import json

class Translator:
    def __init__(self):
        # Use MyMemory API for translation
        self.translation_api_available = True
        print("Using MyMemory translation API")

    def _translate_with_mymemory(self, text, source_lang="id", target_lang="en"):
        """Use MyMemory translation API"""
        try:
            text = text.strip()
            if not text or len(text) < 3:
                return text

            url = "https://api.mymemory.translated.net/get"
            params = {
                'q': text,
                'langpair': f'{source_lang}|{target_lang}'
            }

            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['responseStatus'] == 200:
                    return data['responseData']['translatedText']

            return f"[Translation: {text}]"
        except Exception as e:
            print(f"Translation error: {e}")
            return f"[Translation: {text}]"

    def translate_segments(self, segments):
        """Translate segments to English"""
        translated_segments = []

        for segment in segments:
            try:
                # Skip if already in English
                if segment.get('language') == 'en':
                    translated_segments.append({
                        'start': segment['start'],
                        'end': segment['end'],
                        'text': segment['text'],
                        'original_text': segment['text']
                    })
                    continue

                # Clean text for better translation
                text = self._clean_text(segment['text'])

                if not text.strip():
                    continue

                # Translate to English using MyMemory API
                source_lang = segment.get('language', 'id')
                if source_lang == 'en':
                    # Already English
                    translated_text = text
                else:
                    # Translate from source language to English
                    translated_text = self._translate_with_mymemory(text, source_lang, 'en')

                translated_segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': translated_text,
                    'original_text': segment['text']
                })

                # Small delay to avoid rate limiting
                time.sleep(0.1)

            except Exception as e:
                print(f"Translation error for segment: {str(e)}")
                # Use original text if translation fails
                translated_segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'],
                    'original_text': segment['text']
                })

        return translated_segments

    def _clean_text(self, text):
        """Clean text for better translation"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove common speech artifacts
        text = re.sub(r'\[.*?\]', '', text)  # Remove bracketed content
        text = re.sub(r'\(.*?\)', '', text)  # Remove parenthetical content

        # Remove repeated punctuation
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)

        return text.strip()

    def translate_single_text(self, text, target_language='en', source_language='auto'):
        """Translate a single text string"""
        try:
            if source_language == 'auto':
                result = self.google_translator.translate(text, dest=target_language)
            else:
                result = self.google_translator.translate(text, src=source_language, dest=target_language)

            return result.text
        except Exception as e:
            raise Exception(f"Translation error: {str(e)}")

    def detect_language(self, text):
        """Detect the language of given text"""
        try:
            detection = self.google_translator.detect(text)
            return detection.lang
        except Exception as e:
            return 'unknown'