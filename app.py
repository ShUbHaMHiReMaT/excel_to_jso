from flask import Flask, render_template, request, send_file
import pandas as pd
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
        # Read file directly from stream into memory
        file_bytes = file.read()
        file_stream = io.BytesIO(file_bytes)
        
        result = {}
        
        # Fast Rust-backed calamine parsing engine
        with pd.ExcelFile(file_stream, engine="calamine") as xls:
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                df = df.dropna(how="all") # drop empty rows
                
                # Turn NaN / null items cleanly into JSON-friendly null values
                df = df.astype(object).where(pd.notnull(df), None)
                
                result[sheet_name] = df.to_dict(orient="records")

        # Convert dictionary data to JSON string in memory
        json_data = json.dumps(result, indent=4, default=str)
        
        return_stream = io.BytesIO()
        return_stream.write(json_data.encode("utf-8"))
        return_stream.seek(0)

        # Added download_name explicitly so Flask can handle the byte stream download cleanly
        return send_file(
            return_stream,
            mimetype="application/json",
            as_attachment=True,
            download_name="converted_data.json"
        )

    except Exception as e:
        return f"Conversion error: {str(e)}", 500

if __name__ == "__main__":
    app.run()