# Job Application AI Assistant (JobCopilot Clone)

## Overview
A JobCopilot-style job application assistant where you paste job URLs, AI analyzes each against your CV, calculates match scores (0-100%), and provides intelligent recommendations. Built for Foundation Phase/Special Ed teachers targeting NZ positions.

## Features
- **URL Paste Interface**: Paste job URLs from LinkedIn, Seek NZ, Education Gazette (one per line)
- **Automatic Job Fetching**: Web scraper extracts job title, company, location, description from URLs
- **AI-Powered Analysis**: Claude 3.5 Sonnet analyzes each job against your CV and assigns 0-100% match score
- **Intelligent Categorization**: 
  - 70-100% = EXCELLENT match (green badge)
  - 50-69% = GOOD match (yellow badge)
  - 0-49% = Lower match (gray badge)
- **Detailed AI Reasoning**: Shows why each job is/isn't a good match
- **Multi-Source Support**: Handles LinkedIn, Seek NZ, and Education Gazette NZ job postings
- **Auto-Apply Ready**: Jobs with 80%+ match show "Auto-Apply" button (cover letter generation coming soon)
- **Clean Dashboard**: Tailwind CSS interface with color-coded borders, match scores, and filtering
- **Single-User Authentication**: Secure password-protected access
- **SQLite Database**: Stores analyzed jobs, prevents duplicates

## Tech Stack
- **Backend**: Python 3.11, Flask
- **Database**: SQLite
- **Email**: Gmail API
- **AI**: Claude 3.5 Sonnet (Anthropic API)
- **Frontend**: HTML, Tailwind CSS
- **Scheduler**: APScheduler (30-minute intervals)

## Project Structure
```
├── app.py                      # Flask application with URL analysis endpoint
├── database.py                 # SQLite database operations with match scores
├── job_fetcher.py              # Web scraper for LinkedIn, Seek, Education Gazette
├── ai_matcher.py               # Claude AI job matching and scoring
├── cv_profile.py               # User CV profile and job preferences
├── templates/
│   ├── login.html             # Login page
│   └── index.html             # URL paste interface + results dashboard
├── requirements.txt            # Python dependencies
└── jobs.db                    # SQLite database (created at runtime)
```

## Required Secrets (in Replit Secrets)
1. **SECRET_KEY**: Flask session security key
2. **AUTH_PASSWORD**: Dashboard login password
3. **ANTHROPIC_API_KEY**: Claude AI API key for job matching

## How to Use
1. **Login** with your password
2. **Find jobs** on LinkedIn, Seek NZ, or Education Gazette
3. **Copy job URLs** from your browser
4. **Paste URLs** into the text box (one per line)
5. **Click "Analyze Jobs with AI"** - system will:
   - Fetch job details from each URL
   - Analyze against your CV with Claude AI
   - Calculate match scores
   - Display results with color-coding
6. **Review results**: Green badges = excellent matches, yellow = good, gray = lower
7. **Click "Auto-Apply"** on 80%+ matches (coming soon)

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
- Nov 3, 2025: **MAJOR PIVOT** - Switched from email monitoring to JobCopilot-style URL paste system
- Nov 3, 2025: Built job_fetcher.py - web scraper for LinkedIn, Seek, Education Gazette
- Nov 3, 2025: Created URL paste interface with "Analyze Jobs" button
- Nov 3, 2025: Added /analyze_jobs endpoint - processes multiple URLs in one request
- Nov 3, 2025: Updated dashboard with match score categories (70%+, 50-69%, <50%)
- Nov 3, 2025: Added color-coded job cards (green/yellow/gray borders based on match)
- Nov 3, 2025: Integrated Claude AI for job analysis (already working from previous version)
- Nov 3, 2025: Removed dependency on Gmail API - simpler, more reliable
- Nov 3, 2025: User now has full control over which jobs to analyze

## User Preferences
- Single-user system (Foundation Phase teacher seeking NZ positions)
- Manual URL pasting (user controls which jobs to analyze)
- AI-powered job matching with detailed reasoning and 0-100% scores
- Clean, informative UI with color-coded match badges
- Focus on simplicity and reliability over automation
