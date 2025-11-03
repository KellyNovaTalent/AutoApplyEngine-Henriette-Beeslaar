@echo off
REM --- Daily Seek scrape + Google Sheets upload ---
cd /d "C:\Users\sam\OneDrive\Documents\Job Scraper"
set HEADLESS=1
set PYTHONIOENCODING=utf-8
"C:\Users\sam\AppData\Local\Programs\Python\Python312\python.exe" run_daily_seek.py >> daily_run.log 2>&1
