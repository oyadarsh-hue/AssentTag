import subprocess
import time
import requests
import os
import sys

def test_full_stack():
    # Start server and redirect stdout/stderr to a file
    with open('server_test.log', 'w') as logfile:
        proc = subprocess.Popen([sys.executable, "manage.py", "runserver", "8000"],
                                stdout=logfile, stderr=subprocess.STDOUT)
    
        time.sleep(5) # wait for server
        
        try:
            # We fetch exactly what the browser fetches
            s = requests.Session()
            url = "http://127.0.0.1:8000/image/dynamic/feed/111/"
            print(f"Fetching {url}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            }
            # Unauthenticated first
            r1 = s.get(url, headers=headers)
            print(f"Unauthenticated: {r1.status_code}, length={len(r1.content)}")
            
            # Now mock a login by getting the session cookie
            # But wait, we can just POST to login
            login_url = "http://127.0.0.1:8000/login/loginAction/"
            r_login = s.post(login_url, data={'name': 'adarsh', 'password': 'adarsh'}, allow_redirects=True)
            print(f"Login attempt status: {r_login.status_code}")
            
            # Now authenticated
            r2 = s.get(url, headers=headers)
            print(f"Authenticated fetch: {r2.status_code}, length={len(r2.content)}")
            
        except Exception as e:
            print(f"Error fetching: {e}")
        finally:
            proc.terminate()
            
    # Print the server log
    time.sleep(1)
    if os.path.exists('server_test.log'):
        with open('server_test.log', 'r') as logfile:
            print("\n--- SERVER LOGS ---")
            print(logfile.read())

if __name__ == "__main__":
    test_full_stack()
