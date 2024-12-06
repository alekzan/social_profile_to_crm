import streamlit as st
import sqlite3
from urllib.parse import urlparse, parse_qs
import re

# Import the functions you have defined
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import xmlrpc.client

# Load environment variables
load_dotenv()
URL = os.getenv("URL_DEMO")
DB = os.getenv("DB_DEMO")
USERNAME = os.getenv("USERNAME_DEMO")
PASSWORD = os.getenv("PASSWORD_DEMO")

# --- Functions for data extraction (copied from your code) ---
def convert_shorthand_to_number(value):
    if 'K' in value:
        return int(float(value.replace('K', '')) * 1_000)
    elif 'M' in value:
        return int(float(value.replace('M', '')) * 1_000_000)
    elif 'B' in value:
        return int(float(value.replace('B', '')) * 1_000_000_000)
    else:
        return int(value.replace(',', ''))

def extract_instagram_data(url):
    """
    Extracts username, handle, followers, bio, and the URL from an Instagram profile.

    Args:
    - url (str): The URL of the Instagram profile.

    Returns:
    - dict: A dictionary containing username, handle, followers, bio, and URL.
    """
    try:
        # Parse the URL to clean up the query parameters
        parsed_url = urlparse(url)
        path = parsed_url.path.rstrip("/")  # Remove trailing slash
        username = path.split("/")[-1]  # Extract the last part of the path

        handle = f"@{username}"  # Create the handle

        # Fetch HTML content
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract metadata
        meta_description_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_description_tag:
            meta_description = meta_description_tag.get('content', '')
        else:
            raise ValueError("Meta description not found")

        username_meta_tag = soup.find('meta', attrs={'property': 'og:title'})
        if username_meta_tag:
            username_meta = username_meta_tag.get('content', '')
            username = username_meta.split("•")[0].strip()
        else:
            raise ValueError("Username meta tag not found")

        # Extract and convert follower count
        follower_data = meta_description.split('Followers,')[0].strip()
        followers_count = convert_shorthand_to_number(follower_data)

        # Extract and clean bio
        bio_part = meta_description.split(' - ')[-1]
        bio_clean = bio_part.split('on Instagram:')[1].strip() if 'on Instagram:' in bio_part else bio_part
        bio_clean = bio_clean.replace('\n', ' ')  # Replace line breaks with spaces

        # Return extracted data as a dictionary
        return {
            'user': username,
            'username': handle,
            'followers': followers_count,
            'bio': bio_clean,
            'link': f"https://www.instagram.com/{username}/",  # Standardized URL
            'network': 'IG'
        }
    except Exception as e:
        return {"error": str(e)}

