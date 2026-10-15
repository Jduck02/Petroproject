import os
import glob
import json
import datetime
import pdfplumber
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI

REPORT_FOLDER = "reports"
DATA_FOLDER = "data"

# Setup schema
class PriceData(BaseModel):
    Platts: Optional[float] = None
    ICIS: Optional[float] = None
    Argus: Optional[float] = None

class CommodityData(BaseModel):
    commodity: str
    prices: PriceData

class PetrochemicalReport(BaseModel):
    market_data: List[CommodityData]
    executive_summary: str

def get_latest_pdf():
    files = glob.glob(f"{REPORT_FOLDER}/*.pdf")
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def read_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return text

def run():
    pdf_path = get_latest_pdf()
    if not pdf_path:
        print("No PDF found in reports/ folder!")
        return

    print(f"Reading: {pdf_path}")
    raw_text = read_pdf(pdf_path)

    # Cut off text if it's too long (keep first ~15,000 chars to avoid hitting token limits)
    raw_text = raw_text[:15000]

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a petrochemical analyst. Extract commodity prices (Platts, ICIS, Argus) and write a concise market executive summary."
            },
            {
                "role": "user",
                "content": f"Extract market data from this report:\n{raw_text}"
            }
        ],
        response_format=PetrochemicalReport,
    )

    parsed = completion.choices[0].message.parsed

    today = datetime.date.today().isoformat()
    output = {
        "report_metadata": {"report_date": today},
        "market_data": [item.dict() for item in parsed.market_data],
        "ai_synthesis": {"executive_summary": parsed.executive_summary}
    }

    os.makedirs(DATA_FOLDER, exist_ok=True)
    out_path = f"{DATA_FOLDER}/report_{today}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Successfully generated {out_path}")

if __name__ == "__main__":
    run()
