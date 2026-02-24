import subprocess
import os
import sys
import time

def start():
    # 1. Start Backend
    print("🚀 Starting Backend (FastAPI)...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--reload"],
        cwd=os.getcwd()
    )

    # 2. Start Frontend
    print("🎨 Starting Frontend (Vite)...")
    frontend_dir = os.path.join(os.getcwd(), "Frontend")
    
    # Check if node_modules exists
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("📦 node_modules not found. Installing...")
        subprocess.run(["npm", "install"], cwd=frontend_dir)

    frontend_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir
    )

    try:
        while True:
            time.sleep(1)
            if backend_proc.poll() is not None:
                print("❌ Backend crashed. Shutting down...")
                break
            if frontend_proc.poll() is not None:
                print("❌ Frontend crashed. Shutting down...")
                break
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    finally:
        backend_proc.terminate()
        frontend_proc.terminate()

if __name__ == "__main__":
    start()
