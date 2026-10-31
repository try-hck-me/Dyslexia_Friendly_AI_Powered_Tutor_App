"""Quick smoke-test of all backend endpoints. ASCII-safe for Windows console."""
import sys
import requests

BASE = "http://localhost:8000"
PASS, FAIL, ERR = "OK  ", "FAIL", "ERR "

results = []

def test(method, path, body=None, label=None):
    label = label or f"{method} {path}"
    try:
        if method == "GET":
            r = requests.get(BASE + path, timeout=20)
        else:
            r = requests.post(BASE + path, json=body, timeout=20)
        d = r.json()
        ok = r.status_code == 200
        err = d.get("detail") or d.get("error") or ""
        flag = PASS if ok else FAIL
        msg = f"[{flag}] {label}: HTTP {r.status_code}"
        if err:
            msg += f" | {str(err)[:80]}"
        print(msg)
        results.append((ok, label))
        return d
    except Exception as e:
        print(f"[{ERR}] {label}: {e}")
        results.append((False, label))
        return {}

print("=" * 65)
print("BACKEND SMOKE TEST")
print("=" * 65)

test("GET",  "/",                              label="Health check")
test("GET",  "/status",                        label="Full status")
test("POST", "/users/register",
     {"user_id": "smoke_student", "name": "Smoke Student", "role": "student"},
     label="Register student")
test("GET",  "/users/smoke_student",           label="Get user")
test("GET",  "/analytics/smoke_student",       label="Analytics")
test("GET",  "/documents",                     label="List documents")
test("GET",  "/graph/viz",                     label="Graph viz")
test("GET",  "/chat/history/smoke_student",    label="Chat history")
test("POST", "/chat",
     {"user_id": "smoke_student", "question": "hello"},
     label="Chat (no docs)")
test("POST", "/friendly",
     {"user_id": "smoke_student", "message": "I feel okay"},
     label="FriendlyBot")

print("=" * 65)
passed = sum(1 for ok, _ in results if ok)
total  = len(results)
print(f"RESULT: {passed}/{total} passed")
if passed < total:
    print("FAILED:")
    for ok, label in results:
        if not ok:
            print(f"  - {label}")
