import streamlit as st
import os
import json
import pandas as pd
import re
import PyPDF2
from openai import OpenAI

# Set page config FIRST
st.set_page_config(page_title="AutoApply Engine – Henriette Beeslaar", layout="wide")

# Load key and create client (new SDK style to avoid proxies error)
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key)
    st.sidebar.success("✅ OpenAI key loaded!")
else:
    st.sidebar.error("❌ No OpenAI key found! Check Secrets in Streamlit Cloud")
    st.stop()

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

    # Read CV text
    if cv_path.endswith(".pdf"):
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

                Respond in JSON format only: {{"score": number, "letter": "text", "bullets": ["bullet1", "bullet2", "bullet3"]}}
                """

                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        response_format={"type": "json_object"}
                    )
                    content = response.choices[0].message.content

                    # Clean JSON
                    content = re.sub(r'```json\s*|\s*```', '', content).strip()
                    data = json.loads(content)
                except Exception as e:
                    st.error(f"API Error for job {idx}: {str(e)[:200]}")  # Show exact error for debug
                    data = {"score": "Error", "letter": "AI failed", "bullets": []}

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

st.caption("Running on Streamlit Cloud – 100% free, no Replit costs")
