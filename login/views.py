from django.shortcuts import render
from login.models import Login
# Create your views here.
def add_login(request):
    # if request.method == 'POST':
    #     obj=Login()
    #     obj.username=request.POST.get('email')
    #     obj.password=request.POST.get('password')
    #     obj.type=request.POST.get('role')
    #     obj.u_id=1
    #     obj.save()
    return render(request,"login/login.html")