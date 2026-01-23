from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

# Create your views here.
def add_index(request):
    return render(request,"temp/index.html")
def add_index1(request):
    return render(request,"temp/user-home.html")
def add_index2(request):
    return render(request,"temp/admin-home.html")
