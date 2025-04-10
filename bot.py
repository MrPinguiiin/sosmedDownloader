import os
import telebot
from telebot import types
import yt_dlp
from PIL import Image
import requests
from io import BytesIO
import mutagen
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
import ffmpeg
import time
from datetime import datetime, timedelta
import threading

# Baca variabel dari file var.txt
with open('var.txt') as f:
    config = dict(line.strip().split('=') for line in f if '=' in line)
BOT_TOKEN = config.get('BOT_TOKEN', '').strip("'")
ADMIN = config.get('ADMIN', '').strip("'")
DOMAIN = config.get('DOMAIN', '').strip("'")

# Inisialisasi bot
bot = telebot.TeleBot(BOT_TOKEN)

# Config Admin
ADMIN_IDS = [int(ADMIN)]  # Dari var.txt

# Database sederhana untuk user quota
user_quota = {}
MAX_DAILY_DOWNLOADS = 10  # Maksimal 10 download per hari

# Database banned users
banned_users = set()

# Config Auto Delete
AUTO_DELETE_MINUTES = 30  # Hapus file setelah 30 menit

def schedule_file_deletion(file_path, delay_minutes):
    def delete_file():
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File {file_path} telah dihapus")
        except Exception as e:
            print(f"Gagal menghapus file: {str(e)}")
    
    threading.Timer(delay_minutes * 60, delete_file).start()

# Fungsi untuk check quota
def check_quota(user_id):
    if user_id not in user_quota:
        user_quota[user_id] = {
            'count': 0,
            'reset_time': datetime.now() + timedelta(days=1)
        }
    
    # Reset quota jika sudah lewat waktu
    if datetime.now() > user_quota[user_id]['reset_time']:
        user_quota[user_id] = {
            'count': 0,
            'reset_time': datetime.now() + timedelta(days=1)
        }
    
    return user_quota[user_id]['count'] < MAX_DAILY_DOWNLOADS

# Fungsi untuk update quota
def update_quota(user_id):
    if user_id not in user_quota:
        user_quota[user_id] = {
            'count': 0,
            'reset_time': datetime.now() + timedelta(days=1)
        }
    user_quota[user_id]['count'] += 1

