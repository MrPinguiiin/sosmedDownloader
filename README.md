# Sosmed Downloader Bot

Bot Telegram untuk mendownload video dari TikTok, YouTube, dan Instagram

## Instalasi

1. Clone repository:
```bash
git clone https://github.com/MrPinguiiin/sosmedDownloader.git
cd sosmedDownloader
```

2. Jalankan installer:
```bash
chmod +x sosmedDownloaderInstaller.sh
./sosmedDownloaderInstaller.sh
```

3. Ikuti petunjuk untuk mengisi:
- Token Bot Telegram
- ID Telegram Anda
- Subdomain (opsional)

## Cara Menggunakan

1. Buka bot Telegram Anda
2. Kirim command `/start`
3. Pilih platform (TikTok/YouTube/Instagram)
4. Pilih resolusi (720p/1080p/Terbaik/Audio Saja)
5. Kirim link video yang ingin didownload
6. Tunggu hingga proses selesai

## Fitur
- Support multiple platform
- Pilihan resolusi
- Download audio saja
- Antarmuka interaktif

## Fitur Baru

### Batch Download
- Kirim command `/batch`
- Paste semua link video (1 link per baris)
- Bot akan memproses semua link secara berurutan
- Mendukung hingga 10 link sekaligus

Contoh penggunaan:
```
/batch
https://tiktok.com/...
https://youtube.com/...
https://instagram.com/...
```

### TikTok Watermark Removal
- Pilih platform 'TikTok'
- Pilih opsi 'Tanpa Watermark'
- Kirim link video TikTok
- Bot akan mengirimkan video tanpa watermark

Note: Fitur ini mungkin tidak bekerja untuk semua video TikTok tergantung kebijakan platform

### Format Conversion
- Pilih opsi 'MP3' untuk mengkonversi ke audio
- Pilih opsi 'GIF' untuk mengkonversi ke animasi GIF (10 detik pertama)
- Hasil konversi akan dikirim sekaligus file aslinya

Note: Pastikan server memiliki FFmpeg terinstall

### Metadata Preservation
- Bot akan menyimpan:
  - Judul video asli
  - Deskripsi video
  - Thumbnail/cover
  - Informasi uploader
- Metadata bisa dilihat di properti file hasil download

Note: Fitur ini bekerja untuk format MP4 dan MP3

### Google Drive Integration
1. Buat project di Google Cloud Console
2. Aktifkan Google Drive API
3. Download credentials.json dan simpan di folder bot
4. Saat pertama kali run, bot akan meminta autentikasi
5. File hasil download akan otomatis diupload ke Google Drive

Note: Diperlukan akses internet untuk upload ke Google Drive

### User Quota System
- Setiap user mendapat 10 download per hari
- Cek quota dengan command `/quota`
- Quota reset setiap 24 jam

Untuk admin:
- Ubah `MAX_DAILY_DOWNLOADS` di bot.py untuk adjust quota

### Admin Dashboard (Updated)
Fitur baru:
- 🚫 Ban User - Blokir user tertentu
- ✅ Unban User - Hapus blokir user
- 📊 Stats - Total downloads harian

Cara pakai:
1. Kirim `/admin`
2. Pilih '🔧 Settings'
3. Pilih aksi yang diinginkan

### Auto Delete System
- File akan otomatis terhapus 30 menit setelah download
- Untuk adjust waktu, ubah `AUTO_DELETE_MINUTES` di bot.py
- Sistem berjalan di background tanpa mengganggu proses utama

## Requirements
- Python 3
- pip
- git
- unzip
