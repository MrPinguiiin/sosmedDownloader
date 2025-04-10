import os
import telebot
from yt_dlp import YoutubeDL
from telebot import types

# Baca variabel dari file var.txt
with open('/root/sosmedDownloader/var.txt') as f:
    exec(f.read())

# Inisialisasi bot
bot = telebot.TeleBot(BOT_TOKEN)

# Fungsi untuk menangani pesan /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(row_width=3)
    itembtn1 = types.KeyboardButton('TikTok')
    itembtn2 = types.KeyboardButton('YouTube')
    itembtn3 = types.KeyboardButton('Instagram')
    markup.add(itembtn1, itembtn2, itembtn3)
    
    bot.reply_to(message, "Halo! Pilih platform yang ingin Anda download:", reply_markup=markup)

# Variabel global untuk menyimpan pilihan platform
user_choices = {}

# Handler untuk pilihan platform
@bot.message_handler(func=lambda message: message.text in ['TikTok', 'YouTube', 'Instagram'])
def handle_platform_choice(message):
    user_choices[message.chat.id] = {'platform': message.text}
    
    markup = types.ReplyKeyboardMarkup(row_width=2)
    itembtn1 = types.KeyboardButton('720p')
    itembtn2 = types.KeyboardButton('1080p')
    itembtn3 = types.KeyboardButton('Terbaik')
    itembtn4 = types.KeyboardButton('Audio Saja')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4)
    
    bot.send_message(message.chat.id, f"Pilih resolusi untuk {message.text}:", reply_markup=markup)

# Handler untuk pilihan resolusi
@bot.message_handler(func=lambda message: message.text in ['720p', '1080p', 'Terbaik', 'Audio Saja'])
def handle_resolution_choice(message):
    if message.chat.id in user_choices:
        user_choices[message.chat.id]['resolution'] = message.text
        bot.send_message(message.chat.id, "Sekarang kirim link video yang ingin di-download:", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "Silakan pilih platform terlebih dahulu.")

# Fungsi untuk menangani pesan dengan link
@bot.message_handler(func=lambda message: message.text.startswith(('http://', 'https://')))
def download_video(message):
    url = message.text
    
    if message.chat.id not in user_choices:
        bot.send_message(message.chat.id, "Silakan pilih platform dan resolusi terlebih dahulu.")
        return
        
    platform = user_choices[message.chat.id]['platform']
    resolution = user_choices[message.chat.id]['resolution']
    
    try:
        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True
        }
        
        # Set format berdasarkan pilihan resolusi
        if resolution == '720p':
            ydl_opts['format'] = 'best[height<=720]'
        elif resolution == '1080p':
            ydl_opts['format'] = 'best[height<=1080]'
        elif resolution == 'Audio Saja':
            ydl_opts['format'] = 'bestaudio'
        else:  # Terbaik
            ydl_opts['format'] = 'best'
        
        # Platform-specific options
        if platform == 'TikTok':
            ydl_opts['extractor_args'] = {'tiktok': {'format': 'download_addr'}}
        elif platform == 'Instagram':
            ydl_opts['extractor_args'] = {'instagram': {'format': 'download_url'}}
        
        with YoutubeDL(ydl_opts) as ydl:
            bot.send_message(message.chat.id, f"Sedang mendownload dari {platform} ({resolution})...")
            info_dict = ydl.extract_info(url, download=True)
            
            filename = ydl.prepare_filename(info_dict)
            
            if os.path.exists(filename):
                if resolution == 'Audio Saja':
                    with open(filename, 'rb') as audio:
                        bot.send_audio(message.chat.id, audio)
                else:
                    with open(filename, 'rb') as video:
                        bot.send_video(message.chat.id, video)
                
                os.remove(filename)
                bot.send_message(message.chat.id, "Download selesai!")
            else:
                bot.send_message(message.chat.id, "Gagal menemukan file hasil download.")
        
        # Reset pilihan user setelah selesai
        del user_choices[message.chat.id]
                
    except Exception as e:
        bot.send_message(message.chat.id, f"Terjadi kesalahan: {str(e)}")

# Jalankan bot
bot.polling()