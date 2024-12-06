# Social Profile to CRM
A Streamlit app to extract profile information from Instagram and TikTok and create leads in Odoo CRM.

## Features
- Extracts data from Instagram and TikTok profiles.
- Prevents duplicate submissions using SQLite.

## How to Use
- Paste the profile URL (Instagram or TikTok) in the app.
- The app fetches data, checks for duplicates, and sends the lead to Odoo if it's new.

## Installation
1. Clone the repo: `git clone https://github.com/alekzan/social_profile_to_crm.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `streamlit run app.py`
4. Add your keys in an .env file exactly like this:


URL_DEMO = "{Your Odoo url link to the CRM, e.g. https://example.odoo.com}"
DB_DEMO = "{The name of your database}"
USERNAME_DEMO = "{Your username, usually an email}"
PASSWORD_DEMO = "{Your password for Odoo}"


## License
MIT
