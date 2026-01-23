from django.shortcuts import render
from image.models import Image
from django.core.files.storage import FileSystemStorage
import datetime
# Create your views here.
def add_image(request):
    ob=Image.objects.all()
    context={
        'a':ob
    }
    return render(request,"image/admin_photo_details.html",context)
def add_image1(request):
    if request.method == 'POST' :
        obj = Image()
        obj.date=datetime.datetime.today()
        obj.time=datetime.datetime.now()
        obj.visibility=request.POST.get('visibility')

        my_file=request.FILES['media']
        fs = FileSystemStorage()
        fs.save(my_file.name,my_file)
        obj.photo=my_file.name

        obj.register_id=1
        obj.save()
    return render(request,"image/user-upload.html")
