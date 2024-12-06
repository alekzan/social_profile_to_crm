import streamlit as st
import sqlite3
from urllib.parse import urlparse
import re
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

# --- Odoo lead creation function ---
def create_lead_in_odoo(username, network, link, tag_ids, url=URL, db=DB, user=USERNAME, password=PASSWORD):
    # The partner name will be "username en network"
    partner_name = f"{username} en {network}"

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, user, password, {})
    if not uid:
        print("Authentication failed")
        return None

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    # Check if partner already exists
    partner_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['name', '=', partner_name]]]
    )

    if partner_ids:
        partner_id = partner_ids[0]
        print(f"Existing partner found with ID: {partner_id}")
    else:
        partner_values = {
            'name': partner_name,
            'phone': '+1234567890',  # Dummy phone, can be adjusted
        }
        partner_id = models.execute_kw(
            db, uid, password, 'res.partner', 'create', [partner_values]
        )
        print(f"Partner created with ID: {partner_id}")

    # Create lead
    # lead name = username
    # website = link
    # description = link
    lead_values = {
        "name": username,
        "partner_id": partner_id,
        "website": link,
        "description": link,
        "tag_ids": [(6, 0, tag_ids)],
    }

    lead_id = models.execute_kw(db, uid, password, "crm.lead", "create", [lead_values])
    print("Lead created with ID:", lead_id)

    # Create an activity (just like in the previous code)
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
conn = sqlite3.connect('data/submissions.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS submissions (username TEXT, network TEXT)''')
conn.commit()

# --- Helper functions ---
def extract_username_and_network(url):
    """Extract username and determine network from the given URL."""
    parsed = urlparse(url)
    if "instagram.com" in parsed.netloc.lower():
        network = "Instagram"
        # Instagram URL pattern: https://www.instagram.com/username/ or variations
        # The username is typically the first segment after the domain
        path_parts = [p for p in parsed.path.split('/') if p]
        if not path_parts:
            return None, None
        username = path_parts[0]  # first part of the path
        return username, network
    elif "tiktok.com" in parsed.netloc.lower():
        network = "TikTok"
        # TikTok URL pattern: https://www.tiktok.com/@username or variations
        # The username can be extracted by looking for '@' in the path
        match = re.search(r'/@([^/?]+)', parsed.path)
        if match:
            username = match.group(1)
            return username, network
        else:
            return None, None
    else:
        return None, None

def get_tag_ids_for_followers_range(selection):
    """
    Map the user's selection of follower range to the appropriate tag_ids.
    According to the guide:
    if followers < 30000: tag_ids = [1]
    elif 30001 <= followers <= 50000: tag_ids = [2]
    elif 50001 <= followers <= 100000: tag_ids = [6]
    elif followers > 100000: tag_ids = [7]
    """
    if selection == "Menos de 30000":
        return [1]
    elif selection == "30001 a 50000":
        return [2]
    elif selection == "50001 a 100000":
        return [6]
    elif selection == "Más de 100000":
        return [7]
    return []

import streamlit as st
import sqlite3
from urllib.parse import urlparse
import re
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

# --- Odoo lead creation function ---
def create_lead_in_odoo(username, network, link, tag_ids, url=URL, db=DB, user=USERNAME, password=PASSWORD):
    # The partner name will be "username en network"
    partner_name = f"{username} en {network}"

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, user, password, {})
    if not uid:
        print("Authentication failed")
        return None

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    # Check if partner already exists
    partner_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['name', '=', partner_name]]]
    )

    if partner_ids:
        partner_id = partner_ids[0]
        print(f"Existing partner found with ID: {partner_id}")
    else:
        partner_values = {
            'name': partner_name,
            'phone': '+1234567890',  # Dummy phone, can be adjusted
        }
        partner_id = models.execute_kw(
            db, uid, password, 'res.partner', 'create', [partner_values]
        )
        print(f"Partner created with ID: {partner_id}")

    # Create lead
    # lead name = username
    # website = link
    # description = link
    lead_values = {
        "name": username,
        "partner_id": partner_id,
        "website": link,
        "description": link,
        "tag_ids": [(6, 0, tag_ids)],
    }

    lead_id = models.execute_kw(db, uid, password, "crm.lead", "create", [lead_values])
    print("Lead created with ID:", lead_id)

    # Create an activity (just like in the previous code)
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
conn = sqlite3.connect('data/submissions.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS submissions (username TEXT, network TEXT)''')
conn.commit()

