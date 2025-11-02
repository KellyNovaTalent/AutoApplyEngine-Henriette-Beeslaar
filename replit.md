# Job Application System

## Overview
A fully automatic single-user job application monitoring system that connects to Gmail, parses job alerts from LinkedIn and Seek NZ, auto-filters sponsorship jobs, and provides a web dashboard.

## Features
- **Gmail API Integration**: Monitors job alert emails from LinkedIn and Seek NZ
- **Auto-Rejection Filter**: Automatically rejects jobs with "visa sponsorship" or "sponsorship" in the title
- **Multi-Source Support**: Handles LinkedIn and Seek NZ job alerts with extensible parser system
- **Web Dashboard**: Clean Tailwind CSS interface with filtering and statistics
- **Automatic Processing**: Background job runs every 30 minutes to check for new emails
- **Single-User Authentication**: Password-protected access
- **SQLite Database**: Stores all job data with comprehensive fields

## Tech Stack
- **Backend**: Python 3.11, Flask
- **Database**: SQLite
- **Email**: Gmail API
- **Frontend**: HTML, Tailwind CSS
- **Scheduler**: APScheduler (30-minute intervals)

## Project Structure
```
├── app.py                  # Flask application with routes and scheduler
├── database.py             # SQLite database operations
├── gmail_service.py        # Gmail API integration
├── email_parser.py         # Email parsing for LinkedIn and Seek NZ
├── templates/
│   ├── login.html         # Login page
│   └── index.html         # Main dashboard
├── requirements.txt        # Python dependencies
└── jobs.db                # SQLite database (created at runtime)
```

## Setup Required
1. **Gmail API Credentials**: User needs to provide `credentials.json` from Google Cloud Console
2. **Password**: Default is `admin123` (can be changed via AUTH_PASSWORD env var)

## Database Schema
- **jobs**: Stores all job postings with details, status, and metadata
- **email_tracking**: Prevents duplicate processing of emails
- **app_settings**: Application configuration

## Recent Changes
- Initial project setup (Nov 2, 2025)
- Created complete automatic job application system
- Implemented LinkedIn and Seek NZ email parsers
- Added auto-rejection filter for sponsorship jobs
- Built web dashboard with statistics and filtering
- Configured background scheduler for 30-minute email checks

## User Preferences
- Single-user system
- Automatic processing without approval workflow
- Filter out sponsorship jobs before analysis
- Clean, simple UI
