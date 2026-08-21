import os
import time
import cv2
import numpy as np
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assentag.settings')

try:
    django.setup()
    from register.models import Register
    from face_utils import get_face_descriptor, face_rec_model, predictor, detector, dlib_lock
    
    def run_live_recognition():
        # 1. Load all registered users' profile photos and compute face descriptors
        print("Loading all registered users and computing biometric reference descriptors...")
        known_faces = []
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        
        for u in Register.objects.all():
            anchor = getattr(u, 'reg_photo', None) or getattr(u, 'photo', None)
            if anchor:
                path_u = os.path.join(static_dir, str(anchor))
                if os.path.exists(path_u):
                    d_u = get_face_descriptor(path_u)
                    if d_u is not None:
                        user_label = f"{u.first_name} {u.last_name} (ID: {u.register_id})"
                        known_faces.append((user_label, d_u))
                        print(f"  [+] Loaded Biometrics for: {user_label}")
                    else:
                        print(f"  [!] Could not parse face in registered photo: {path_u}")
                else:
                    print(f"  [!] Reference photo missing on disk: {path_u}")
                    
        if not known_faces:
            print("\nError: No registered user reference photos found to match against!")
            return
            
        print(f"\nSuccessfully loaded {len(known_faces)} registered users.")
        
        # 2. Access the built-in webcam
        print("\nInitializing built-in webcam...")
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("Error: Could not open the built-in webcam. Please make sure it is not in use.")
            return
            
        # Warm up camera sensor for a brief second
        print("Warming up camera sensor...")
        time.sleep(1.0)
        
        print("Capturing live frame into RAM...")
        ret, frame = cap.read()
        cap.release()
        
        if not ret or frame is None:
            print("Error: Failed to capture image from webcam.")
            return
            
        # 3. Detect face in the live frame
        live_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        print("Detecting face in webcam frame...")
        with dlib_lock:
            live_faces = detector(live_rgb)
            
        if len(live_faces) == 0:
            print("\nBiometric Check Failed: No face detected in front of the webcam stream!")
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            save_path = os.path.join(desktop_dir, "live_recognition_failed.jpg")
            cv2.imwrite(save_path, frame)
            print(f"Saved the capture so you can verify the camera frame: {save_path}")
            return
            
        print(f"Detected {len(live_faces)} face(s) in webcam frame.")
        largest_face = max(live_faces, key=lambda rect: rect.width() * rect.height())
        
        with dlib_lock:
            shape = predictor(live_rgb, largest_face)
            live_desc = np.array(face_rec_model.compute_face_descriptor(live_rgb, shape))
            
        # 4. Compare live webcam face against all registered users
        print("\nPerforming biological verification against database...")
        best_match_label = "Unknown (Imposter / Not Registered)"
        best_dist = float('inf')
        threshold = 0.55  # standard facial recognition threshold
        
        for label, ref_desc in known_faces:
            dist = np.linalg.norm(live_desc - ref_desc)
            print(f"  -> Distance to {label}: {dist:.4f}")
            if dist < best_dist:
                best_dist = dist
                if dist <= threshold:
                    best_match_label = label
                    
        print("\n" + "="*55)
        print("                  BIOMETRIC AUDIT REPORT")
        print("="*55)
        print(f"Identified Person : {best_match_label}")
        print(f"Euclidean Distance: {best_dist:.4f}")
        if best_match_label != "Unknown (Imposter / Not Registered)":
            print("Status             : VERIFIED MATCH SUCCESS!")
        else:
            print("Status             : VERIFICATION REJECTED (Stranger/Unauthorized)")
        print("="*55)
        
        # Save the captured result image to Desktop
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        save_path = os.path.join(desktop_dir, "live_recognition_result.jpg")
        cv2.imwrite(save_path, frame)
        print(f"\nSaved live recognition capture to: {save_path}")

    if __name__ == "__main__":
        run_live_recognition()

except Exception as e:
    print(f"Error loading system requirements or models: {e}")
