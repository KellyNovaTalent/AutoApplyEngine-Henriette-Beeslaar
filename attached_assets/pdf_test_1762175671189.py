import requests
from io import BytesIO
from PyPDF2 import PdfReader

pdf_url = "https://gazette-live-storagestack-17-assetstorages3bucket-1571qjbkpxwcd.s3.ap-southeast-2.amazonaws.com/public/Uploads/Learning-Support-Co-ordinator-Job-Description-v9.pdf"

r = requests.get(pdf_url, timeout=30)
pdf = PdfReader(BytesIO(r.content))

for i, page in enumerate(pdf.pages, start=1):
    text = page.extract_text()
    print(f"\n--- Page {i} ---")
    print(text if text else "[NO TEXT FOUND]")
