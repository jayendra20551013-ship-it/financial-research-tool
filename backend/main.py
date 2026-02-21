import os
import uuid
import pdfplumber
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from openai import OpenAI

app = FastAPI()

# ✅ IMPORTANT: Allow only your Vercel frontend
origins = [
    "https://financial-research-tool-five.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI Client
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

    all_results = []

    for file in files:
        file_id = str(uuid.uuid4())
        temp_path = f"temp_{file_id}.pdf"

        # Save file temporarily
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # Extract text (NO OCR → low memory)
        text = ""
        with pdfplumber.open(temp_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        os.remove(temp_path)

        # Filter lines with financial keywords
        filtered_lines = [
            line for line in text.split("\n")
            if any(keyword.lower() in line.lower() for keyword in KEYWORDS)
        ]

        filtered_text = "\n".join(filtered_lines)

        # Ask OpenAI to structure output
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Extract financial line items and their numeric values. Return clean structured JSON."
                },
                {
                    "role": "user",
                    "content": filtered_text
                }
            ]
        )

        structured_output = response.choices[0].message.content

        all_results.append({
            "filename": file.filename,
            "extracted_data": structured_output
        })

    # Create Excel
    df = pd.DataFrame(all_results)

    output_file = "financial_output.xlsx"
    df.to_excel(output_file, index=False)

    return FileResponse(
        output_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="financial_output.xlsx"
    )
