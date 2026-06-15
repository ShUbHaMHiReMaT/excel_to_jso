from flask import Flask, render_template, request, send_file
from openpyxl import load_workbook
import json
import io

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return "No file uploaded", 400

    file = request.files["file"]

    if file.filename == "":
        return "No file selected", 400

    try:
        # Read file directly from stream
        file_stream = io.BytesIO(file.read())
        workbook = load_workbook(file_stream, data_only=True)
        
        result = {}
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            rows = list(sheet.values)

            if not rows:
                continue

            headers = rows[0]
            data = []

            for row in rows[1:]:
                item = {}
                for header, value in zip(headers, row):
                    if header is not None:
                        item[str(header)] = value
                data.append(item)

            result[sheet_name] = data

        # Write to memory stream
        json_data = json.dumps(result, indent=4, default=str)
        return_stream = io.BytesIO()
        return_stream.write(json_data.encode("utf-8"))
        return_stream.seek(0)

        return send_file(
            return_stream,
            mimetype="application/json",
            as_attachment=True
        )

    except Exception as e:
        return f"Conversion error: {str(e)}", 500

if __name__ == "__main__":
    app.run()