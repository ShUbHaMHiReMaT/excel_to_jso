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
        return "No file uploaded structure received.", 400

    file = request.files["file"]

    if file.filename == "":
        return "No file selected.", 400

    try:
        # Read file cleanly directly into RAM buffer
        file_bytes = file.read()
        file_stream = io.BytesIO(file_bytes)
        
        result = {}
        
        # Parse Excel via ultra-fast Rust calamine engine
        with pd.ExcelFile(file_stream, engine="calamine") as xls:
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                
                # 1. Strip out rows and columns that are entirely blank
                df = df.dropna(how="all")
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')] # drop unnamed blank columns
                
                if df.empty:
                    continue

                # 2. Advanced data cleanup for mobile JSON compatibility
                # Standardize data types, convert timestamps/dates cleanly to strings, match JSON nulls
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S').fillna("")
                
                # Turn remaining NaN/Nat elements into native None tokens
                df = df.astype(object).where(pd.notnull(df), None)
                
                # Convert the individual sheet to records layout
                result[sheet_name] = df.to_dict(orient="records")

        # Fallback if the excel file ended up completely empty
        if not result:
            return "The uploaded file contains no valid sheet data.", 400

        # Stringify dataset cleanly to UTF-8
        json_data = json.dumps(result, indent=4, default=str)
        
        return_stream = io.BytesIO()
        return_stream.write(json_data.encode("utf-8"))
        return_stream.seek(0)

        return send_file(
            return_stream,
            mimetype="application/json",
            as_attachment=True,
            download_name="converted_data.json"
        )

    except Exception as e:
        # Returns a clear clean string error message for our frontend Javascript catch block
        return f"Conversion failed: {str(e)}", 500

if __name__ == "__main__":
    app.run()