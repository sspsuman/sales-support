Superstore Analytics
Structure (must be exactly like this, with vercel.json at the Vercel Root Directory):
  public/index.html   frontend
  api/*.py            serverless API
  superstore.db, server.py, vercel.json
LOCAL:  python server.py -> http://localhost:8000
VERCEL: Root Directory = folder containing vercel.json, Framework Preset = Other.
