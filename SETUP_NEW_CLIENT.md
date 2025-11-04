# Setup Instructions for New Client

## Files You Need to Copy:

### Python Files (all in root directory):
- app.py
- database.py
- ai_matcher.py
- auto_apply.py
- cover_letter_generator.py
- cover_letter_pdf.py
- cv_profile.py
- email_sender.py
- gmail_service.py
- job_fetcher_apify.py
- job_fetcher_gazette.py
- job_search_config.py
- apify_cost_tracker.py
- requirements.txt

### Folders:
- templates/ (contains index.html and login.html)
- static/cv/ (upload new client's CV here)

## Customization Steps:

### 1. Update cv_profile.py
Replace ALL details with new client's information:
- name, email, phone, location
- experience, qualifications
- target roles, excluded roles
- skills and specializations

### 2. Upload New CV
- Delete Henriette_Beeslaar_CV.pdf from static/cv/
- Upload new client's CV
- Update filename in auto_apply.py (line ~30)

### 3. Update job_search_config.py
Change keywords to match new client's target jobs

### 4. Set Secrets in Replit:
- SECRET_KEY (generate new with: python -c "import secrets; print(secrets.token_hex(32))")
- AUTH_PASSWORD (dashboard login password)
- ANTHROPIC_API_KEY (use same as Henriette's)

### 5. Connect Gmail Integration:
- Go to Integrations tab
- Add Google Mail
- Connect NEW CLIENT'S Gmail account

### 6. Delete jobs.db
Start with fresh database for new client

## Done!
Run the app and upload new client's job CSVs.
