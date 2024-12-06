# Social Profile to CRM

A Streamlit app to extract profile information from Instagram and TikTok and create leads in Odoo CRM.

## Features

- Extracts usernames and profile links from Instagram and TikTok URLs.
- Maps follower ranges to Odoo tags for proper lead categorization.
- Prevents duplicate submissions using SQLite to track processed profiles.
- Integrates seamlessly with Odoo CRM for lead creation and activity tracking.

## How to Use

1. Paste the profile URL (Instagram or TikTok) into the app.
2. Select the follower range for the profile.
3. Click "Enviar" to process the profile:
   - The app checks if the profile has already been submitted.
   - If new, the lead is created in Odoo CRM.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alekzan/social_profile_to_crm.git
