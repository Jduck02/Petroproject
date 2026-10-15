import os, json, glob, datetime
import google.generativeai as genai
import pdfplumber

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

def run():
    # 1. Find all PDFs
    files = glob.glob("reports/*.pdf")
    if not files: return 

    # 2. Extract text (Simple)
    text = ""
    with pdfplumber.open(files[0]) as pdf:
        text = "".join([p.extract_text() for p in pdf.pages])

    # 3. AI Processing
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(f"Summarize this: {text[:10000]}")
    
    # 4. Save to /data/
    output = {"date": str(datetime.date.today()), "summary": response.text}
    with open(f"data/report_{datetime.date.today()}.json", "w") as f:
        json.dump(output, f)

if __name__ == "__main__": run()
