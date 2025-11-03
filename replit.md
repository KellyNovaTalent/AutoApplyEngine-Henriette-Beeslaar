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

**📧 Smart Application System:**
- Automatically prepares applications for 70%+ matches
- Includes CV + tailored cover letter (saved as PDFs)
- Sends via Gmail when contact email available
- Otherwise marks "ready_to_apply" with cover letter attached
- Tracks application status (applied/ready/pending)

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
- **Email**: Gmail API (automated sending)
- **AI**: Claude 3.5 Sonnet (Anthropic API)
- **Job Search**: Apify API (LinkedIn + Seek scrapers)
- **Frontend**: HTML, Tailwind CSS
- **Scheduler**: APScheduler (3-hour auto-search intervals)
- **PDF Generation**: fpdf2 (cover letters)

## Project Structure
```
├── app.py                      # Flask app with auto-search endpoint + scheduler
├── database.py                 # SQLite database operations
├── job_fetcher_apify.py        # Apify API integration (LinkedIn + Seek)
├── ai_matcher.py               # Claude AI job matching (0-100% scores)
├── cover_letter_generator.py  # AI-powered cover letter generation
├── cover_letter_pdf.py         # PDF generation with Unicode handling
├── auto_apply.py               # Auto-application system (70%+ matches)
├── email_sender.py             # Gmail API email sending
├── gmail_service.py            # Gmail OAuth authentication
├── job_search_config.py        # User search configuration
├── apify_cost_tracker.py       # Daily usage limits (10 searches, 500 jobs)
├── cv_profile.py               # User CV profile (Henriëtte Beeslaar)
├── templates/
│   ├── login.html             # Login page
│   └── index.html             # JobCopilot dashboard with auto-search
├── requirements.txt            # Python dependencies
├── cover_letters/             # Generated cover letter PDFs
└── jobs.db                    # SQLite database (auto-created)
```

## Required Secrets (in Replit Secrets)
1. **SECRET_KEY**: Flask session security key
2. **AUTH_PASSWORD**: Dashboard login password  
3. **ANTHROPIC_API_KEY**: Claude AI API key for job matching and cover letters
4. **APIFY_API_KEY**: Apify API key for LinkedIn + Seek job scraping
5. **Gmail Integration**: Configured via Replit Connectors (OAuth)

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

3. **Smart Application Handling:**
   - AI generates personalized cover letter (saved as PDF)
   - Packages CV + cover letter
   - **IF** contact email found: Sends application via Gmail → Status: "applied"
   - **IF** no email: Saves application docs → Status: "ready_to_apply" 
   - User applies manually at job portal with AI-generated materials

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
- **Preferred Roles**: Foundation Phase (Grades R-3), Primary School (Junior Primary), ECD/Early Childhood, New Entrant Teacher
- **Excluded Roles**: Secondary/Intermediate/Senior Phase (Grades 4+), Administrative positions
- **Languages**: English and Afrikaans

## Recent Changes
- Nov 3, 2025: Updated job search keywords - Focus ONLY on Foundation Phase (Grades R-3) and Junior Primary positions
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
