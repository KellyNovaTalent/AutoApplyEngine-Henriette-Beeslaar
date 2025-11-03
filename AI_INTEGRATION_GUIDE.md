# AI Job Matching Integration Guide

## Overview
The system now uses Claude AI (Anthropic) to automatically analyze every job posting and provide a match score based on your CV and preferences.

## How It Works

### Automatic Analysis
1. When new job alerts are synced from Gmail
2. Each job (except auto-rejected ones) is sent to Claude AI
3. Claude analyzes the job against your profile and assigns a score (0-100%)
4. The analysis and score are stored in the database

### Scoring Criteria
Claude evaluates jobs based on:
- **Location Match (0-30 points)**: Is it in New Zealand?
- **Role Match (0-30 points)**: Foundation Phase/Primary/Special Education?
- **Experience Level (0-20 points)**: Suitable for 18+ years experience?
- **Specialization Match (0-20 points)**: Special needs, learning support?

### Match Score Interpretation
- **70-100%**: EXCELLENT match - Highly recommended
- **50-69%**: GOOD match - Worth considering
- **0-49%**: Lower match - May not be ideal

## What the AI Knows About You

Your profile includes:
- 18+ years teaching experience
- Foundation Phase specialist (Grades R-3)
- Special Educational Needs expert
- NZ Teaching Registration
- Qualifications: B.Ed Foundation Phase
- Specializations: Autism, Down Syndrome, ADHD, learning disabilities
- Preferred location: New Zealand
- Bilingual: English and Afrikaans

## AI Analysis Display

On the dashboard, you'll see:
1. **Color-coded match badges**:
   - Green (70%+): EXCELLENT match
   - Yellow (50-69%): GOOD match
   - Gray (<50%): Lower match

2. **AI Analysis**: Brief explanation of why the job received that score

## Privacy & Cost

- Your CV summary is sent to Claude AI for analysis
- Only job details from emails are analyzed
- The system uses Claude 3.5 Sonnet for fast, accurate analysis
- Each job analysis costs approximately $0.001-0.002

## Turning Off AI Analysis

If you want to disable AI analysis:
1. Remove the `ANTHROPIC_API_KEY` from your secrets
2. The system will continue working but won't analyze jobs
3. Match scores will be set to 0

## API Key Setup

Your Claude API key should be:
- Added to Replit Secrets as `ANTHROPIC_API_KEY`
- Keep it private and never share it
- Get your key from: https://console.anthropic.com/

## Customizing the Analysis

To adjust what the AI looks for, edit `cv_profile.py`:
- Update `CV_SUMMARY` with your latest experience
- Modify `JOB_PREFERENCES` to change target criteria
- Adjust `ideal_roles` or `preferred_specializations` lists
