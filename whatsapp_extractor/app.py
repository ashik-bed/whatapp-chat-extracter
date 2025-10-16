import os
import re
import pandas as pd
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def parse_whatsapp_chat(file_path, start_date=None, end_date=None, filter_sender=None):
    pattern = r"^(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2})[  ]?(AM|PM|am|pm)? - (.*?): (.*)"
    messages = []

    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.replace('\u202f', ' ').replace('\xa0', ' ').strip()
            match = re.match(pattern, line)
            if match:
                date_str, time, am_pm, sender, message = match.groups()
                full_time = time + (' ' + am_pm if am_pm else '')
                for fmt in ("%d/%m/%Y", "%d/%m/%y"):
                    try:
                        full_date = datetime.strptime(date_str, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    continue

                if (start_date and full_date < start_date) or (end_date and full_date > end_date):
                    continue

                if filter_sender and sender.strip().lower() != filter_sender.strip().lower():
                    continue

                messages.append([full_date.strftime('%d/%m/%Y'), full_time, sender, message])
            elif messages:
                messages[-1][3] += '\n' + line.strip()

    return pd.DataFrame(messages, columns=["Date", "Time", "Sender", "Message"])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['chatfile']
    if not file:
        return "No file uploaded", 400

    start = request.form.get("start_date")
    end = request.form.get("end_date")
    sender = request.form.get("sender")

    start_date = datetime.strptime(start, "%Y-%m-%d") if start else None
    end_date = datetime.strptime(end, "%Y-%m-%d") if end else None

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    df = parse_whatsapp_chat(file_path, start_date, end_date, sender)
    df.to_excel(os.path.join(UPLOAD_FOLDER, "parsed_chat.xlsx"), index=False)

    summary = df["Sender"].value_counts().reset_index()
    summary.columns = ["Sender", "Message Count"]

    return render_template("result.html",
                           tables=df.to_html(classes='table table-sm table-bordered', index=False),
                           summary=summary.to_html(classes='table table-sm table-striped', index=False),
                           download=True)


@app.route('/download')
def download():
    return send_file(os.path.join(UPLOAD_FOLDER, "parsed_chat.xlsx"), as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
