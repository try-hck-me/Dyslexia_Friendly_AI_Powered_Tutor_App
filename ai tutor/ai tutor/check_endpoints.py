import requests

base = "http://127.0.0.1:8000"
endpoints = [
    "/docs",
    "/api/upload/health",
    "/api/chatbot/health",
    "/api/quiz/health",
    "/api/analytics/health",
    "/api/graph/health",
    "/api/tts/health",
    "/api/friendlybot/health",
]

for ep in endpoints:
    try:
        r = requests.get(base + ep, timeout=5)
        print(f"{r.status_code}  {ep}")
    except Exception as e:
        print(f"ERR  {ep}  ->  {type(e).__name__}: {e}")
