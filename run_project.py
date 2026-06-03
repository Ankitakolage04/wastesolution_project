"""
run_project.py - Multi-process runner for WasteSolution.
Launches both the FastAPI backend and Vite React frontend concurrently.
"""

import os
import sys
import subprocess
import threading
import time

def log_stream(stream, prefix, color_code):
    """Read a stream line-by-line and print it with a color-coded prefix."""
    try:
        for line in iter(stream.readline, ''):
            if not line:
                break
            # Print with color prefix. 
            # 32 = Green, 36 = Cyan, 35 = Magenta
            sys.stdout.write(f"\033[{color_code}m{prefix}\033[0m {line}")
            sys.stdout.flush()
    except Exception:
        pass

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    frontend_dir = os.path.join(root_dir, 'frontend')
    backend_dir = os.path.join(root_dir, 'profiles_api')
    
    # Path to virtual env Python
    if sys.platform == 'win32':
        python_exe = os.path.join(root_dir, 'venv', 'Scripts', 'python.exe')
        npm_cmd = 'npm.cmd'
    else:
        python_exe = os.path.join(root_dir, 'venv', 'bin', 'python')
        npm_cmd = 'npm'
        
    if not os.path.exists(python_exe):
        print(f"Error: Virtual environment python not found at {python_exe}")
        sys.exit(1)

    print("\033[1;33m[SYSTEM] Starting WasteSolution system...\033[0m")
    
    processes = []
    
    try:
        # 1. Start Backend FastAPI
        print("\033[1;32m[SYSTEM] Spawning FastAPI Backend on http://localhost:8000...\033[0m")
        backend_proc = subprocess.Popen(
            [python_exe, 'run.py'],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        processes.append(backend_proc)
        
        # 2. Start Frontend Vite
        print("\033[1;36m[SYSTEM] Spawning Vite React Frontend on http://localhost:5173...\033[0m")
        frontend_proc = subprocess.Popen(
            [npm_cmd, 'run', 'dev'],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        processes.append(frontend_proc)
        
        # Threading for stream logs redirect
        threads = [
            threading.Thread(target=log_stream, args=(backend_proc.stdout, "[BACKEND]", "32"), daemon=True),
            threading.Thread(target=log_stream, args=(backend_proc.stderr, "[BACKEND-ERR]", "31"), daemon=True),
            threading.Thread(target=log_stream, args=(frontend_proc.stdout, "[FRONTEND]", "36"), daemon=True),
            threading.Thread(target=log_stream, args=(frontend_proc.stderr, "[FRONTEND-ERR]", "35"), daemon=True)
        ]
        
        for t in threads:
            t.start()
            
        print("\033[1;33m[SYSTEM] Both servers are running. Press Ctrl+C to stop.\033[0m")
        
        # Keep main thread alive and watch processes
        while True:
            time.sleep(1)
            # Check if any process terminated unexpectedly
            for p in processes:
                if p.poll() is not None:
                    print(f"\n\033[1;31m[SYSTEM] Warning: Process terminated with exit code {p.returncode}\033[0m")
                    raise KeyboardInterrupt
                    
    except KeyboardInterrupt:
        print("\n\033[1;33m[SYSTEM] Shutting down both servers...\033[0m")
        for p in processes:
            if p.poll() is None:
                try:
                    p.terminate()
                    # Wait briefly for graceful exit, then kill if stubborn
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("\033[1;32m[SYSTEM] Clean shutdown completed successfully.\033[0m")

if __name__ == "__main__":
    main()
