from flask import Flask, render_template, request, send_file
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

import fitz  # PyMuPDF
import pandas as pd
import io
import os
import re


app = Flask(__name__)

def extract_text_from_pdf(pdf_file):
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()
    # print("Extracted Text:\n", text[:1000])  # Show a sample
    return text


def parse_transactions(text):
    credit_data = []
    debit_data = []

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect date
        if re.match(r'\w{3} \d{2}, \d{4}', line):  # Example: Apr 02, 2025
            try:
                date = line
                time = lines[i+1].strip()
                type_ = lines[i+2].strip()
                amount_line = lines[i+3].strip()
                details = lines[i+4].strip()

                # Extract amount (₹ sign may cause issues if not handled)
                amount = re.sub(r'[^\d.]', '', amount_line)

                transaction = [f"{date} {time}", details, amount]

                if "CREDIT" in type_:
                    credit_data.append(transaction)
                elif "DEBIT" in type_:
                    debit_data.append(transaction)

                i += 6  # Skip ahead to next block
            except IndexError:
                i += 1
        else:
            i += 1

    print("Parsed Credit:", credit_data[:2])
    print("Parsed Debit:", debit_data[:2])
    return credit_data, debit_data


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    text = extract_text_from_pdf(file)
    credit_data, debit_data = parse_transactions(text)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        if credit_data:
            pd.DataFrame(credit_data, columns=["Date", "Description", "Amount"]).to_excel(writer, sheet_name="Credit", index=False)
        if debit_data:
            pd.DataFrame(debit_data, columns=["Date", "Description", "Amount"]).to_excel(writer, sheet_name="Debit", index=False)
        writer.close()
    
    output.seek(0)
    return send_file(output, as_attachment=True, download_name="Transaction_Report.xlsx", mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == "__main__":
    app.run(debug=True)
