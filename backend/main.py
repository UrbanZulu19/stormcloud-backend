#!/bin/bash
# StormCloud VIBE Backend Multi-AI Super Installer
# Works on Termux (Android 12)
# Author: Brandon

# ----------------------------
# CONFIGURATION
# ----------------------------
PROJECT_DIR=$HOME/stormcloud-backend
ADMIN_EMAIL="admin@stormcloud.dev"
ADMIN_PASSWORD="Stormgod420!"
REPO_URL=""  # Optional GitHub URL to push later

# ----------------------------
# UPDATE & INSTALL DEPENDENCIES
# ----------------------------
echo "[1/7] Updating packages and installing dependencies..."
pkg update -y && pkg upgrade -y
pkg install -y python git curl wget clang make
pip install --upgrade pip
pip install fastapi uvicorn pydantic python-multipart requests

# ----------------------------
# CREATE PROJECT DIRECTORY
# ----------------------------
echo "[2/7] Creating project directory..."
mkdir -p $PROJECT_DIR && cd $PROJECT_DIR

# ----------------------------
# CREATE MAIN.PY BACKEND
# ----------------------------
echo "[3/7] Writing main.py backend with multi-AI support..."
cat > main.py << 'EOF'
#!/usr/bin/env python3
# main.py - StormCloud VIBE Backend with Multi-AI Support
# Author: Brandon

import os, sqlite3, secrets, time, subprocess, requests
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

DATABASE = "stormcloud.db"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL") or "admin@stormcloud.dev"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or "Stormgod420!"

# ------------------------------
# DATABASE INIT
# ------------------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT,
        subscription_tier TEXT DEFAULT 'free',
        ai_requests_used INTEGER DEFAULT 0,
        executions_used INTEGER DEFAULT 0,
        token TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS ai_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        prompt TEXT,
        old_code TEXT,
        new_code TEXT,
        explanation TEXT,
        provider TEXT,
        cost REAL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    # insert admin if missing
    c.execute("SELECT * FROM users WHERE email=?", (ADMIN_EMAIL,))
    if not c.fetchone():
        c.execute("INSERT INTO users (name,email,password,subscription_tier) VALUES (?,?,?,?)",
                  ("Admin", ADMIN_EMAIL, ADMIN_PASSWORD, "admin"))
    conn.commit()
    conn.close()

init_db()

# ------------------------------
# FASTAPI SETUP
# ------------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# SCHEMAS
# ------------------------------
class AuthModel(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class CodeExecutionModel(BaseModel):
    code: str
    language: str = "python"

class VibeRequestModel(BaseModel):
    prompt: str
    current_code: str
    mode: str = "edit"

# ------------------------------
# UTILS
# ------------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def authenticate_user(token: str = Header(...)):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE token=?", (token,)).fetchone()
    conn.close()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return user

def generate_token():
    return secrets.token_hex(32)

# ------------------------------
# AUTH ENDPOINTS
# ------------------------------
@app.post("/auth/register")
def register(auth: AuthModel):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        token = generate_token()
        c.execute("INSERT INTO users (name,email,password,token) VALUES (?,?,?,?)",
                  (auth.name, auth.email, auth.password, token))
        conn.commit()
        user_id = c.lastrowid
        return {"access_token": token, "user": {"id": user_id, "email": auth.email, "name": auth.name}}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Email already exists")
    finally:
        conn.close()

@app.post("/auth/login")
def login(auth: AuthModel):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email=? AND password=?", (auth.email, auth.password)).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = generate_token()
    conn.execute("UPDATE users SET token=? WHERE id=?", (token, user["id"]))
    conn.commit()
    conn.close()
    return {"access_token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"], "subscription_tier": user["subscription_tier"]}}

@app.get("/auth/me")
def get_me(user = Depends(authenticate_user)):
    return {"id": user["id"], "email": user["email"], "name": user["name"], "subscription_tier": user["subscription_tier"], "ai_requests_used": user["ai_requests_used"], "executions_used": user["executions_used"]}

