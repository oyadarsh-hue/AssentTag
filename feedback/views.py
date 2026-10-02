from django.shortcuts import render, redirect
from django.contrib import messages as notices
from feedback.models import Feedback
from register.models import Register
import datetime

# Create your views here.
def add_feedback(request):
    ob=Feedback.objects.all()
    context={
        'a':ob
    }
    return render(request,"feedback/admin_feedback_view.html",context)

def add_feedback1(request):
    ss = request.session.get('u_id')
    if not ss:
        return redirect('/login/login/')
    current_user = Register.objects.get(register_id=ss)
    
    if request.method == 'POST':
        obj = Feedback()
        obj.date = datetime.datetime.today()
        obj.time = datetime.datetime.now()
        obj.feedback=request.POST.get('comments')
        obj.topic=request.POST.get('topic')
        obj.rating=request.POST.get('rating')
        obj.register_id=ss
        obj.save()
        notices.success(request, 'Thank you. Your feedback has been saved successfully.', extra_tags='feedback')
        return redirect('/feedback/feedback/')
    return render(request,"feedback/user_feedback.html", {'current_user': current_user})


