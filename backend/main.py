from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="StormCloud", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "⚡ STORMCLOUD DEPLOYED", "battery": "12%"}

@app.get("/health")
def health():
    return {"alive": True, "message": "Your AI built this!"}

@app.post("/execute")
def execute(code: str):
    return {"result": "Code execution coming soon!", "code": code}