# ------------------------------
# CODE EXECUTION ENDPOINT
# ------------------------------
@app.post("/execute")
def execute_code(exec_model: CodeExecutionModel, user = Depends(authenticate_user)):
    start = time.time()
    try:
        result = subprocess.run(["python3", "-c", exec_model.code],
                                capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
        exit_code = result.returncode
        exec_time = time.time() - start
    except Exception as e:
        output = str(e)
        exit_code = -1
        exec_time = time.time() - start
    conn = get_db_connection()
    conn.execute("UPDATE users SET executions_used = executions_used + 1 WHERE id=?", (user["id"],))
    conn.commit()
    conn.close()
    return {"output": output, "exit_code": exit_code, "execution_time": exec_time}

# ------------------------------
# MULTI-AI PROVIDER LOGIC
# ------------------------------
class BaseAIProvider:
    name = "mock"
    def edit_code(self, prompt: str, current_code: str):
        return {"new_code": current_code + "\n# Mock Vibe: " + prompt,
                "explanation": f"Applied mock vibe: {prompt}",
                "cost": 0.0}

class GroqAI(BaseAIProvider):
    name = "groq"
    API_KEY = os.environ.get("GROQ_API_KEY")
    def edit_code(self, prompt, current_code):
        if not self.API_KEY:
            return BaseAIProvider().edit_code(prompt, current_code)
        payload = {"prompt": prompt, "code": current_code}
        headers = {"Authorization": f"Bearer {self.API_KEY}"}
        r = requests.post("https://api.groq.com/v1/vibe", json=payload, headers=headers)
        data = r.json()
        return {"new_code": data.get("new_code", current_code), "explanation": data.get("explanation", ""), "cost": data.get("cost",0)}

class GoogleAI(BaseAIProvider):
    name = "google"
    API_KEY = os.environ.get("GOOGLE_API_KEY")
    def edit_code(self, prompt, current_code):
        if not self.API_KEY:
            return BaseAIProvider().edit_code(prompt, current_code)
        payload = {"prompt": prompt, "code": current_code}
        headers = {"Authorization": f"Bearer {self.API_KEY}"}
        r = requests.post("https://api.google.com/gemini/v1/vibe", json=payload, headers=headers)
        data = r.json()
        return {"new_code": data.get("new_code", current_code), "explanation": data.get("explanation", ""), "cost": data.get("cost",0)}

class OpenRouterAI(BaseAIProvider):
    name = "openrouter"
    API_KEY = os.environ.get("OPENROUTER_API_KEY")
    def edit_code(self, prompt, current_code):
        if not self.API_KEY:
            return BaseAIProvider().edit_code(prompt, current_code)
        payload = {"prompt": prompt, "code": current_code}
        headers = {"Authorization": f"Bearer {self.API_KEY}"}
        r = requests.post("https://openrouter.ai/v1/code", json=payload, headers=headers)
        data = r.json()
        return {"new_code": data.get("new_code", current_code), "explanation": data.get("explanation", ""), "cost": data.get("cost",0)}

def get_provider(provider_name: str):
    providers = [GroqAI(), GoogleAI(), OpenRouterAI(), BaseAIProvider()]
    for p in providers:
        if p.name == provider_name.lower():
            return p
    return BaseAIProvider()

# ------------------------------
# AI VIBE ENDPOINT
# ------------------------------
@app.post("/ai/vibe")
def ai_vibe(vibe: VibeRequestModel, user = Depends(authenticate_user), provider: str = "auto"):
    if provider == "auto":
        sequence = ["google","groq","openrouter","mock"]
        idx = user["ai_requests_used"] % len(sequence)
        provider_name = sequence[idx]
    else:
        provider_name = provider
    ai = get_provider(provider_name)
    result = ai.edit_code(vibe.prompt, vibe.current_code)
    
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO ai_logs (user_id,prompt,old_code,new_code,explanation,provider,cost)
        VALUES (?,?,?,?,?,?,?)""",
                 (user["id"], vibe.prompt, vibe.current_code, result["new_code"], result["explanation"], ai.name, result["cost"]))
    conn.execute("UPDATE users SET ai_requests_used = ai_requests_used + 1 WHERE id=?", (user["id"],))
    conn.commit()
    conn.close()
    
    return {"changes": {"new_code": result["new_code"], "explanation": result["explanation"]}, "provider": ai.name, "cost": result["cost"]}

# ------------------------------
# RUN SERVER
# ------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
EOF

# ----------------------------
# ENV VARIABLES (you fill keys)
# ----------------------------
export ADMIN_EMAIL=$ADMIN_EMAIL
export ADMIN_PASSWORD=$ADMIN_PASSWORD
echo "[4/7] Please set your AI provider keys if available:"
echo "export GOOGLE_API_KEY='your-google-key'"
echo "export GROQ_API_KEY='your-groq-key'"
echo "export OPENROUTER_API_KEY='your-openrouter-key'"

# ----------------------------
# RUN BACKEND
# ----------------------------
echo "[5/7] Starting StormCloud VIBE backend..."
uvicorn main:app --host 0.0.0.0 --port 8001 --reload &

# ----------------------------
# OPTIONAL: GitHub Push
# ----------------------------
if [ -n "$REPO_URL" ]; then
    echo "[6/7] Initializing Git repository and pushing to GitHub..."
    git init
    git add .
    git commit -m "Initial StormCloud VIBE backend with Multi-AI"
    git branch -M main
    git remote add origin $REPO_URL
    git push -u origin main
fi

echo "[7/7] Installation complete!"
echo "Backend running at http://localhost:8001"
echo "Admin account: $ADMIN_EMAIL / $ADMIN_PASSWORD"
echo "Use selectedProvider in frontend: 'auto', 'google', 'groq', 'openrouter'"