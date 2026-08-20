# PotholeVision 🕳️🔍

**Real-Time Computer Vision Pothole Detection, Monocular Depth Estimation, and 2D/3D Blueprint Analysis System.**

A full-stack application with a **React frontend** (Vercel) and **Flask API backend** (Render).

---

## 📁 Project Structure

```
RealTime/
├── frontend/          ← React + Vite (deploy to Vercel)
│   ├── src/
│   ├── package.json
│   └── vercel.json
│
├── backend/           ← Flask REST API (deploy to Render)
│   ├── app.py         ← Flask API server
│   ├── main.py        ← Desktop OpenCV HUD (local only)
│   ├── config.py
│   ├── requirements.txt
│   ├── Procfile
│   ├── render.yaml
│   ├── detection/
│   ├── depth/
│   ├── analysis/
│   ├── visualization/
│   └── utils/
│
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start (Local Development)

### Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
# API runs on http://localhost:5000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# App runs on http://localhost:5173
```

---

## ☁️ Deployment

### Frontend → Vercel
1. Push this repo to GitHub
2. Import the repo on [Vercel](https://vercel.com)
3. Set **Root Directory** to `frontend`
4. Set environment variable: `VITE_API_URL` = your Render backend URL
5. Deploy

### Backend → Render
1. Create a **Web Service** on [Render](https://render.com)
2. Connect your GitHub repo
3. Set **Root Directory** to `backend`
4. Set **Build Command**: `pip install -r requirements.txt`
5. Set **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
6. Deploy

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/analyze` | Upload image → get detections, metrics, annotated image |
| `POST` | `/api/analyze/3d` | Get 3D surface mesh data for a specific pothole |
| `GET` | `/api/sample` | Analyze the built-in sample image |

---

## 🎮 Desktop HUD (Local Only)

```bash
cd backend
python main.py --source 0          # Webcam
python main.py --source video.mp4  # Video file
python main.py --source image.jpg  # Single image
```

| Key | Action |
|:---:|:---|
| `Q` | Quit |
| `B` | Toggle blueprint panel |
| `H` | Toggle depth heatmap |
| `S` | Save screenshot |
| `E` | Export 3D OBJ mesh |
| `N/P` | Select next/prev pothole |

---

## 📋 License

MIT
