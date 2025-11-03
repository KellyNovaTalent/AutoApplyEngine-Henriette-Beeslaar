# Job Application AI Assistant (Full JobCopilot Clone)

## Overview
A fully automated job application system that searches for teaching jobs daily, uses AI to match against your CV, and automatically sends applications with personalized cover letters. Built for Foundation Phase/Special Ed teachers targeting NZ positions.

**🤖 FULLY AUTOMATED - NO MANUAL WORK REQUIRED**

## Features (JobCopilot Clone)

**🔍 Automated Job Discovery:**
- Searches LinkedIn + Seek NZ every few hours automatically
- Uses professional Apify scrapers (not basic web scraping)
- Configurable keywords, location filters, excluded terms
- Cost controls: 10 searches/day, 500 jobs/day max

**🤖 AI-Powered Matching:**
- Claude 3.5 Sonnet analyzes every job against your CV
- 0-100% match scores with detailed reasoning
- Intelligent categorization:
  - 70-100% = EXCELLENT match (green badge) → Auto-apply
  - 50-69% = GOOD match (yellow badge)
  - 0-49% = Lower match (gray badge)

**✍️ Automatic Cover Letter Generation:**
- AI writes personalized cover letters for each job
- Tailored to job description + your experience
- Professional NZ business letter format
- Highlights relevant special needs experience

**📧 Auto-Apply System:**
- Automatically prepares applications for 70%+ matches
- Includes CV + tailored cover letter
- Email-ready application packages
- Tracks application status

**📊 Smart Dashboard:**
- Color-coded job cards (green/yellow/gray)
- Match scores and AI analysis visible
- Application tracking
- Daily usage statistics

**🔒 Security & Reliability:**
- Single-user authentication
- API key management via Replit Secrets
- SQLite database with duplicate prevention
- Error handling and cost controls

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

## How It Works (Fully Automated)

**🚀 Set It and Forget It:**

1. **Configure Your Search** (one-time setup in `job_search_config.py`):
   ```python
   USER_SEARCH_CONFIG = {
       'keywords': ['Foundation Phase Teacher', 'Special Education Teacher'],
       'location': 'New Zealand',
       'platforms': ['linkedin', 'seek'],  # Or just one
       'auto_apply_enabled': True,  # Auto-send applications
       'auto_apply_threshold': 70  # Apply to 70%+ matches
   }
   ```

2. **Click "Auto Search Jobs"** (or run on schedule):
   - System searches LinkedIn + Seek for your keywords
   - Filters out excluded keywords (secondary, high school, etc.)
   - Analyzes each job with Claude AI
   - Calculates 0-100% match scores
   - **AUTOMATICALLY** prepares applications for 70%+ matches

3. **Applications Get Sent:**
   - AI generates personalized cover letter
   - Packages CV + cover letter
   - Prepares email-ready application
   - Updates job status to "ready_to_apply" or "applied"

4. **Review Dashboard:**
   - See all found jobs with match scores
   - View AI analysis and reasoning
   - Track application statuses
   - Check daily usage limits

**NO MANUAL URL PASTING REQUIRED!**

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
- Nov 3, 2025: **COMPLETE AUTOMATION** - Full JobCopilot clone implemented
- Nov 3, 2025: Built cover_letter_generator.py - AI writes personalized cover letters
- Nov 3, 2025: Created auto_apply.py - automatic application submission system
- Nov 3, 2025: Integrated Apify API - professional LinkedIn + Seek scrapers
- Nov 3, 2025: Added cost controls - 10 searches/day, 500 jobs/day max
- Nov 3, 2025: Implemented in-run job tracking - prevents runaway API costs
- Nov 3, 2025: Added auto-apply to workflow - 70%+ matches get applications prepared automatically
- Nov 3, 2025: Updated database schema - added cover_letter and auto_applied fields
- Nov 3, 2025: Configuration system - user controls keywords, platforms, thresholds
- Nov 3, 2025: Removed manual URL paste focus - now fully automated job discovery

## User Preferences
- Single-user system (Foundation Phase teacher seeking NZ positions)
- **Fully automated** - NO manual URL pasting required
- AI-powered job matching with detailed reasoning and 0-100% scores
- **Auto-apply enabled** - applications sent automatically for 70%+ matches
- Personalized cover letters generated by Claude AI
- Clean dashboard with application tracking
- Focus on automation, reliability, and hands-off operation
