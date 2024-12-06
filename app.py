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
    partner_name = f"{username} en {network}"

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, user, password, {})
    if not uid:
        return None

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    partner_ids = models.execute_kw(
        db, uid, password,
        'res.partner', 'search',
        [[['name', '=', partner_name]]]
    )

    if partner_ids:
        partner_id = partner_ids[0]
    else:
        partner_values = {
            'name': partner_name,
            'phone': '+1234567890'
        }
        partner_id = models.execute_kw(
            db, uid, password, 'res.partner', 'create', [partner_values]
        )

    today_date = datetime.today().strftime('%Y-%m-%d')
    lead_name = f"{username} - Agregado {today_date}"

    lead_values = {
        "name": lead_name,
        "partner_id": partner_id,
        "website": link,
        "description": link,
        "tag_ids": [(6, 0, tag_ids)],
    }

    lead_id = models.execute_kw(db, uid, password, "crm.lead", "create", [lead_values])

    activity_type_id = 1
    activity_summary = f"Enviar Mensaje.\nAgregado el {today_date}."

    model_ids = models.execute_kw(db, uid, password, 'ir.model', 'search', [[['model', '=', 'crm.lead']]])
    if not model_ids:
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

    models.execute_kw(db, uid, password, "mail.activity", "create", [activity_values])
    return lead_id

# --- Database Setup ---
conn = sqlite3.connect('data/submissions.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS submissions (username TEXT, network TEXT)''')
conn.commit()

def extract_username_and_network(url):
    parsed = urlparse(url)
    if "instagram.com" in parsed.netloc.lower():
        network = "Instagram"
        path_parts = [p for p in parsed.path.split('/') if p]
        if not path_parts:
            return None, None
        username = path_parts[0]
        return username, network
    elif "tiktok.com" in parsed.netloc.lower():
        network = "TikTok"
        match = re.search(r'/@([^/?]+)', parsed.path)
        if match:
            username = match.group(1)
            return username, network
        else:
            return None, None
    else:
        return None, None

def get_tag_ids_for_followers_range(selection):
    if selection == "Menos de 30,000":
        return [1]
    elif selection == "30,001 a 50,000":
        return [2]
    elif selection == "50,001 a 100,000":
        return [6]
    elif selection == "Más de 100,000":
        return [7]
    return []

# --- Streamlit App ---
st.title("Registro de Perfiles de IG/TikTok")
st.write("Instrucciones: Ingrese la URL del perfil de Instagram o TikTok y seleccione el rango de seguidores.")
st.write("El sistema creará un nuevo lead en Odoo, **si no se ha enviado antes** (mismo usuario y red social).")

url_input = st.text_input("URL del perfil (ejemplo: https://www.instagram.com/joedoe o https://www.tiktok.com/@joedoe)")

followers_range = st.radio(
    "Seleccione el rango de seguidores:",
    ["Menos de 30,000", "30,001 a 50,000", "50,001 a 100,000", "Más de 100,000"]
)

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

        c.execute("SELECT * FROM submissions WHERE username=? AND network=?", (username, network))
        existing = c.fetchone()

        if existing:
            st.warning(f"Este perfil ({username} - {network}) ya fue enviado anteriormente.")
        else:
            tag_ids = get_tag_ids_for_followers_range(followers_range)
            lead_id = create_lead_in_odoo(username, network, url_input.strip(), tag_ids)
            if lead_id:
                c.execute("INSERT INTO submissions (username, network) VALUES (?, ?)", (username, network))
                conn.commit()
                st.success(f"Lead creado con éxito en Odoo con ID: {lead_id}")
            else:
                st.error("No se pudo crear el lead en Odoo. Verifique la configuración.")
