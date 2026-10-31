"""QA test for all backend endpoints."""
import urllib.request
import json

BASE = "http://localhost:8000"


def get(path):
    req = urllib.request.Request(BASE + path)
    res = urllib.request.urlopen(req, timeout=10)
    return json.loads(res.read())


def post(path, body):
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    res = urllib.request.urlopen(req, timeout=10)
    return json.loads(res.read())


PASS = []
FAIL = []


def check(name, fn):
    try:
        result = fn()
        PASS.append(name)
        print(f"  PASS  {name}  ->  {result}")
    except Exception as exc:
        FAIL.append(name)
        print(f"  FAIL  {name}  ->  {exc}")


check("GET /",                   lambda: get("/"))
check("GET /status",             lambda: get("/status"))
check("POST /users/register",    lambda: post("/users/register", {"user_id": "qa_user", "name": "QA User", "role": "student"}))
check("GET /users/qa_user",      lambda: get("/users/qa_user"))
check("GET /chat/history/qa_user", lambda: get("/chat/history/qa_user"))
check("GET /analytics/qa_user",  lambda: get("/analytics/qa_user"))
check("GET /documents",          lambda: get("/documents"))

print()
print(f"Results: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILED:", FAIL)
