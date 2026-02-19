import os
import uuid
import pdfplumber
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Financial Keywords
KEYWORDS = [
    "revenue", "profit", "loss", "income", "expenses",
    "assets", "liabilities", "equity", "cash flow",
    "operating income", "net income", "gross profit",
    "ebitda", "tax", "debt"
]


@app.get("/")
def home():
    return {"status": "Financial Research Tool Backend Running"}


@app.post("/extract")
async def extract(files: list[UploadFile] = File(...)):
    results = []

    for file in files:
        file_id = str(uuid.uuid4())
        file_path = f"temp_{file_id}.pdf"

        # Save uploaded file
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # Extract text using pdfplumber (NO OCR)
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

        os.remove(file_path)

        # Filter text for financial keywords
        filtered_text = "\n".join(
            [line for line in text.split("\n")
             if any(keyword.lower() in line.lower() for keyword in KEYWORDS)]
        )

        # Ask OpenAI to structure data
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract financial line items and numbers into structured JSON."},
                {"role": "user", "content": filtered_text}
            ]
        )

        structured_data = response.choices[0].message.content

        results.append({
            "filename": file.filename,
            "extracted_data": structured_data
        })

    # Convert to DataFrame
    df = pd.DataFrame(results)

    o
