# pyre-ignore-all-errors
import cv2 # pyre-ignore
import dlib # pyre-ignore
import numpy as np # pyre-ignore
import os # pyre-ignore
import threading # pyre-ignore
from django.core.cache import cache # pyre-ignore

dlib_lock = threading.Lock()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PREDICTOR_PATH = os.path.join(BASE_DIR, 'static', 'shape_predictor_68_face_landmarks.dat')
FACE_REC_MODEL_PATH = os.path.join(BASE_DIR, 'static', 'dlib_face_recognition_resnet_model_v1.dat')

if os.path.exists(PREDICTOR_PATH):
    predictor = dlib.shape_predictor(PREDICTOR_PATH)
else:
    predictor = None
    print(f"Warning: Could not find {PREDICTOR_PATH}")

if os.path.exists(FACE_REC_MODEL_PATH):
    face_rec_model = dlib.face_recognition_model_v1(FACE_REC_MODEL_PATH)
else:
    face_rec_model = None
    print(f"Warning: Could not find {FACE_REC_MODEL_PATH}")

detector = dlib.get_frontal_face_detector()

def get_face_descriptor(image_path_or_bytes):
    """
    Returns the face descriptor of the FIRST face detected in the image.
    Accepts either an image path or bytes/np array.
    """
    try:
        img = None
        cache_key = None
        
        if isinstance(image_path_or_bytes, str):
            if not os.path.exists(image_path_or_bytes):
                return None
                
            # Attempt to retrieve from cache using path and mtime
            try:
                mtime = os.path.getmtime(image_path_or_bytes)
                # Create a safe, stable cache key
                import hashlib
                safe_path = hashlib.md5(image_path_or_bytes.encode('utf-8')).hexdigest()
                cache_key = f"face_desc_{safe_path}_{mtime}"
                
                cached_desc = cache.get(cache_key)
                if cached_desc is not None:
                    if isinstance(cached_desc, str) and cached_desc == "NO_FACE":
                        return None
                    return cached_desc
            except Exception as e:
                print(f"Cache check error: {e}")
                
            img = cv2.imread(image_path_or_bytes)
        elif isinstance(image_path_or_bytes, bytes):
            img = cv2.imdecode(np.frombuffer(image_path_or_bytes, np.uint8), cv2.IMREAD_COLOR)
        else:
            img = image_path_or_bytes
            
        if img is None:
            if cache_key:
                cache.set(cache_key, "NO_FACE", timeout=None)
            return None
            
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        with dlib_lock:
            # Upsample=1 for standard detection
            faces = detector(rgb, 1)
            if not faces:
                # Try more aggressive upsampling
                faces = detector(rgb, 2)
                if not faces:
                    if cache_key:
                        cache.set(cache_key, "NO_FACE", timeout=None)
                    return None
            
            shape = predictor(rgb, faces[0])
            face_descriptor = face_rec_model.compute_face_descriptor(rgb, shape)
            
            result = np.array(face_descriptor)
            
            if cache_key:
                try:
                    # Cache the result indefinitely
                    cache.set(cache_key, result, timeout=None)
                except Exception as e:
                    print(f"Cache set error: {e}")
                    
            return result
    except Exception as e:
        print(f"Error in get_face_descriptor: {e}")
        return None

def compare_faces(known_faces, test_descriptor, threshold=0.60):
    """
    Compares a test descriptor against a list of known_faces.
    known_faces is typically a list of tuples: [('name_or_id', descriptor_array), ...]
    Returns (matched_name, distance) or ("Unknown", float('inf'))
    """
    if test_descriptor is None or not known_faces:
        return "Unknown", float('inf')
        
    best_match = "Unknown"
    best_distance = float('inf')
    
    test_desc_np = np.array(test_descriptor)
    
    for name, known_desc in known_faces:
        if known_desc is None:
            continue
        known_desc_np = np.array(known_desc)
        
        distance = np.linalg.norm(known_desc_np - test_desc_np) # pyre-ignore
        
        if distance < best_distance:
            best_distance = distance
            best_match = name
            
    if best_distance <= threshold:
        return best_match, best_distance
        
    return "Unknown", best_distance
