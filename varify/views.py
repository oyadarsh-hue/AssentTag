from django.shortcuts import render # pyre-ignore

import numpy as np # pyre-ignore
import dlib # pyre-ignore
import cv2 # pyre-ignore
from assentag import settings # pyre-ignore
import os # pyre-ignore
from django.core.files.storage import FileSystemStorage # pyre-ignore
detector = dlib.get_frontal_face_detector()
# shape_predictor = dlib.shape_predictor(str(settings.BASE_DIR)+str(settings.STATIC_URL)+"shape_predictor_68_face_landmarks.dat")

shape_predictor = str(settings.BASE_DIR)+"/"+str(settings.STATIC_URL)+"shape_predictor_68_face_landmarks.dat"
predictor = dlib.shape_predictor(shape_predictor)

model_path = str(settings.BASE_DIR)+"/"+str(settings.STATIC_URL)+"dlib_face_recognition_resnet_model_v1.dat"
face_rec_model = dlib.face_recognition_model_v1(model_path)

def get_face_descriptor(image_path):
    print(image_path)
    image = cv2.imread(image_path)
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    faces = detector(rgb_image)
    if len(faces) == 0:
        return None


    shape = predictor(rgb_image, faces[0])
    # return None
    descriptor = face_rec_model.compute_face_descriptor(rgb_image, shape)
    return np.array(descriptor)

from register.models import Register # pyre-ignore
from pyzbar.pyzbar import decode # pyre-ignore
from django.http import HttpResponse # pyre-ignore

def load_known_faces(cid):
    known_faces = []
    objs=Register.objects.all()
    for o in objs:
        folder_path = str(settings.BASE_DIR)+"/"+str(settings.MEDIA_URL)+ o.image
        # path = os.path.join(folder_path, 'photo.jpg')
        name = str(o.c_id)

        descriptor = get_face_descriptor(folder_path)
        if descriptor is not None:
            known_faces.append((name, descriptor))
            print(f"[+] Loaded encoding for {name}")
        else:
            print(f"[!] No face found in {folder_path}")
        return known_faces

def compare_faces(known_faces, face_descriptor, threshold=0.98):
    best_match = ("Unknown", 0.0)  # name, similarity%
    for name, known_descriptor in known_faces:
        dist = np.linalg.norm(known_descriptor - face_descriptor) # pyre-ignore
        similarity = 1 - (dist / threshold)  # normalized similarity (0 to 1)
        similarity_percentage = similarity * 100
        print(similarity_percentage )
        if similarity_percentage >= 50 and similarity_percentage > best_match[1]:
            best_match = (name, similarity_percentage)
    return best_match

# Create your views here.
def varify(request):
    if request.method == 'POST' and request.FILES.get('photo'):
        photo = request.FILES['photo']
        fs = FileSystemStorage()
        filename = fs.save(photo.name, photo)
        # file_path = os.path.join(settings.MEDIA_ROOT, filename)
        frame = cv2.imread(str(settings.BASE_DIR)+str(settings.MEDIA_URL)+filename)

        qr = request.FILES['qr']
        filename1 = fs.save(qr.name, qr)
        qimg= cv2.imread(str(settings.BASE_DIR)+str(settings.MEDIA_URL)+filename1)


        decoded_objects = decode(qimg)
        if decoded_objects:
            data = decoded_objects[0].data.decode("utf-8")
            dat=data.split('-')[0]
            cobj=Register.objects.all()
            if len(cobj)>0:
                cert=cobj[0]

                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                known_faces = load_known_faces(cert.c_id)
                faces = detector(rgb_frame)
                # if len(faces)>0:
                for face in faces:
                    face=faces[0]
                    print("hello")
                    shape = predictor(rgb_frame, face)
                    descriptor = face_rec_model.compute_face_descriptor(rgb_frame, shape)
                    descriptor = np.array(descriptor)

                    name, distance = compare_faces(known_faces, descriptor)
                    print(name)
                    # if dat==name:
                    #     return HttpResponse("Certificate VArified")
                    # else:
                    #     return HttpResponse("Matching record not found")


    return render(request,'varify/varify.html')