from flask import Flask, render_template, request, send_file
import pandas as pd
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return "No file selected"

    file = request.files["file"]

    if file.filename == "":
        return "No file selected"

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(filepath)

    try:
        excel_file = pd.ExcelFile(filepath)

        result = {}

        for sheet in excel_file.sheet_names:
            df = pd.read_excel(filepath, sheet_name=sheet)
            df = df.fillna("")
            result[sheet] = df.to_dict(orient="records")

        json_filename = os.path.splitext(filename)[0] + ".json"
        json_path = os.path.join(app.config["OUTPUT_FOLDER"], json_filename)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4, ensure_ascii=False)

        return render_template(
            "index.html",
            download_ready=True,
            download_file=json_filename
        )

    except Exception as e:
        return f"Error: {str(e)}"


@app.route("/download/<filename>")
def download(filename):
    filepath = os.path.join(app.config["OUTPUT_FOLDER"], filename)
    return send_file(filepath, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)