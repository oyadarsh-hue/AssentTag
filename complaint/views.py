from django.shortcuts import render, redirect
from complaint.models import Complaint
from register.models import Register
import datetime

# Create your views here.
def add_complaint_view(request):
    ob=Complaint.objects.all()
    context={
        'a':ob
    }
    return render(request,"complaint/admin_complaints_view.html",context)

def add_complaint1(request):
    ss = request.session.get('u_id')
    if not ss:
        return redirect('/login/login/')
    current_user = Register.objects.get(register_id=ss)
    
    if request.method=='POST':
        obj=Complaint()
        obj.date=datetime.datetime.today()
        obj.time=datetime.datetime.now()
        obj.complaint=request.POST.get('description')
        obj.subject=request.POST.get('subject')
        obj.urgency=request.POST.get('urgency')
        obj.reply='pending'
        obj.register_id=ss
        obj.save()
    return render(request,"complaint/user_complaint.html", {'current_user': current_user})

def add_reply(request,idd):
    if request.method=='POST':
        obj=Complaint.objects.get(complaint_id=idd)
        obj.reply=request.POST.get('admin_reply')
        obj.save()
    return render(request,'complaint/post_reply.html')

def view_replies(request):
    ss = request.session.get('u_id')
    if not ss:
        from django.shortcuts import redirect
        return redirect('/login/login/')
    current_user = Register.objects.get(register_id=ss)
    
    complaints = Complaint.objects.filter(register_id=ss).order_by('-date', '-time')
    return render(request, 'complaint/view_replies.html', {'complaints': complaints, 'current_user': current_user})
