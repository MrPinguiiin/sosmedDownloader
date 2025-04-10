import os
import telebot
from yt_dlp import YoutubeDL

# Baca variabel dari file var.txt
with open('/root/sosmedDownloader/var.txt') as f:
    exec(f.read())

# Inisialisasi bot
bot = telebot.TeleBot(BOT_TOKEN)

# Fungsi untuk menangani pesan /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Halo! Saya adalah bot downloader. Kirimkan link TikTok, Instagram, atau YouTube yang ingin Anda unduh.")

# Fungsi untuk menangani pesan dengan link
@bot.message_handler(func=lambda message: True)
def download_video(message):
    url = message.text
    
    # Validasi URL sederhana
    if not url.startswith(('http://', 'https://')):
        bot.send_message(message.chat.id, "Format URL tidak valid. Pastikan URL diawali dengan http:// atau https://")
        return
        
    try:
        ydl_opts = {
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True
        }
        
        with YoutubeDL(ydl_opts) as ydl:
            bot.send_message(message.chat.id, "Sedang mendownload...")
            info_dict = ydl.extract_info(url, download=True)
            
            # Cari file yang baru saja di-download
            filename = f"{info_dict['title']}.mp4"
            if not os.path.exists(filename):
                # Jika tidak ada .mp4, coba format lain
                filename = ydl.prepare_filename(info_dict)
                
            if os.path.exists(filename):
                with open(filename, 'rb') as video:
                    bot.send_video(message.chat.id, video)
                os.remove(filename)  # Hapus file setelah dikirim
                bot.send_message(message.chat.id, "Download selesai!")
            else:
                bot.send_message(message.chat.id, "Gagal menemukan file hasil download.")
                
    except Exception as e:
        bot.send_message(message.chat.id, f"Terjadi kesalahan: {str(e)}")

# Jalankan bot
bot.polling()