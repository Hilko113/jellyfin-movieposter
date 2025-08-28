#!/usr/bin/env python3

import os
import json
import requests
import textwrap
from PIL import Image, ImageDraw, ImageFont
import qrcode

# Replace these with your Jellyfin server details
JELLYFIN_BASE_URL = "http://192.168.2.62:8096"
API_KEY = "2e6e5ffe71904d3296efa9754570e268"
TARGET_USERNAME = "Hilko"
CACHE_FILE = "poster_cache.json"


def get_currently_playing_info():
    url = f"{JELLYFIN_BASE_URL}/Sessions"
    headers = {'X-Emby-Token': API_KEY}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    sessions = response.json()

    if sessions and 'NowPlayingItem' in sessions[0]:
        return sessions[0]['NowPlayingItem'], sessions[0]['UserName'], sessions[0]['UserId']
    return None, None, None


def get_item_details(item_id, user_id):
    """
    Fetch item metadata including provider IDs and taglines.
    """
    url = f"{JELLYFIN_BASE_URL}/Items/{item_id}"
    headers = {'X-Emby-Token': API_KEY}
    params = {
        'fields': 'ProviderIds,Taglines',
        'userId': user_id
    }
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)


def wrap_text(text, font, max_width, draw):
    """
    Wrap text to fit within max_width when rendered with given font.
    Returns list of lines.
    """
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test_line = f"{current} {word}".strip()
        w, h = draw.textbbox((0, 0), test_line, font=font)[2:]
        if w <= max_width:
            current = test_line
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def adjust_to_9_16(image_path, title, year, tagline=None, imdb_url=None, output_path="poster_final.jpg"):
    with Image.open(image_path) as img:
        # Resize to 2000x3000 if not already
        img = img.resize((2000, 3000), Image.LANCZOS)

        bevel_thickness = 10

        # Create beveled layer
        bevel_width = img.width + 2 * bevel_thickness
        bevel_height = img.height + 2 * bevel_thickness
        bevel_layer = Image.new("RGB", (bevel_width, bevel_height), color="white")
        bevel_layer.paste(img, (bevel_thickness, bevel_thickness))
        draw = ImageDraw.Draw(bevel_layer)
        # Bevel shading
        light = (230, 230, 230)
        dark = (160, 160, 160)
        draw.rectangle([(0, 0), (bevel_width, bevel_thickness)], fill=dark)
        draw.rectangle([(0, 0), (bevel_thickness, bevel_height)], fill=dark)
        draw.rectangle([(0, bevel_height - bevel_thickness), (bevel_width, bevel_height)], fill=light)
        draw.rectangle([(bevel_width - bevel_thickness, 0), (bevel_width, bevel_height)], fill=light)

        # Add passe-partout
        passe_padding = 80
        total_width = bevel_width + 2 * passe_padding
        total_height = bevel_height + 2 * passe_padding
        passe_partout = Image.new("RGB", (total_width, total_height), color="#f8f8f8")
        passe_partout.paste(bevel_layer, (passe_padding, passe_padding))

        # Prepare drawing and fonts
        draw_pp = ImageDraw.Draw(passe_partout)
        try:
            font_title = ImageFont.truetype("nexa.ttf", size=30)
            font_tag = ImageFont.truetype("melodrame.ttf", size=70)
        except IOError:
            font_title = ImageFont.load_default()
            font_tag = ImageFont.load_default()

        # Draw Title at bottom-right
        title_text = f"{title} ({year})"
        bbox = draw_pp.textbbox((0, 0), title_text, font=font_title)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x_title = total_width - text_w - 85
        y_title = total_height - text_h - 55
        draw_pp.text((x_title, y_title), title_text, fill="black", font=font_title)

        # Draw QR code if URL provided
        if imdb_url:
            qr_size = 80
            qr = qrcode.QRCode(
                version=2,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=2,
                border=0,
            )
            qr.add_data(imdb_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
            x_qr = 82
            y_qr = total_height - qr_size
            passe_partout.paste(qr_img, (x_qr, y_qr))

        # Crop to 9:16
        target_ratio = 9 / 16
        current_ratio = total_width / total_height
        if current_ratio < target_ratio:
            final_w = int(total_height * target_ratio)
            final_h = total_height
        else:
            final_w = total_width
            final_h = int(total_width / target_ratio)
        final_img = Image.new("RGB", (final_w, final_h), color="#f8f8f8")
        x_off = (final_w - total_width) // 2
        y_off = (final_h - total_height) // 2
        final_img.paste(passe_partout, (x_off, y_off))

        # Draw Tagline on the cropped image with wrapping
        if tagline:
            draw_final = ImageDraw.Draw(final_img)
            # define margins
            margin = 240
            max_width = final_w - 2 * margin
            # wrap into lines
            lines = wrap_text(tagline, font_tag, max_width, draw_final)
            # calculate total height
            line_height = draw_final.textbbox((0,0), 'A', font=font_tag)[3]
            total_text_height = len(lines) * line_height
            # start drawing lines above bottom margin
            y_text = final_h - total_text_height - 75
            for line in lines:
                w, h = draw_final.textbbox((0, 0), line, font=font_tag)[2:]
                x_text = (final_w - w) // 2
                draw_final.text((x_text, y_text), line, fill="black", font=font_tag)
                y_text += line_height

        # Rotate to portrait
        final_img = final_img.rotate(90, expand=True)

        # Define the temporary file path
        temp_output_path = "poster_temporary.jpg"
        
        # Save the final image to a temporary file first
        final_img.save(temp_output_path)

        os.replace(temp_output_path, output_path)
        
        print(f"Poster processed and saved as {output_path}.")


def download_poster(item_id, title, year, tagline=None, imdb_url=None):
    url = f"{JELLYFIN_BASE_URL}/Items/{item_id}/Images/Primary"
    headers = {'X-Emby-Token': API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open("poster.jpg", 'wb') as f:
            f.write(response.content)
        print("Poster downloaded successfully.")
        adjust_to_9_16("poster.jpg", title, year, tagline, imdb_url)
    else:
        print(f"Failed to download poster. Status code: {response.status_code}")


def main():
    now_playing, username, user_id = get_currently_playing_info()
    if not now_playing:
        print("No media is currently playing.")
        return

    if username != TARGET_USERNAME:
        print(f"Currently playing by {username}, not {TARGET_USERNAME}. Skipping.")
        return

    if now_playing.get('Type') != 'Movie':
        print("Currently playing media is not a Movie. Skipping.")
        return

    item_id = now_playing['Id']
    title = now_playing.get('Name', 'Unknown Title')
    year = now_playing.get('ProductionYear', 'Unknown Year')
    image_tag = now_playing['ImageTags'].get('Primary')

    cache = load_cache()
    if item_id == cache.get('item_id') and image_tag == cache.get('image_tag'):
        print("Same movie poster already downloaded. No action taken.")
        return

    # Fetch additional details including tagline
    full_item = get_item_details(item_id, user_id)
    imdb_id = full_item.get('ProviderIds', {}).get('Imdb')
    imdb_url = f"https://www.imdb.com/title/{imdb_id}/" if imdb_id else None
    taglines = full_item.get('Taglines') or []
    tagline = taglines[0] if taglines else None

    download_poster(item_id, title, year, tagline, imdb_url)

    cache['item_id'] = item_id
    cache['image_tag'] = image_tag
    save_cache(cache)


if __name__ == "__main__":
    main()
