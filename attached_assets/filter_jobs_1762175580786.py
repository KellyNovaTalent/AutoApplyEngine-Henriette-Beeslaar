import pandas as pd

# Load the full scraped jobs
jobs = pd.read_csv("millicent_jobs.csv")

# Define keywords relevant to Millicent’s CV
keywords = [
    "ECE", "early childhood", "kindergarten", "kaiako", 
    "preschool", "centre manager", "head teacher"
]

def matches(job_title, job_description):
    text = f"{job_title} {job_description}".lower()
    return any(kw.lower() in text for kw in keywords)

# Filter
filtered = jobs[jobs.apply(lambda row: matches(row["Title"], row.get("Description", "")), axis=1)]

print(f"✅ Found {len(filtered)} matching jobs for Millicent")

# Save to new CSV
filtered.to_csv("millicent_jobs_filtered.csv", index=False, encoding="utf-8")
print("✅ Saved matching jobs into millicent_jobs_filtered.csv")
