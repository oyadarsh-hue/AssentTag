from django.shortcuts import render
from  complaint.models import  Complaint
import  datetime

# Create your views here.
def add_complaint_view(request):
    ob=Complaint.objects.all()
    context={
        'a':ob
    }
    return render(request,"complaint/admin_complaints_view.html",context)
def add_complaint1(request):
    if request.method=='POST':
        obj=Complaint()
        obj.date=datetime.datetime.today()
        obj.time=datetime.datetime.now()
        obj.complaint=request.POST.get('description')
        obj.subject=request.POST.get('subject')
        obj.urgency=request.POST.get('urgency')
        obj.reply='pending'
        obj.u_id=1
        obj.save()
    return render(request,"complaint/user_complaint.html")

def add_reply(request,idd):
    if request.method=='POST':
        obj=Complaint.objects.get(complaint_id=idd)
        obj.reply=request.POST.get('admin_reply')
        obj.save()
    return render(request,'complaint/post_reply.html')
