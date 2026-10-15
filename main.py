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
    # ADDED LOGGING
    print("Current working directory:", os.getcwd())
    print("Listing files in current directory:", os.listdir('.'))
    
    if os.path.exists(REPORT_FOLDER):
        files_in_reports = os.listdir(REPORT_FOLDER)
        print(f"Files found in {REPORT_FOLDER}: {files_in_reports}")
    else:
        print(f"ERROR: The folder {REPORT_FOLDER} does not exist!")
        return

    pdf_files = glob.glob(os.path.join(REPORT_FOLDER, "*.pdf"))
    if not pdf_files:
        print("No PDFs found matching *.pdf")
        return
    # ... (rest of your existing code)

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

# Change the output path to be absolutely sure it's in the /data folder
    # We use 'os.getcwd()' to tell the computer exactly where to save it
    base_path = os.getcwd()
    output_dir = os.path.join(base_path, "data")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"report_{datetime.date.today().isoformat()}.json"
    out_path = os.path.join(output_dir, filename)
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

# ... inside your run() function, right after the json.dump ...
    print(f"Successfully generated {out_path}")
    
    # ADD THESE TWO LINES TO HELP US DEBUG
    print("Files in current directory:")
    print(os.listdir('.'))
    print(f"Files in data folder: {os.listdir(DATA_FOLDER)}")

if __name__ == "__main__":
    run()
