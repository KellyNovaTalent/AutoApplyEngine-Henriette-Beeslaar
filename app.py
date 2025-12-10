import streamlit as st
import os
import openai
from dotenv import load_dotenv
import json
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="AutoApply Engine – Henriette Beeslaar", layout="wide")
st.title("AutoApply Engine – Henriette Beeslaar")
st.markdown("Upload your CV and the job list → AI matches & generates tailored applications instantly")

# Sidebar
with st.sidebar:
    st.header("Upload Files")
    cv_file = st.file_uploader("Upload Henriette's CV (PDF or TXT)", type=["pdf", "txt"])
    jobs_file = st.file_uploader("Upload Job List (CSV, JSON or Excel)", type=["csv", "json", "xlsx", "xls"])

# Main area
if cv_file and jobs_file:
    # Save files temporarily
    cv_path = f"/tmp/{cv_file.name}"
    jobs_path = f"/tmp/{jobs_file.name}"
    
    with open(cv_path, "wb") as f:
        f.write(cv_file.getbuffer())
    with open(jobs_path, "wb") as f:
        f.write(jobs_file.getbuffer())

    st.success("Files uploaded successfully!")

    # Read CV text (simple extraction)
    if cv_path.endswith(".pdf"):
        import PyPDF2
        with open(cv_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            cv_text = " ".join([page.extract_text() or "" for page in reader.pages])
    else:
        with open(cv_path, "r", encoding="utf-8") as f:
            cv_text = f.read()

    # Read jobs
    if jobs_path.endswith(".csv"):
        jobs_df = pd.read_csv(jobs_path)
    elif jobs_path.endswith(".json"):
        jobs_df = pd.read_json(jobs_path)
    else:
        jobs_df = pd.read_excel(jobs_path)

    st.write(f"Found **{len(jobs_df)} jobs** to analyze")

    if st.button("Start AI Matching & Application Generation"):
        with st.spinner("AI is analyzing jobs and writing applications..."):
            results = []
            progress_bar = st.progress(0)

            for idx, row in jobs_df.iterrows():
                progress_bar.progress((idx + 1) / len(jobs_df))

                job_title = row.get("title", "N/A")
                company = row.get("company", "N/A")
                description = str(row.get("description", row.get("job_description", "")))[:5000]

                prompt = f"""
                You are an expert career coach. Henriette Beeslaar has this experience:
                {cv_text[:8000]}

                Job: {job_title} at {company}
                Description: {description}

                1. Give a match score 0–100
                2. Write a short, powerful motivation letter (max 250 words) tailored to this job
                3. List 3 bullet points of why she is a perfect fit

                Respond in JSON format only.
                """

                try:
                    response = openai.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7
                    )
                    result = response.choices[0].message.content
                    data = json.loads(result)
                except:
                    data = {"score": "Error", "letter": "AI error", "bullets": []}

                results.append({
                    "Job": job_title,
                    "Company": company,
                    "Match Score": data.get("score", "??"),
                    "Motivation Letter": data.get("letter", "Not generated"),
                    "Why She Fits": " • " + "\n • ".join(data.get("bullets", [])) if data.get("bullets") else "N/A"
                })

            st.success("All applications generated!")
            results_df = pd.DataFrame(results)
            st.dataframe(results_df, use_container_width=True)

            # Download button
            csv = results_df.to_csv(index=False)
            st.download_button("Download All Applications (CSV)", csv, "applications.csv", "text/csv")

else:
    st.info("Please upload Henriette's CV and your scraped job list to begin.")

st.caption("Running on Render free tier – 100% free, no Replit costs")
