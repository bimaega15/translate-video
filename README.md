# Video Translation App

Web aplikasi untuk menambahkan subtitle bahasa Inggris ke video secara otomatis.

## 🚀 Cara Menjalankan

### 1. Versi Demo (Siap Pakai)
```bash
python app_simple.py
```
Lalu buka browser ke: http://localhost:5000

### 2. Versi Lengkap (Perlu Install Dependencies)
```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan aplikasi
python main.py
```

## 📋 Fitur

- **Upload Video**: Drag & drop file video
- **Multi Format**: Mendukung MP4, AVI, MOV, MKV, WMV, FLV, WEBM
- **Multi Bahasa**: Deteksi otomatis atau pilih bahasa sumber
- **Progress Tracking**: Pantau proses real-time
- **Download Result**: Unduh video dengan subtitle bahasa Inggris

## 🛠️ Dependencies untuk Versi Lengkap

- Flask (web framework)
- MoviePy (video processing)
- OpenAI Whisper (speech recognition)
- Google Translate (translation)
- FFmpeg (audio/video codecs)

## 📁 Struktur Project

```
translate-video/
├── app_simple.py          # Versi demo (siap pakai)
├── main.py               # Versi lengkap
├── requirements.txt      # Dependencies
├── utils/               # Utilitas processing
│   ├── video_processor.py
│   ├── transcriber.py
│   ├── translator.py
│   └── subtitle_generator.py
├── templates/           # HTML templates
│   ├── index.html
│   └── processing.html
├── static/             # File upload/download
│   ├── uploads/
│   └── processed/
└── video/              # Video anda
```

## 💡 Cara Menggunakan

1. **Jalankan aplikasi** (lihat instruksi di atas)
2. **Buka browser** ke http://localhost:5000
3. **Upload video** dengan drag & drop atau klik browse
4. **Pilih bahasa sumber** (atau biarkan auto-detect)
5. **Klik "Start Translation"**
6. **Tunggu proses selesai** (akan ada progress bar)
7. **Download video** dengan subtitle bahasa Inggris

## 🔧 Install FFmpeg (untuk versi lengkap)

Windows:
1. Download dari https://ffmpeg.org/download.html
2. Extract dan tambahkan ke PATH system
3. Test dengan command: `ffmpeg -version`

## 📝 Catatan

- **Versi Demo**: Hanya simulasi, video tidak diproses secara real
- **Versi Lengkap**: Memerlukan dependencies dan FFmpeg untuk processing sesungguhnya
- **File Size Limit**: Maximum 500MB per file
- **Supported Languages**: 20+ bahasa dengan auto-detection

## 🐛 Troubleshooting

- **Module not found**: Install dependencies dengan `pip install -r requirements.txt`
- **FFmpeg error**: Pastikan FFmpeg sudah terinstall dan ada di PATH
- **Unicode error**: Gunakan `app_simple.py` untuk demo tanpa dependencies