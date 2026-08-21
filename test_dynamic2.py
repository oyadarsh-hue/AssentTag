import urllib.request
try:
    resp = urllib.request.urlopen("http://127.0.0.1:8000/image/dynamic/71/")
    print(f"Status: {resp.getcode()}")
    print(f"Size: {len(resp.read())} bytes")
except Exception as e:
    print(e)
