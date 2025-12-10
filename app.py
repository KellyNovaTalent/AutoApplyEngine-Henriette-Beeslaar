import streamlit as st
import os
import openai
import json
import pandas as pd
import re
import PyPDF2

# === DEBUG: Check if key is loaded ===
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    st.sidebar.success("OpenAI key loaded successfully!")
else:
    st.sidebar.error("No OpenAI key found! Check Secrets in Streamlit Cloud")
    st.stop()

openai.api_key = api_key

st.set_page_config(page_title="AutoApply Engine – Henriette", layout="wide")
st.title("AutoApply Engine – Henriette Beeslaar")
st.markdown("Upload CV + job list → AI generates perfect applications instantly")

with st.sidebar:
    st.header("Upload Files")
    cv_file = st.file_uploader("Henriette's CV (PDF or TXT)", type=["pdf", "txt"])
    jobs_file = st.file_uploader("Job List (CSV/Excel/JSON)", type=["csv", "xlsx", "xls", "json"])

if cv_file and jobs_file:
    # Save files
    cv_path = f"/tmp/{cv_file.name}"
    jobs_path = f"/tmp/{jobs_file.name}"
    with open(cv_path, "wb") as f: f.write(cv_file.getbuffer())
    with open(jobs_path, "wb") as f: f.write(jobs_file.getbuffer())
    st.success("Files uploaded!")

    # Read CV
    if cv_path.endswith(".pdf"):
        reader = PyPDF2.PdfReader(cv_path)
        cv_text = " ".join([p.extract_text() or "" for p in reader.pages])
    else:
        cv_text = open(cv_path, "r", encoding="utf-8").read()

    # Read jobs
    if jobs_path.endswith(".csv"):
        df = pd.read_csv(jobs_path)
    elif jobs_path.endswith(".json"):
        df = pd.read_json(jobs_path)
    else:
        df = pd.read_excel(jobs_path)

    st.write(f"Found **{len(df)} jobs** to process")

    if st.button("Start AI Matching & Application Generation", type="primary"):
        results = []
        progress = st.progress(0)

        for i, row in df.iterrows():
            progress.progress((i + 1) / len(df))
            title = str(row.get("title", row.get("job_title", "N/A")))
            company = str(row.get("company", "N/A"))
            desc = str(row.get("description", row.get("job_description", "")))[:8000]

            prompt = f"""You are an expert career coach. Here is Henriette's full experience:
{cv_text[:12000]}

Job: {title} at {company}
Description: {desc}

Return ONLY valid JSON with these exact keys:
{{"score": 0-100, "letter": "motivation letter max 250 words", "bullets": ["bullet 1", "bullet 2", "bullet 3"]}}
No extra text, no markdown."""

            try:
                response = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    response_format={"type": "json_object"}
                )
                raw = response.choices[0].message.content
                # Clean any junk
                json_str = re.search(r'\{.*\}', raw, re.DOTALL).group(0)
                data = json.loads(json_str)
            except Exception as e:
                data = {"score": "Error", "letter": f"AI failed: {str(e)[:100]}", "bullets": []}

            results.append({
                "Job": title,
                "Company": company,
                "Match Score": data.get("score", "??"),
                "Motivation Letter": data.get("letter", "Not generated"),
                "Why She Fits": " • " + "\n • ".join(data.get("bullets", [])) if data.get("bullets") else "N/A"
            })

        st.success("All applications generated!")
        df_out = pd.DataFrame(results)
        st.dataframe(df_out, use_container_width=True)
        csv = df_out.to_csv(index=False)
        st.download_button("Download All Applications", csv, "henriette_applications.csv", "text/csv")

else:
    st.info("Upload CV and job list to start")

st.caption("Running on Streamlit Community Cloud – 100% free forever")
