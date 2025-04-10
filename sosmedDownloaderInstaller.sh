#!/bin/bash

# Hapus skrip jika sudah ada
rm -f sosmedDownloaderInstaller.sh

# Update sistem
apt update && apt upgrade -y

# Install dependensi sistem
apt install -y python3 python3-pip git unzip ffmpeg

# Clone repositori
git clone https://github.com/mrpinguiiin/sosmedDownloader.git

# Masuk ke direktori repositori
cd sosmedDownloader

# Install dependensi Python
pip3 install -r requirements.txt

# Install yt-dlp
pip3 install yt-dlp

# Setup var.txt
echo ""
read -p "Masukkan Bot Token: " bottoken
read -p "Masukkan Admin ID: " admin
read -p "Masukkan Domain (opsional): " domain

echo "BOT_TOKEN=$bottoken" > var.txt
echo "ADMIN=$admin" >> var.txt
echo "DOMAIN=$domain" >> var.txt

clear
echo "Data Bot Anda:"
echo -e "==============================="
echo "Bot Token     : $bottoken"
echo "Id Telegram   : $admin"
echo "Subdomain     : $domain"
echo -e "==============================="
echo "Pengaturan selesai. Mohon tunggu 10 detik..."
sleep 10

# Buat file service systemd
cat > /etc/systemd/system/sosmedDownloader.service << END
[Unit]
Description=SosmedDownloader - Bot Downloader
After=network.target

[Service]
WorkingDirectory=/root/sosmedDownloader
ExecStart=/usr/bin/python3 /root/sosmedDownloader/bot.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
END

# Mulai dan aktifkan service
systemctl daemon-reload
systemctl start sosmedDownloader
systemctl enable sosmedDownloader

clear

echo -e "==============================================="
echo "Instalasi selesai, ketik /menu di bot Telegram Anda"
echo -e "==============================================="
read -n 1 -s -r -p "Tekan tombol apa saja untuk reboot"
rm -f sosmedDownloaderInstaller.sh
clear
reboot