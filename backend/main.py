import os
import uuid
import pdfplumber
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from openai import OpenAI

app = FastAPI()

# ✅ Handle preflight OPTIONS requests (CORS fix)
@app.options("/{full_path:path}")
async def preflight_handler(full_path: str):
    return JSONResponse(content={"message": "OK"})

# ✅ Allow all origins (safe for demo deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Financial keywords
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
    try:
        all_results = []

        for file in files:
            file_id = str(uuid.uuid4())
            temp_path = f"temp_{file_id}.pdf"

            # Save file
            with open(temp_path, "wb") as f:
                f.write(await file.read())

            # Extract text (NO OCR)
            text = ""
            with pdfplumber.open(temp_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"

            os.remove(temp_path)

            # Filter financial lines
            filtered_lines = [
                line for line in text.split("\n")
                if any(keyword.lower() in line.lower() for keyword in KEYWORDS)
            ]

            filtered_text = "\n".join(filtered_lines)

            if not filtered_text.strip():
                filtered_text = "No financial keywords detected."

            # OpenAI structuring
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract financial line items and numeric values. Return structured clean JSON."
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

        # Create Excel file
        df = pd.DataFrame(all_results)
        output_file = "financial_output.xlsx"
        df.to_excel(output_file, index=False)

        return FileResponse(
            output_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="financial_output.xlsx"
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
