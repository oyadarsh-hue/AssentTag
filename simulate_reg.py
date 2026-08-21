import requests

def submit_registration():
    url = "http://127.0.0.1:8000/register/register/"
    
    session = requests.Session()
    # Get the CSRF token
    response = session.get("http://127.0.0.1:8000/register/register/")
    csrf_token = session.cookies.get('csrftoken')
    
    # We need an image to upload. Let's use 24C053.jpeg which we know exists and has a face.
    image_path = r"d:\AssentTag\assentag - Copy (2)\static\24C053.jpeg"
    files = {'photo': open(image_path, 'rb')}
    
    data = {
        'csrfmiddlewaretoken': csrf_token,
        'fname': 'Test',
        'lname': 'User',
        'email': 'test@example.com',
        'dob': '2000-01-01',
        'gender': 'Male',
        'city': 'TestCity',
        'country': 'USA',
        'mobile': '1234567890',
        'bio': 'Test bio',
        'pass': 'Password@123',
        'cpass': 'Password@123',
        'live_photo': ''
    }
    
    print("Submitting POST request to registration...")
    response = session.post(url, data=data, files=files)
    
    print(f"Status Code: {response.status_code}")
    if "Registration Failed: Duplicate account detected" in response.text:
        print("Success: Correctly detected duplicate.")
    elif "Error: No face detected" in response.text:
        print("Bug: Emitted No Face Detected error!")
    else:
        print("Other outcome:", response.text[:200])

if __name__ == "__main__":
    submit_registration()
