from flask import Flask, render_template, request, send_file
from cryptography.fernet import Fernet
import os
import uuid
import time

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load secret key
with open("secret.key", "rb") as key_file:
    key = key_file.read()

fernet = Fernet(key)

# Store file mapping with timestamp
file_mapping = {}

# Expiry time (5 minutes = 300 seconds)
EXPIRY_TIME = 300

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]

    if file:
        file_data = file.read()
        encrypted_data = fernet.encrypt(file_data)

        unique_id = str(uuid.uuid4())
        encrypted_filename = unique_id + ".enc"

        file_path = os.path.join(UPLOAD_FOLDER, encrypted_filename)

        with open(file_path, "wb") as f:
            f.write(encrypted_data)

        # Store original filename + timestamp
        file_mapping[unique_id] = {
            "filename": file.filename,
            "timestamp": time.time()
        }

        return f"""
        File uploaded securely!<br>
        This link will expire in 5 minutes.<br><br>
        <a href="/download/{unique_id}">Download File</a>
        """

    return "No file selected"


@app.route("/download/<file_id>")
def download_file(file_id):

    if file_id in file_mapping:

        file_info = file_mapping[file_id]
        upload_time = file_info["timestamp"]

        # Check expiry
        if time.time() - upload_time > EXPIRY_TIME:
            del file_mapping[file_id]
            return "Link expired."

        encrypted_path = os.path.join(UPLOAD_FOLDER, file_id + ".enc")

        if os.path.exists(encrypted_path):

            with open(encrypted_path, "rb") as f:
                encrypted_data = f.read()

            decrypted_data = fernet.decrypt(encrypted_data)

            original_filename = file_info["filename"]

            decrypted_path = os.path.join(UPLOAD_FOLDER, original_filename)

            with open(decrypted_path, "wb") as f:
                f.write(decrypted_data)

            # Delete encrypted file (one-time download)
            os.remove(encrypted_path)
            del file_mapping[file_id]

            return send_file(decrypted_path, as_attachment=True)

    return "File not found or already downloaded."


if __name__ == "__main__":
    app.run(debug=False)
