🌊 Marine Debris Dashboard

An AI-based dashboard for detecting marine debris, recording detection data, identifying debris hotspots, and visualizing the results on a web interface.

Features

- 🤖 YOLO26-based debris detection
- 🗑️ Detects bottle, plastic, metal, glass, and other waste
- 📍 GPS-based location tagging
- 🕒 Timestamped detection records
- 🗺️ Debris hotspot visualization
- 📊 Detection statistics and historical data
- 🧠 Local AI-assisted hotspot analysis using Ollama
- 🌐 Interactive web dashboard

How It Works

Camera
   ↓
YOLO26 Detection
   ↓
GPS + Timestamp
   ↓
Database
   ↓
Hotspot Analysis
   ↓
Ollama AI Analysis
   ↓
Dashboard

Project Structure

marine-debris-dashboard/
│
├── app.py
├── requirements.txt
├── model/
│   └── best.onnx
│
├── database/
│   └── schema.sql
│
├── backend/
├── frontend/
└── README.md

Detection Model

The dashboard uses a trained YOLO26n model.

Classes

Bottle
Plastic
Metal
Glass
Other

Model Performance

Metric| Value
Precision| 0.590
Recall| 0.608
mAP@50| 0.545
mAP@50-95| 0.421

Requirements

- Python 3.10+
- Ultralytics / YOLO
- OpenCV
- ONNX Runtime
- Streamlit
- PostgreSQL
- Ollama

Install dependencies:

pip install -r requirements.txt

Run Locally

streamlit run app.py

The dashboard will open in your browser.

Database

The dashboard can use PostgreSQL to store detection records.

Configure the database using the "DATABASE_URL" environment variable:

DATABASE_URL=<your-postgresql-connection-string>

Initialize the database using:

database/schema.sql

Never commit database credentials, API keys, or other secrets to GitHub.

Ollama

Ollama provides local AI-assisted analysis of debris hotspots.

The analysis can consider:

- Debris count
- Debris categories
- Historical detection data
- Changes in hotspot activity

The AI model runs locally through Ollama.

Deployment

The dashboard can be deployed using Streamlit Community Cloud.

1. Push the project to GitHub.
2. Create a Streamlit app.
3. Select the repository and "app.py".
4. Add required environment variables through Streamlit Secrets.
5. Deploy.

Database credentials should be stored only in the deployment secrets and not in the GitHub repository.

Dataset

The detection model was trained using a combined dataset derived from:

- BEPLI
- TACO
- FloW

The datasets were unified into a common five-class label structure.

