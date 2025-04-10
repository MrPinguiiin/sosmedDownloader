import os
import telebot
from youtube_dl import YoutubeDL

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
    try:
        with YoutubeDL() as ydl:
            info_dict = ydl.extract_info(url, download=False)
            video_url = info_dict.get('url', None) or info_dict.get('webpage_url', None)
            if video_url:
                bot.send_message(message.chat.id, "Sedang mendownload...")
                ydl.download([url])
                bot.send_message(message.chat.id, "Download selesai!")
                bot.send_video(message.chat.id, open(info_dict['title'] + '.mp4', 'rb'))
            else:
                bot.send_message(message.chat.id, "Link tidak valid atau tidak didukung.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Terjadi kesalahan: {str(e)}")

# Jalankan bot
bot.polling()