from django.shortcuts import render
from feedback.models import Feedback
import datetime
# Create your views here.
def add_feedback(request):
    ob=Feedback.objects.all()
    context={
        'a':ob
    }
    return render(request,"feedback/admin_feedback_view.html",context)

def add_feedback1(request):
    if request.method == 'POST':
        obj = Feedback()
        obj.date = datetime.datetime.today()
        obj.time = datetime.datetime.now()
        obj.feedback=request.POST.get('comments')
        obj.topic=request.POST.get('topic')
        obj.rating=request.POST.get('rating')
        obj.u_id=1
        obj.save()
    return render(request,"feedback/user_feedback.html")


