# Setup Instructions for Job Application System

## Prerequisites
You need to set up Gmail API access to allow this system to read your job alert emails.

## Step 1: Get Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select an existing one)
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen first:
     - User Type: External
     - App name: Job Application System
     - User support email: your email
     - Developer contact: your email
     - Scopes: Leave default
     - Test users: Add your email address
   - Application type: Desktop app
   - Name: Job Application System
   - Click "Create"

5. Download the credentials:
   - Click the download icon next to your newly created OAuth client
   - Save the file as `credentials.json` in the project root directory

## Step 2: First Time Gmail Authentication

When you first run the application and click "Sync Emails", the system will:
1. Open a browser window asking you to sign in to your Google account
2. Ask you to grant permission to read your emails
3. Save an authentication token (`token.json`) for future use

**Important**: The system only reads your emails, it never sends emails or modifies them.

## Step 3: Configure Email Filters (Optional but Recommended)

To ensure you receive job alerts, make sure:
- You're subscribed to LinkedIn job alerts (Settings > Job Alerts)
- You're subscribed to Seek NZ job alerts

The system monitors emails from:
- LinkedIn: `jobs-listings@linkedin.com` or any `linkedin.com` email
- Seek NZ: `noreply@seek.co.nz` or `job-alerts@seek.co.nz`

## Step 4: Access the Dashboard

1. Open your browser and go to the application URL
2. Default login password: `admin123`
3. Click "Sync Emails" to fetch and process job alerts
4. The system will automatically check for new emails every 30 minutes

## Security Notes

- The `credentials.json` and `token.json` files contain sensitive information
- Never commit these files to version control (they're in .gitignore)
- Change the default password by setting the `AUTH_PASSWORD` environment variable

## How It Works

1. **Email Monitoring**: Every 30 minutes, the system checks your Gmail for new job alerts
2. **Parsing**: Extracts job details (title, company, location, URL, etc.)
3. **Auto-Filtering**: Automatically rejects jobs with "sponsorship" in the title
4. **Storage**: Saves all jobs to a local SQLite database
5. **Dashboard**: Displays jobs with filtering options and statistics

## Troubleshooting

**"credentials.json not found"**
- Make sure you've downloaded the OAuth credentials from Google Cloud Console
- Place the file in the project root directory

**"No jobs found"**
- Make sure you have job alert emails in your Gmail
- Check that you're subscribed to LinkedIn and/or Seek NZ job alerts
- Try clicking "Sync Emails" manually

**"Authentication failed"**
- Delete `token.json` and try again
- Make sure you're using the correct Google account

## Support

If you encounter issues:
1. Check the console logs for error messages
2. Verify your Gmail API credentials are correct
3. Ensure you've granted the necessary permissions
