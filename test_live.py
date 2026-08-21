import subprocess
import time
import urllib.request
import urllib.error
import sys

def test_live_server():
    print("Starting Django server...")
    proc = subprocess.Popen(["python", "manage.py", "runserver", "8000"], 
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    time.sleep(5) # Wait for server to start
    
    try:
        url = "http://127.0.0.1:8000/image/dynamic/feed/111/"
        print(f"Requesting {url}...")
        req = urllib.request.Request(url)
        content = urllib.request.urlopen(req).read()
        print(f"Success! Content length: {len(content)}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode('utf-8', errors='ignore'))
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Stopping server...")
        proc.terminate()
        
if __name__ == "__main__":
    test_live_server()
