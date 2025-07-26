# jellyfin-movieposter
A python-based project that uses the Jellyfin API to show the poster of the movie you're watching.
It loads the poster with a nice frame around it, and adds the title, a QR-code to imdb, and the tagline beneath the poster.

I run this project on a Raspberry Pi Zero that's connected to a 32 inch Samsung The Frame TV.

![alt text](https://github.com/Hilko113/jellyfin-movieposter/blob/main/example.jpg)


I did not include fonts. You can download a font you like and edit the following lines in posterdownload.py:

            font_title = ImageFont.truetype("arial.ttf", size=30)
            font_tag = ImageFont.truetype("arial.ttf", size=70)


To install this on a Raspberry Pi Zero follow the next steps:


Install Raspberry OS Lite (no gui)

Connect to network and enable SSH
```
sudo apt-get update
sudo apt install python3 python3-pip
sudo apt install python3-pil
sudo apt install python3-pygame
sudo apt install xserver-xorg xinit openbox
python3 -m pip install --break-system-packages qrcode[pil] requests
sudo usermod -aG video pi
chmod +x /home/pi/posterdownload.py
```
```
nano ~/.xinitrc
```
Paste the text below:
```
#!/bin/sh

# Wake HDMI if blanked
xrandr --output HDMI-1 --auto || xrandr --output HDMI-0 --auto

# Run app
python3 /home/pi/postershow.py
```
```
chmod +x ~/.xinitrc
```
```
nano ~/.bash_profile
```
Paste the text below:
```
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  startx
fi
```
```
sudo raspi-config
```
Choose: System Options → Boot / Auto Login → Console Autologin
```
sudo nano /etc/systemd/system/jellyfin-poster.service
```
Paste the text below:
```
[Unit]
Description=Fetch & process Jellyfin poster

[Service]
Type=oneshot
User=pi
# Adjust if you install script elsewhere
ExecStart=/usr/bin/env python3 /home/pi/posterdownload.py
```
```
sudo nano /etc/systemd/system/jellyfin-poster.timer
```
Paste the text below:
```
[Unit]
Description=Run Jellyfin poster fetch every 30s

[Timer]
OnBootSec=30s
OnUnitActiveSec=30s
AccuracySec=1s

[Install]
WantedBy=timers.target
```
```
sudo systemctl daemon-reload
```
```
sudo systemctl enable --now jellyfin-poster.timer
```