# Fungsi untuk menangani pesan /start
def show_main_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    markup.add('📥 Download', 'ℹ️ Bantuan', '📊 Quota')
    bot.send_message(
        chat_id=chat_id,
        text="Pilih menu:",
        reply_markup=markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        show_main_menu(message.chat.id)
    except Exception as e:
        print(f"Error di /start: {str(e)}")

# Variabel global untuk menyimpan pilihan platform
user_choices = {}

# Fungsi untuk menghapus watermark TikTok
def remove_tiktok_watermark(url):
    try:
        ydl_opts = {
            'format': 'best',
            'extractor_args': {'tiktok': {'format': 'download_addr'}},
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info['url']
    except Exception as e:
        print(f"Error removing watermark: {str(e)}")
        return None

# Handler untuk pilihan platform
@bot.message_handler(func=lambda message: message.text in ['TikTok', 'YouTube', 'Instagram'])
def handle_platform_choice(message):
    user_choices[message.chat.id] = {'platform': message.text}
    
    markup = types.ReplyKeyboardMarkup(row_width=2)
    
    if message.text == 'TikTok':
        itembtn_wm = types.KeyboardButton('Tanpa Watermark')
        markup.add(itembtn_wm)
    
    itembtn1 = types.KeyboardButton('720p')
    itembtn2 = types.KeyboardButton('1080p')
    itembtn3 = types.KeyboardButton('Terbaik')
    itembtn4 = types.KeyboardButton('Audio Saja')
    itembtn5 = types.KeyboardButton('MP3')
    itembtn6 = types.KeyboardButton('GIF')
    markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5, itembtn6)
    
    bot.send_message(message.chat.id, f"Pilih kualitas untuk {message.text}:", reply_markup=markup)

# Handler untuk pilihan resolusi
@bot.message_handler(func=lambda message: message.text in ['720p', '1080p', 'Terbaik', 'Audio Saja', 'Tanpa Watermark', 'MP3', 'GIF'])
def handle_resolution_choice(message):
    if message.chat.id in user_choices:
        user_choices[message.chat.id]['resolution'] = message.text
        bot.send_message(message.chat.id, "Sekarang kirim link video yang ingin di-download:", reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id, "Silakan pilih platform terlebih dahulu.")

# Fungsi untuk menangani pesan dengan link
@bot.message_handler(func=lambda message: message.text.startswith(('http://', 'https://')))
def download_video(message, link=None, is_batch=False, batch_progress=None):
    if message.from_user.id in banned_users:
        bot.send_message(message.chat.id, "Anda telah dibanned dari menggunakan bot ini")
        return
    
    if not check_quota(message.chat.id):
        bot.send_message(message.chat.id, "Maaf, Anda telah mencapai batas download harian.")
        return
    
    if link is None:
        url = message.text
    else:
        url = link
    
    if message.chat.id not in user_choices and not is_batch:
        bot.send_message(message.chat.id, "Silakan pilih platform dan resolusi terlebih dahulu.")
        return
        
    platform = user_choices[message.chat.id]['platform'] if not is_batch else 'YouTube'
    resolution = user_choices[message.chat.id]['resolution'] if not is_batch else 'Terbaik'
    
    try:
        ydl_opts = {
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'writethumbnail': True,
            'postprocessors': [
                {'key': 'FFmpegMetadata'},
                {'key': 'EmbedThumbnail'}
            ]
        }
        
        # Handle TikTok tanpa watermark
        if platform == 'TikTok' and resolution == 'Tanpa Watermark':
            video_url = remove_tiktok_watermark(url)
            if video_url:
                # Download video langsung dari URL tanpa watermark
                filename = f"{int(time.time())}.mp4"
                with requests.get(video_url, stream=True) as r:
                    r.raise_for_status()
                    with open(filename, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                
                with open(filename, 'rb') as video:
                    bot.send_video(message.chat.id, video)
                schedule_file_deletion(filename, AUTO_DELETE_MINUTES)
                update_quota(message.chat.id)
                show_main_menu(message.chat.id)
                return
            else:
                bot.send_message(message.chat.id, "Gagal menghapus watermark, mencoba download biasa...")
                resolution = 'Terbaik'
        
        # Set format berdasarkan pilihan resolusi
        if resolution == '720p':
            ydl_opts['format'] = 'best[height<=720]'
        elif resolution == '1080p':
            ydl_opts['format'] = 'best[height<=1080]'
        elif resolution == 'Audio Saja':
            ydl_opts['format'] = 'bestaudio'
        elif resolution == 'MP3':
            ydl_opts['format'] = 'bestaudio'
        elif resolution == 'GIF':
            ydl_opts['format'] = 'best'
        else:  # Terbaik
            ydl_opts['format'] = 'best'
        
        # Platform-specific options
        if platform == 'TikTok':
            ydl_opts['extractor_args'] = {'tiktok': {'format': 'download_addr'}}
        elif platform == 'Instagram':
            ydl_opts['extractor_args'] = {'instagram': {'format': 'download_url'}}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if is_batch:
                bot.send_message(message.chat.id, f"Sedang mendownload dari {platform} ({resolution}) - {batch_progress[0]}/{batch_progress[1]}...")
            else:
                bot.send_message(message.chat.id, f"Sedang mendownload dari {platform} ({resolution})...")
            info_dict = ydl.extract_info(url, download=True)
            
            filename = ydl.prepare_filename(info_dict)
            
            if os.path.exists(filename):
                save_video_metadata(filename, info_dict)
                
                if resolution == 'MP3':
                    mp3_file = filename.rsplit('.', 1)[0] + '.mp3'
                    if convert_to_mp3(filename, mp3_file):
                        with open(mp3_file, 'rb') as audio:
                            bot.send_audio(message.chat.id, audio)
                        schedule_file_deletion(mp3_file, AUTO_DELETE_MINUTES)
                elif resolution == 'GIF':
                    gif_file = filename.rsplit('.', 1)[0] + '.gif'
                    if convert_to_gif(filename, gif_file):
                        with open(gif_file, 'rb') as gif:
                            bot.send_animation(message.chat.id, gif)
                        schedule_file_deletion(gif_file, AUTO_DELETE_MINUTES)
                elif resolution == 'Audio Saja':
                    with open(filename, 'rb') as audio:
                        bot.send_audio(message.chat.id, audio)
                else:
                    with open(filename, 'rb') as video:
                        bot.send_video(message.chat.id, video)
                
                schedule_file_deletion(filename, AUTO_DELETE_MINUTES)
                update_quota(message.chat.id)
                if is_batch:
                    bot.send_message(message.chat.id, f"Download {batch_progress[0]}/{batch_progress[1]} selesai!")
                else:
                    bot.send_message(message.chat.id, "✅ Download selesai!")
                show_main_menu(message.chat.id)
                
                # Upload ke Google Drive
                # gdrive_link = upload_to_gdrive(filename)
                # if gdrive_link:
                #     bot.send_message(message.chat.id, f"File berhasil diupload ke Google Drive: {gdrive_link}")
            else:
                bot.send_message(message.chat.id, "Gagal menemukan file hasil download.")
                show_main_menu(message.chat.id)
        
        # Reset pilihan user setelah selesai
        if not is_batch:
            del user_choices[message.chat.id]
                
    except Exception as e:
        bot.send_message(message.chat.id, f"Terjadi kesalahan: {str(e)}")
        show_main_menu(message.chat.id)

# Fungsi untuk menyimpan metadata video
def save_video_metadata(filename, info):
    try:
        if filename.endswith('.mp4'):
            video = mutagen.mp4.MP4(filename)
            video['\xa9nam'] = info.get('title', '')
            video['\xa9alb'] = f"{info['extractor_key']} Video"
            video['\xa9ART'] = info.get('uploader', '')
            video['\xa9cmt'] = info.get('description', '')[:255]
            
            # Tambahkan thumbnail jika ada
            thumbnail_url = info.get('thumbnail')
            if thumbnail_url:
                response = requests.get(thumbnail_url)
                if response.status_code == 200:
                    video['covr'] = [mutagen.mp4.MP4Cover(data=response.content)]
            
            video.save()
        elif filename.endswith('.mp3'):
            audio = ID3(filename)
            audio['TIT2'] = TIT2(encoding=3, text=info.get('title', ''))
            audio['TPE1'] = TPE1(encoding=3, text=info.get('uploader', ''))
            audio['TALB'] = TALB(encoding=3, text=f"{info['extractor_key']} Audio")
            
            thumbnail_url = info.get('thumbnail')
            if thumbnail_url:
                response = requests.get(thumbnail_url)
                if response.status_code == 200:
                    audio['APIC'] = APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,
                        desc='Cover',
                        data=response.content
                    )
            
            audio.save()
    except Exception as e:
        print(f"Error saving metadata: {str(e)}")

# Fungsi konversi ke MP3
def convert_to_mp3(input_file, output_file):
    try:
        (
            ffmpeg
            .input(input_file)
            .output(output_file, acodec='libmp3lame', audio_bitrate='192k')
            .run(overwrite_output=True)
        )
        return True
    except Exception as e:
        print(f"MP3 Conversion Error: {str(e)}")
        return False

# Fungsi konversi ke GIF
def convert_to_gif(input_file, output_file, duration=10):
    try:
        (
            ffmpeg
            .input(input_file, ss=0, t=duration)
            .filter('fps', fps=10)
            .filter('scale', w=480, h=-1)
            .output(output_file, loop=0)
            .run(overwrite_output=True)
        )
        return True
    except Exception as e:
        print(f"GIF Conversion Error: {str(e)}")
        return False

# Admin Command Handlers
@bot.message_handler(commands=['admin'], func=lambda m: m.from_user.id in ADMIN_IDS)
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    markup.add('📊 Stats', '👥 Users', '🔧 Settings')
    bot.send_message(message.chat.id, "Admin Dashboard:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '📊 Stats' and m.from_user.id in ADMIN_IDS)
def show_stats(message):
    total_users = len(user_quota)
    active_today = sum(1 for u in user_quota.values() if u['count'] > 0)
    bot.send_message(message.chat.id, f"📊 Bot Stats\n\nTotal Users: {total_users}\nActive Today: {active_today}")

@bot.message_handler(func=lambda m: m.text == '👥 Users' and m.from_user.id in ADMIN_IDS)
def show_users(message):
    active_users = [f"{uid}: {data['count']} downloads" for uid, data in user_quota.items() if data['count'] > 0]
    msg = "👥 Active Users Today:\n\n" + "\n".join(active_users[:50])  # Limit to 50 users
    bot.send_message(message.chat.id, msg)

@bot.message_handler(commands=['batch'])
def handle_batch(message):
    msg = bot.reply_to(message, "Kirim semua link yang ingin didownload (1 link per baris):", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_batch_links)

def process_batch_links(message):
    links = message.text.split('\n')
    valid_links = [link.strip() for link in links if link.strip().startswith(('http://', 'https://'))]
    
    if not valid_links:
        bot.reply_to(message, "Tidak ada link valid yang ditemukan.")
        return
    
    bot.reply_to(message, f"Memproses {len(valid_links)} link...")
    
    for i, link in enumerate(valid_links, 1):
        try:
            # Reuse existing download function
            download_video(message, link, is_batch=True, batch_progress=(i, len(valid_links)))
        except Exception as e:
            bot.reply_to(message, f"Gagal memproses link {i}: {str(e)}")
    
    bot.reply_to(message, "Proses batch download selesai!")
    show_main_menu(message.chat.id)

@bot.message_handler(commands=['quota'])
def show_quota(message):
    user_id = message.from_user.id
    if user_id not in user_quota:
        check_quota(user_id)  # Initialize quota
    
    remaining = MAX_DAILY_DOWNLOADS - user_quota[user_id]['count']
    reset_time = user_quota[user_id]['reset_time']
    
    bot.send_message(message.chat.id,
                   f"Quota harian Anda: {remaining}/{MAX_DAILY_DOWNLOADS}\n"
                   f"Akan reset pada: {reset_time.strftime('%Y-%m-%d %H:%M')}")

@bot.message_handler(func=lambda m: m.text == '🔧 Settings' and m.from_user.id in ADMIN_IDS)
def admin_settings(message):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    markup.add('🚫 Ban User', '✅ Unban User', '⬅️ Back')
    bot.send_message(message.chat.id, "Admin Settings:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🚫 Ban User' and m.from_user.id in ADMIN_IDS)
def request_ban_user(message):
    msg = bot.reply_to(message, "Kirim ID user yang akan diban:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_ban_user)

def process_ban_user(message):
    try:
        user_id = int(message.text)
        banned_users.add(user_id)
        bot.send_message(message.chat.id, f"User {user_id} telah dibanned!")
    except ValueError:
        bot.send_message(message.chat.id, "ID user tidak valid")

@bot.message_handler(func=lambda m: m.text == '✅ Unban User' and m.from_user.id in ADMIN_IDS)
def request_unban_user(message):
    msg = bot.reply_to(message, "Kirim ID user yang akan diunban:", reply_markup=types.ForceReply())
    bot.register_next_step_handler(msg, process_unban_user)

def process_unban_user(message):
    try:
        user_id = int(message.text)
        if user_id in banned_users:
            banned_users.remove(user_id)
            bot.send_message(message.chat.id, f"User {user_id} telah diunban!")
        else:
            bot.send_message(message.chat.id, "User tidak ditemukan dalam daftar banned")
    except ValueError:
        bot.send_message(message.chat.id, "ID user tidak valid")

@bot.message_handler(func=lambda m: m.from_user.id in banned_users)
def handle_banned_user(message):
    bot.send_message(message.chat.id, "Anda telah dibanned dari menggunakan bot ini")

# Jalankan bot
bot.polling()