FACE ATTENDANCE SERVICE (FastAPI + Offline Face Recognition)
==========================================================

What you get
- FastAPI backend (enroll, identify, attendance mark)
- SQLite database auto-created in: data/attendance.db
- Simple HTML dashboard in: Frontend/index.html (optional)

Requirements
- Python 3.9–3.11 (recommended 3.10)
- OS: Windows/macOS/Linux
- Webcam (for live attendance)

Quick Start (Recommended)
1) Open terminal in project folder
2) Create and activate a virtual environment

   Windows (PowerShell):
     python -m venv venv
     .\venv\Scripts\Activate.ps1

   macOS / Linux:
     python3 -m venv venv
     source venv/bin/activate

3) Install packages
     pip install -r requirements.txt

4) Start backend
     python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

5) Open API docs
     http://127.0.0.1:8000/docs

Optional: Start the HTML dashboard
- In a NEW terminal:
     cd Frontend
     python -m http.server 5500
- Open in browser:
     http://localhost:5500

Network Access (for CodeIgniter integration)
- Find your LAN IP:
     macOS: ipconfig getifaddr en0
- Share:
     IP: <your-ip>
     Port: 8000
- Backend must be started with host 0.0.0.0 (already shown above).

Notes
- On first run, folders are created automatically:
  uploads/ and data/
- If you want a fresh start, delete:
  data/attendance.db and data/encodings.pkl (if present).
