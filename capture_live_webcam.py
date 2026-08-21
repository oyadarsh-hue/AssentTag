import cv2
import os
import time

def capture_frame():
    # 1. Access the built-in webcam (index 0 is typically the default integrated camera)
    print("Initializing built-in webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open the built-in webcam. Please make sure it is not being used by another application or blocked by privacy settings.")
        return
        
    # Warm up camera sensor for a brief second to adjust exposure/brightness automatically
    print("Warming up camera sensor...")
    time.sleep(1.0)
    
    # 2. Capture a live frame into RAM (stored in-memory in variable 'frame')
    print("Capturing live frame into RAM...")
    ret, frame = cap.read()
    
    if not ret or frame is None:
        print("Error: Failed to capture image from webcam.")
        cap.release()
        return
        
    # 3. Save the in-memory frame from RAM directly to the Desktop
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    save_path = os.path.join(desktop_dir, "live_webcam_test.jpg")
    
    success = cv2.imwrite(save_path, frame)
    if success:
        print(f"\nSUCCESS! Captured live webcam image into RAM and saved it to: {save_path}")
    else:
        print("\nError: Failed to save the image to your Desktop folder.")
    
    # 4. Release the camera resource
    cap.release()

if __name__ == "__main__":
    capture_frame()
