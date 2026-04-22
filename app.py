from flask import Flask, render_template, request, send_from_directory
import cv2
import os
import smtplib
import uuid
from email.message import EmailMessage

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# ---------------- EMAIL FUNCTION ----------------
def send_email(receiver_email, filename):
    msg = EmailMessage()
    msg['Subject'] = 'Your Processed File'
    msg['From'] = 'ashmitgarg104@gmail.com'   
    msg['To'] = receiver_email

    link = f"http://127.0.0.1:5000/download/{filename}"
    msg.set_content(f"Download your processed file:\n{link}")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login('ashmitgarg104@gmail.com', 'kfdd llmj yroe dpdn')  
        smtp.send_message(msg)

# ---------------- HOME ----------------
@app.route('/')
def index():
    return render_template('index.html')

# ---------------- PROCESS ----------------
@app.route('/process', methods=['POST'])
def process():
    file = request.files['image']
    resize_percent = int(request.form['resize'])
    bw = 'bw' in request.form
    email = request.form['email']

    # Unique names
    unique_id = str(uuid.uuid4())[:8]
    filename = file.filename.lower()

    input_path = os.path.join(UPLOAD_FOLDER, f"input_{unique_id}_{filename}")

    # Save file
    file.save(input_path)

    # ---------------- IMAGE PROCESSING ----------------
    if filename.endswith(('.jpg', '.jpeg', '.png')):

        img = cv2.imread(input_path)

        # Resize
        width = int(img.shape[1] * resize_percent / 100)
        height = int(img.shape[0] * resize_percent / 100)
        img = cv2.resize(img, (width, height))

        # B/W
        if bw:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        output_filename = f"output_{unique_id}.jpg"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        cv2.imwrite(output_path, img)

    # ---------------- VIDEO PROCESSING ----------------
    elif filename.endswith(('.mp4', '.avi', '.mov')):

        cap = cv2.VideoCapture(input_path)

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        new_width = int(width * resize_percent / 100)
        new_height = int(height * resize_percent / 100)

        output_filename = f"output_{unique_id}.mp4"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)

        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(output_path, fourcc, fps, (new_width, new_height))

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.resize(frame, (new_width, new_height))

            if bw:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            out.write(frame)

        cap.release()
        out.release()

    else:
        return "❌ Unsupported file format"

    # Send email
    send_email(email, output_filename)

    return "✅ File processed! Check your email."

# ---------------- DOWNLOAD ----------------
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)