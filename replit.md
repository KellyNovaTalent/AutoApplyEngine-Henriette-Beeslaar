# Job Application System with AI Matching

## Overview
A fully automatic single-user job application monitoring system that connects to Gmail, parses job alerts from LinkedIn, Seek NZ, and Education Gazette NZ, auto-filters sponsorship jobs, **uses Claude AI to score job matches**, and provides a web dashboard with intelligent job recommendations.

## Features
- **Gmail API Integration**: Monitors job alert emails from LinkedIn, Seek NZ, and Education Gazette NZ
- **Auto-Rejection Filter**: Automatically rejects jobs with "visa sponsorship" or "sponsorship" in the title BEFORE AI analysis
- **AI-Powered Job Matching**: Claude 3.5 Sonnet analyzes each job and assigns a match score (0-100%) based on CV
- **Multi-Source Support**: Handles LinkedIn, Seek NZ, and Education Gazette NZ job alerts with extensible parser system
- **Web Dashboard**: Clean Tailwind CSS interface with color-coded match scores, AI analysis, filtering, and statistics
- **Automatic Processing**: Background job runs every 30 minutes to check for new emails
- **Single-User Authentication**: Secure password-protected access
- **SQLite Database**: Stores all job data with AI analysis and match scores

## Tech Stack
- **Backend**: Python 3.11, Flask
- **Database**: SQLite
- **Email**: Gmail API
- **AI**: Claude 3.5 Sonnet (Anthropic API)
- **Frontend**: HTML, Tailwind CSS
- **Scheduler**: APScheduler (30-minute intervals)

## Project Structure
```
├── app.py                      # Flask application with routes and scheduler
├── database.py                 # SQLite database operations with AI fields
├── gmail_service.py            # Gmail API integration with AI workflow
├── email_parser.py             # Email parsing for LinkedIn, Seek NZ, and Education Gazette NZ
├── ai_matcher.py               # Claude AI job matching and scoring
├── cv_profile.py               # User CV profile and job preferences
├── templates/
│   ├── login.html             # Login page
│   └── index.html             # Dashboard with AI match scores
├── requirements.txt            # Python dependencies (including anthropic)
├── SETUP_INSTRUCTIONS.md       # Gmail API setup guide
├── AI_INTEGRATION_GUIDE.md     # AI matching documentation
└── jobs.db                    # SQLite database (created at runtime)
```

## Required Secrets (in Replit Secrets)
1. **SECRET_KEY**: Flask session security key
2. **AUTH_PASSWORD**: Dashboard login password
3. **ANTHROPIC_API_KEY**: Claude AI API key for job matching

## Setup Required
1. **Gmail API Credentials**: Upload `credentials.json` from Google Cloud Console (see SETUP_INSTRUCTIONS.md)
2. **Set Environment Secrets**: SECRET_KEY, AUTH_PASSWORD, ANTHROPIC_API_KEY
3. **First Run**: Click "Sync Emails" to authenticate with Gmail and start monitoring

## Database Schema
- **jobs**: Job postings with details, status, AI match_score, ai_analysis
- **email_tracking**: Prevents duplicate email processing
- **app_settings**: Application configuration

## AI Match Scoring
Claude AI analyzes each job based on:
- **Location Match (0-30 points)**: Must be in New Zealand
- **Role Match (0-30 points)**: Foundation Phase/Primary/Special Education teaching
- **Experience Level (0-20 points)**: Suitable for 18+ years experience
- **Specialization Match (0-20 points)**: Special needs, learning support, inclusive education

**Score Interpretation**:
- 70-100%: EXCELLENT match (green badge)
- 50-69%: GOOD match (yellow badge)
- 0-49%: Lower match (gray badge)

## User Profile (Henriëtte Charlotte Beeslaar)
- **Experience**: 18+ years Foundation Phase and Special Education teaching
- **Qualifications**: B.Ed Foundation Phase, NZ Teaching Registration
- **Specializations**: Autism, Down Syndrome, ADHD, intellectual disabilities
- **Target Location**: New Zealand
- **Preferred Roles**: Foundation Phase, Primary School, Special Education, Learning Support
- **Languages**: English and Afrikaans

## Recent Changes
- Nov 3, 2025: Added Education Gazette NZ email parser for teaching job alerts
- Nov 3, 2025: Integrated Claude AI for automatic job matching
- Nov 3, 2025: Added AI analysis and match score fields to database
- Nov 3, 2025: Updated UI with color-coded match scores and AI analysis display
- Nov 3, 2025: Fixed AI response parsing to handle ThinkingBlock correctly
- Nov 2, 2025: Initial project setup with Gmail integration and auto-rejection
- Nov 2, 2025: Implemented LinkedIn and Seek NZ email parsers
- Nov 2, 2025: Built web dashboard with statistics and filtering
- Nov 2, 2025: Secured authentication with environment variables

## User Preferences
- Single-user system (Foundation Phase teacher seeking NZ positions)
- Automatic processing without approval workflow
- Filter out sponsorship jobs BEFORE AI analysis (saves API costs)
- AI-powered job matching with detailed reasoning
- Clean, informative UI with prominent match scores