# --- Helper functions ---
def extract_username_and_network(url):
    """Extract username and determine network from the given URL."""
    parsed = urlparse(url)
    if "instagram.com" in parsed.netloc.lower():
        network = "Instagram"
        # Instagram URL pattern: https://www.instagram.com/username/ or variations
        # The username is typically the first segment after the domain
        path_parts = [p for p in parsed.path.split('/') if p]
        if not path_parts:
            return None, None
        username = path_parts[0]  # first part of the path
        return username, network
    elif "tiktok.com" in parsed.netloc.lower():
        network = "TikTok"
        # TikTok URL pattern: https://www.tiktok.com/@username or variations
        # The username can be extracted by looking for '@' in the path
        match = re.search(r'/@([^/?]+)', parsed.path)
        if match:
            username = match.group(1)
            return username, network
        else:
            return None, None
    else:
        return None, None

def get_tag_ids_for_followers_range(selection):
    """
    Map the user's selection of follower range to the appropriate tag_ids.
    According to the guide:
    if followers < 30000: tag_ids = [1]
    elif 30001 <= followers <= 50000: tag_ids = [2]
    elif 50001 <= followers <= 100000: tag_ids = [6]
    elif followers > 100000: tag_ids = [7]
    """
    if selection == "Menos de 30000":
        return [1]
    elif selection == "30001 a 50000":
        return [2]
    elif selection == "50001 a 100000":
        return [6]
    elif selection == "Más de 100000":
        return [7]
    return []

# --- Streamlit App ---
st.title("Registro de Perfiles de IG/TikTok")

st.write("Instrucciones: Ingrese la URL del perfil de Instagram o TikTok y seleccione el rango de seguidores.")
st.write("El sistema creará un nuevo lead en Odoo, **si no se ha enviado antes** (mismo usuario y red social).")

url_input = st.text_input("URL del perfil (ejemplo: https://www.instagram.com/joedoe o https://www.tiktok.com/@joedoe)")

st.write("Seleccione el rango de seguidores:")
col1, col2, col3, col4 = st.columns(4)

followers_range = None  # Variable to store the selected range

# Add buttons for follower ranges
with col1:
    if st.button("Menos de 30,000"):
        followers_range = "Menos de 30,000"
with col2:
    if st.button("30,001 a 50,000"):
        followers_range = "30,001 a 50,000"
with col3:
    if st.button("50,001 a 100,000"):
        followers_range = "50,001 a 100,000"
with col4:
    if st.button("Más de 100,000"):
        followers_range = "Más de 100,000"

# Proceed only if a follower range is selected
if st.button("Enviar"):
    if not url_input.strip():
        st.warning("Por favor ingrese una URL.")
    elif not followers_range:
        st.warning("Por favor seleccione un rango de seguidores.")
    else:
        username, network = extract_username_and_network(url_input.strip())
        if not username or not network:
            st.error("La URL no corresponde a un perfil válido de Instagram o TikTok.")
            st.stop()

        # Check if this (username, network) is already in DB
        c.execute("SELECT * FROM submissions WHERE username=? AND network=?", (username, network))
        existing = c.fetchone()

        if existing:
            st.warning(f"Este perfil ({username} - {network}) ya fue enviado anteriormente.")
        else:
            tag_ids = get_tag_ids_for_followers_range(followers_range)
            lead_id = create_lead_in_odoo(username, network, url_input.strip(), tag_ids)
            if lead_id:
                # Store in DB
                c.execute("INSERT INTO submissions (username, network) VALUES (?, ?)", (username, network))
                conn.commit()
                st.success(f"Lead creado con éxito en Odoo con ID: {lead_id}")
            else:
                st.error("No se pudo crear el lead en Odoo. Verifique la configuración.")

# --- Helper functions update ---
def get_tag_ids_for_followers_range(selection):
    """
    Map the user's selection of follower range to the appropriate tag_ids.
    """
    if selection == "Menos de 30,000":
        return [1]
    elif selection == "30,001 a 50,000":
        return [2]
    elif selection == "50,001 a 100,000":
        return [6]
    elif selection == "Más de 100,000":
        return [7]
    return []
