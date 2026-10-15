import os
import glob
import json
import datetime
import pdfplumber
import google.generativeai as genai
from pydantic import BaseModel
from typing import List, Optional

# Setup
REPORT_FOLDER = "reports"
DATA_FOLDER = "data"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

class PriceData(BaseModel):
    Platts: Optional[float] = None
    ICIS: Optional[float] = None
    Argus: Optional[float] = None

class CommodityData(BaseModel):
    commodity: str
    prices: PriceData

# We use a simple structure for the free model
def read_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t: text += t + "\n"
    return text

def run():
    pdf_files = glob.glob(os.path.join(REPORT_FOLDER, "*.pdf"))
    if not pdf_files:
        print("No PDFs found!")
        return

    all_data = []
    summaries = []

    model = genai.GenerativeModel('gemini-1.5-flash')

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path}")
        raw_text = read_pdf(pdf_path)[:15000]
        
        prompt = f"""
        Extract petrochemical prices and a summary from this text: {raw_text}
        Return ONLY valid JSON in this format:
        {{
            "market_data": [{{"commodity": "Name", "prices": {{"Platts": 0.0, "ICIS": 0.0, "Argus": 0.0}}}}],
            "summary": "Short summary here"
        }}
        """
        
        response = model.generate_content(prompt)
        # Clean up Gemini's response to get pure JSON
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_json)
        
        all_data.extend(data['market_data'])
        summaries.append(data['summary'])

    output = {
        "report_metadata": {"report_date": datetime.date.today().isoformat()},
        "market_data": all_data,
        "ai_synthesis": {"executive_summary": " | ".join(summaries)}
    }

    os.makedirs(DATA_FOLDER, exist_ok=True)
    with open(f"{DATA_FOLDER}/report_{datetime.date.today().isoformat()}.json", "w") as f:
        json.dump(output, f, indent=2)

# ... inside your run() function, right after the json.dump ...
    print(f"Successfully generated {out_path}")
    
    # ADD THESE TWO LINES TO HELP US DEBUG
    print("Files in current directory:")
    print(os.listdir('.'))
    print(f"Files in data folder: {os.listdir(DATA_FOLDER)}")

if __name__ == "__main__":
    run()
