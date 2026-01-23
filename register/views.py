from django.shortcuts import render
from register.models import  Register
from django.core.files.storage import FileSystemStorage
import datetime
# Create your views here.
def add_register1(request):
    if request.method == 'POST':
        obj=Register()
        obj.date = datetime.datetime.today()
        obj.time = datetime.datetime.now()
        obj.first_name=request.POST.get('fname')
        obj.last_name=request.POST.get('lname')
        obj.email=request.POST.get('email')
        obj.date_of_birth=request.POST.get('dob')
        obj.gender=request.POST.get('gender')
        obj.city=request.POST.get('city')
        obj.country=request.POST.get('country')
        obj.mobile=request.POST.get('mobile')
        obj.bio=request.POST.get('bio')
        obj.password=request.POST.get('pass')
        obj.status='pending'
        obj.confirm_password=request.POST.get('cpass')
        my_file = request.FILES['photo']
        fs = FileSystemStorage()
        fs.save(my_file.name, my_file)
        obj.photo = my_file.name
        obj.register_id=1
        obj.save()
    return render(request,"register/register.html")

def add_register(request):
    ob = Register.objects.all()
    context = {
        'b': ob
    }
    return render(request,"register/admin_users.html",context)

def accept(request,idd):
    obj=Register.objects.get(register_id=idd)
    obj.status='accept'
    obj.save()
    return add_register(request)
def reject(request,idd):
    obj=Register.objects.get(register_id=idd)
    obj.status='reject'
    obj.save()
    return add_register(request)