def extract_tiktok_profile_data(url):
    def convert_to_number(value):
        if value[-1].lower() == 'm':
            return int(float(value[:-1]) * 1_000_000)
        elif value[-1].lower() == 'k':
            return int(float(value[:-1]) * 1_000)
        else:
            return int(value)

    def decode_unicode_escapes(encoded_str):
        return encoded_str.encode('utf-8').decode('unicode_escape')

    def extract_username_from_url(url):
        path = urlparse(url).path
        match = re.search(r'/@([^/?]+)', path)
        return f"@{match.group(1)}" if match else "No username found"

    username = extract_username_from_url(url)
    headers = {
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://www.tiktok.com/',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')
    script_tags = soup.find_all('script')

    signature = None
    title = None
    followers = None
    likes = None
    link_in_bio = None

    for tag in script_tags:
        tag_text = tag.text
        if 'signature' in tag_text and not signature:
            signature_pattern = r'"signature":"(.*?)","createTime"'
            signature_match = re.search(signature_pattern, tag_text)
            if signature_match:
                signature = signature_match.group(1)

        if '"shareMeta":{"title":"' in tag_text and not (title and followers and likes):
            title_pattern = r'"shareMeta":{"title":"(.*?)"'
            followers_pattern = r'@[^ ]+ ([\d\.]+[a-zA-Z]*) Followers'
            likes_pattern = r'([\d\.]+[a-zA-Z]*) Likes'

            title_match = re.search(title_pattern, tag_text)
            title = title_match.group(1) if title_match else None

            followers_match = re.search(followers_pattern, tag_text)
            followers_raw = followers_match.group(1) if followers_match else None
            followers = convert_to_number(followers_raw) if followers_raw else None

            likes_match = re.search(likes_pattern, tag_text)
            likes_raw = likes_match.group(1) if likes_match else None
            likes = convert_to_number(likes_raw) if likes_raw else None

        if '"bioLink":{"link":"' in tag_text and not link_in_bio:
            link_pattern = r'"bioLink":{"link":"(.*?)","risk":'
            link_match = re.search(link_pattern, tag_text)
            if link_match:
                raw_link = link_match.group(1)
                link_in_bio = decode_unicode_escapes(raw_link)

    description = signature if signature else "No description found"

    return {
        "user": title if title else "No title found",
        "username": username,
        "followers": followers if followers else 0,
        "bio": description,
        "link": url,
        'network': 'TikTok',
        "likes": likes if likes else 0,
        "link_in_bio": link_in_bio if link_in_bio else ""
    }

# --- Odoo lead creation function (copied from your code) ---
def create_lead_from_social_media(profile_data, url=URL, db=DB, username=USERNAME, password=PASSWORD):
    user_display_name = profile_data.get('user')
    username_handle = profile_data.get('username')
    network = profile_data.get('network')
    link = profile_data.get('link')
    bio = profile_data.get('bio')
    followers = profile_data.get('followers', 0)
    likes = profile_data.get('likes', '')
    link_in_bio = profile_data.get('link_in_bio', '')

    description_lines = [f"Bio: {bio}"]
    if network == 'TikTok':
        if link_in_bio:
            description_lines.append(f"Link en bio: {link_in_bio}")
        if likes:
            description_lines.append(f"Likes en contenido: {likes}")
    description = "\n".join(description_lines)

    tag_ids = []
    if followers < 30000:
        tag_ids = [1]
    elif 30001 <= followers <= 50000:
        tag_ids = [2]
    elif 50001 <= followers <= 100000:
        tag_ids = [6]
    elif followers > 100000:
        tag_ids = [7]

    lead_name = f"{username_handle} en {network}"

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("Authentication failed")
        return None

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    partner_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['name', '=', user_display_name]]]
    )

    if partner_ids:
        partner_id = partner_ids[0]
        print(f"Existing partner found with ID: {partner_id}")
    else:
        partner_values = {
            'name': user_display_name,
            'phone': '+1234567890',
        }
        partner_id = models.execute_kw(
            db, uid, password, 'res.partner', 'create', [partner_values]
        )
        print(f"Partner created with ID: {partner_id}")

    lead_values = {
        "name": lead_name,
        "partner_id": partner_id,
        "website": link,
        "description": description,
        "tag_ids": [(6, 0, tag_ids)],
    }

    lead_id = models.execute_kw(db, uid, password, "crm.lead", "create", [lead_values])
    print("Lead created with ID:", lead_id)

    activity_type_id = 1
    today = datetime.today().strftime('%d-%m-%Y')
    activity_summary = f"Enviar Mensaje.\nAgregado el {today}."

    model_ids = models.execute_kw(db, uid, password, 'ir.model', 'search', [[['model', '=', 'crm.lead']]])
    if not model_ids:
        print("Could not find model 'crm.lead'")
        return lead_id
    res_model_id = model_ids[0]

    activity_values = {
        'res_model_id': res_model_id,
        'res_id': lead_id,
        'activity_type_id': activity_type_id,
        'summary': activity_summary,
        'date_deadline': (datetime.today() + timedelta(days=7)).strftime('%Y-%m-%d'),
        'user_id': uid,
    }

    activity_id = models.execute_kw(db, uid, password, "mail.activity", "create", [activity_values])
    print("Activity scheduled with ID:", activity_id)

    return lead_id

# --- Database Setup ---
# We will create a local SQLite DB to store (username, network)
conn = sqlite3.connect('data/submissions.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS submissions (username TEXT, network TEXT)''')
conn.commit()

# --- Streamlit App ---
st.title("Registro de Perfiles de IG/TikTok")

st.write("Instrucciones: Ingrese la URL del perfil de Instagram o TikTok y presione el botón para enviar.")
st.write("El sistema extraerá los datos del perfil y creará un nuevo lead en Odoo, **si no se ha enviado antes**.")
st.write("Si ya se ha enviado ese perfil (mismo usuario y misma red social), se le informará al usuario.")

url_input = st.text_input("URL del perfil (ejemplo: https://www.instagram.com/joedoe o https://www.tiktok.com/@joedoe)")

if st.button("Enviar"):
    if not url_input.strip():
        st.warning("Por favor ingrese una URL.")
    else:
        # Determine if IG or TikTok
        if "instagram.com" in url_input.lower():
            network = "IG"
            profile_data = extract_instagram_data(url_input.strip())
        elif "tiktok.com" in url_input.lower():
            network = "TikTok"
            profile_data = extract_tiktok_profile_data(url_input.strip())
        else:
            st.error("La URL no corresponde a Instagram ni a TikTok. Por favor ingrese un enlace válido.")
            st.stop()

        # Check for errors in extraction
        if "error" in profile_data:
            st.error(f"Ocurrió un error al extraer los datos: {profile_data['error']}")
            st.stop()

        # Extract username from profile data (remove '@' for storage)
        username_extracted = profile_data.get("username", "").lstrip("@")

        if not username_extracted:
            st.error("No se pudo extraer el nombre de usuario del perfil.")
            st.stop()

        # Check if this (username, network) is already in DB
        c.execute("SELECT * FROM submissions WHERE username=? AND network=?", (username_extracted, network))
        existing = c.fetchone()

        if existing:
            st.warning(f"Este perfil ({username_extracted} - {network}) ya fue enviado anteriormente.")
        else:
            # Send info to Odoo
            lead_id = create_lead_from_social_media(profile_data)
            if lead_id:
                # Store in DB
                c.execute("INSERT INTO submissions (username, network) VALUES (?, ?)", (username_extracted, network))
                conn.commit()
                st.success(f"Lead creado con éxito en Odoo con ID: {lead_id}")
            else:
                st.error("No se pudo crear el lead en Odoo. Verifique la configuración.")
