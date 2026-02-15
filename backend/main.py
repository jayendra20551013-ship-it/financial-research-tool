import re
import io
import pytesseract
import pandas as pd

from typing import List
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pdf2image import convert_from_bytes
from PyPDF2 import PdfReader

# ----------------------------
# CREATE FASTAPI APP
# ----------------------------
app = FastAPI(title="Financial Research Tool API")

# ----------------------------
# ENABLE CORS (important for frontend)
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# FINANCIAL KEYWORDS LIST
# ----------------------------
FINANCIAL_KEYWORDS = [
    "Revenue", "Net Revenue", "Sales",
    "Profit", "Net Profit", "Loss",
    "EBITDA", "Operating Income",
    "Expenses", "Total Assets",
    "Total Liabilities", "Equity",
    "Cash Flow", "Gross Profit"
]

# ----------------------------
# ROOT ROUTE
# ----------------------------
@app.get("/")
def home():
    return {"message": "Financial Research Tool Backend Running 🚀"}

# ----------------------------
# DOCUMENT UPLOAD + RESEARCH TOOL
# ----------------------------
@app.post("/extract")
async def extract_documents(files: List[UploadFile] = File(...)):

    all_results = []

    for file in files:
        contents = await file.read()
        text = ""

        # -------- NORMAL PDF TEXT EXTRACTION --------
        try:
            reader = PdfReader(io.BytesIO(contents))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except:
            pass

        # -------- OCR FALLBACK --------
        if len(text.strip()) < 50:
            try:
                images = convert_from_bytes(contents)
                for img in images:
                    text += pytesseract.image_to_string(img)
            except:
                pass

        # -------- KEYWORD EXTRACTION --------
        file_data = []

        for keyword in FINANCIAL_KEYWORDS:
            pattern = rf"{keyword}\s*[:\-]?\s*([\d,]+)"
            matches = re.findall(pattern, text, re.IGNORECASE)

            if matches:
                for value in matches:
                    file_data.append({
                        "keyword": keyword,
                        "value": value
                    })

        # -------- HANDLE MISSING DATA --------
        if not file_data:
            file_data.append({
                "keyword": "No financial keywords found",
                "value": "N/A"
            })

        all_results.append({
            "file_name": file.filename,
            "extracted_data": file_data
        })

    # -------- CLEAN STRUCTURED RESPONSE --------
    return {
        "status": "success",
        "total_files_processed": len(files),
        "results": all_results
    }
