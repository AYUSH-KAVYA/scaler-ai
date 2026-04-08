import os
import re
import sys
import subprocess
import time
from dotenv import load_dotenv

load_dotenv()

def check_file(path):
    exists = os.path.exists(path)
    print(f"[{'OK' if exists else 'FAIL'}] {path}")
    return exists

def check_env_vars():
    vars = ["HF_TOKEN", "API_BASE_URL", "MODEL_NAME"]
    all_ok = True
    for v in vars:
        val = os.getenv(v)
        print(f"[{'OK' if val else 'MISSING'}] Env Var: {v}")
        if not val: all_ok = False
    return all_ok

def check_endpoints():
    print("Checking Local Endpoints (Ensure server is running)...")
    try:
        import requests
        endpoints = ["/reset", "/step", "/state"]
        for ep in endpoints:
            try:
                r = requests.get(f"http://localhost:8000{ep}") if ep == "/state" else requests.post(f"http://localhost:8000{ep}")
                print(f"[{'OK' if r.status_code == 200 else 'FAIL'}] Endpoint {ep} ({r.status_code})")
            except:
                print(f"[FAIL] Endpoint {ep} (Connection Error)")
    except ImportError:
        print("[SKIP] requests library not found. Install it to check endpoints.")

def validate():
    print("--- NEONGRID SUBMISSION VALIDATOR ---")
    
    files_ok = all([
        check_file("inference.py"),
        check_file("Dockerfile"),
        check_file("openenv.yaml"),
        check_file("models.py")
    ])
    
    env_ok = check_env_vars()
    
    # Check inference.py for hardcoded keys
    with open("inference.py", "r") as f:
        content = f.read()
        if "hf_" in content and "os.getenv" not in content.split("hf_")[1].split()[0]:
            print("[WARNING] Found potential hardcoded API key in inference.py!")
        else:
            print("[OK] No hardcoded keys detected in inference.py")

    # Check log format in inference.py
    log_patterns = [r"\[START\]", r"\[STEP\]", r"\[END\]"]
    logs_match = True
    for p in log_patterns:
        if not re.search(p, content):
            print(f"[FAIL] Missing log pattern: {p}")
            logs_match = False
    if logs_match:
        print("[OK] Logging patterns present.")

    if files_ok and env_ok and logs_match:
        print("\n[SUCCESS] Basic compliance verified. Ready for baseline reproduction test.")
    else:
        print("\n[FAIL] Compliance check failed. Fix errors before submitting.")

if __name__ == "__main__":
    validate()
    check_endpoints()
