from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
# Create your views here.
import dlib
import cv2
from assentag import settings
import os
predictor_path = str(settings.BASE_DIR)+ "/"+str(settings.STATIC_URL)+"shape_predictor_68_face_landmarks.dat"
predictor = dlib.shape_predictor(predictor_path)

def generate(request):

    if request.method == 'POST' and request.FILES.get('photo'):
        photo = request.FILES['photo']
        fs = FileSystemStorage()
        filename = fs.save(photo.name, photo)
        # uploaded_file_url = fs.url(filename)
        # image = cv2.imread(str(settings.BASE_DIR)+"/"+str(settings.STATIC_URL)+filename)
        uploaded_path = os.path.join(settings.MEDIA_ROOT, filename)
        image = cv2.imread(uploaded_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Detect faces in the image
        detector = dlib.get_frontal_face_detector()
        faces = detector(gray)
        print(len(faces))
        for face in faces:
            # Predict facial landmarks
            landmarks = predictor(gray, face)
            facial_landmarks = []
            # Loop over the 68 facial landmarks
            for n in range(0, 68):
                x = landmarks.part(n).x
                y = landmarks.part(n).y
                cv2.circle(image, (x, y), 1, (0, 255, 0), -1)
                facial_landmarks.append((x, y))
        
        output_filename = "landmark_output.jpg"
        output_path = os.path.join(settings.MEDIA_ROOT, output_filename)
        cv2.imwrite(output_path, image)


        return render(request, 'generate/upload.html', {'uploaded_file_url': output_filename, 'photo': filename})
    return render(request,'generate/upload.html')