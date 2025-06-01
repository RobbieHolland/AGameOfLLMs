#!/usr/bin/env python3

import subprocess
import time
import sys
import os

def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting FastAPI backend server...")
    backend_process = subprocess.Popen([
        sys.executable, "-m", "uvicorn", 
        "backend.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ])
    return backend_process

def start_frontend():
    """Start the Streamlit frontend."""
    print("🎨 Starting Streamlit frontend...")
    frontend_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", 
        "frontend/app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])
    return frontend_process

def main():
    """Start both backend and frontend."""
    print("🏁 Starting Code-Writing Contest Dashboard...")
    
    # Start backend
    backend_proc = start_backend()
    
    # Wait a moment for backend to start
    print("⏳ Waiting for backend to start...")
    time.sleep(3)
    
    # Start frontend
    frontend_proc = start_frontend()
    
    print("\n✅ Dashboard started!")
    print("📊 Streamlit Dashboard: http://localhost:8501")
    print("🔧 FastAPI Backend: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("\n🛑 Press Ctrl+C to stop both servers")
    
    try:
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_proc.poll() is not None:
                print("❌ Backend process stopped")
                break
            if frontend_proc.poll() is not None:
                print("❌ Frontend process stopped")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        
        # Wait for graceful shutdown
        backend_proc.wait()
        frontend_proc.wait()
        
        print("✅ Servers stopped")

if __name__ == "__main__":
    main() 