from django.shortcuts import render, redirect
from django.contrib import messages as notices
from login.models import Login
from register.models import Register, Follower, Message
from django.http import HttpResponseRedirect
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.cache import never_cache
from django.template.loader import render_to_string
from login.disappearing import (TIMER_CHOICES, can_chat, timer_for, timer_payload,
                                update_timer, conversation_messages, create_message)

# @ratelimit(key='ip', rate='5/15m', block=True)
def add_login(request):
    if request.method == 'POST':
        email=request.POST.get('email')
        password=request.POST.get('password')
        selected_role=request.POST.get('role')
        
        obj=Login.objects.filter(username=email,password=password)
        
        if len(obj) == 0:
            context = {
                'msg': "Username or password incorrect. Please try again.",
                'msg_type': 'error'
            }
            return render(request, 'login/login.html', context)
            
        for ob in obj:
            tp=ob.type
            uid=ob.u_id
            
            # Require the access mode dropdown to match the actual account role
            if tp != selected_role:
                error_msg = f"Access Denied. You selected '{selected_role}' but your account is '{tp}'."
                if tp == 'admin' and selected_role == 'user':
                    error_msg = "Warning: Admin Trying to Login User module. Protocol blocked."
                elif tp == 'user' and selected_role == 'admin':
                    error_msg = "Warning: User Trying to Login Admin module. Protocol blocked."
                
                context = {
                    'msg': error_msg,
                    'msg_type': 'error'
                }
                return render(request, 'login/login.html', context)
            
            if tp == "admin":
                request.session.cycle_key()
                request.session["u_id"]=uid
                request.session["type"]="admin"
                notices.success(request, 'You are signed in. Your admin dashboard is ready.', extra_tags='admin-login')
                return redirect('/index/index2/')
            elif tp == "user":
                user = Register.objects.filter(register_id=uid).first()
                if user and user.status == 'hibernated':
                    user.status = 'approved'
                    user.save()
                    
                request.session.cycle_key()
                request.session["u_id"]=uid
                request.session["type"]="user"
                notices.success(request, f'Welcome back, {user.first_name if user else "friend"}. Your dashboard is ready.', extra_tags='login')
                return redirect('/index/index3/')
            else:
                context = {
                    'msg': "Invalid user role."
                }
                return render(request,'login/login.html',context)
    return render(request,"login/login.html")

def follow_user(request, user_id):
    ss = request.session.get('u_id')
    if not ss:
        return redirect('/login/login/')
        
    # Prevent self-following
    if str(ss) != str(user_id):
        target_user = Register.objects.filter(register_id=user_id).first()
        if not target_user:
            return redirect('/index/index3/')
            
        # Check if already following
        exists = Follower.objects.filter(follower_user_id=ss, user_id=user_id).exists()
        if not exists:
            if target_user.is_private:
                from register.models import FollowRequest
                req_exists = FollowRequest.objects.filter(requester_user_id=ss, target_user_id=user_id).exists()
                if not req_exists:
                    FollowRequest.objects.create(requester_user_id=ss, target_user_id=user_id)
            else:
                Follower.objects.create(follower_user_id=ss, user_id=user_id)
            
    return redirect(request.META.get('HTTP_REFERER', '/index/index3/'))

def accept_follow(request, req_id):
    ss = request.session.get('u_id')
    if not ss: return redirect('/login/login/')
    from register.models import FollowRequest
    freq = FollowRequest.objects.filter(request_id=req_id, target_user_id=ss).first()
    if freq:
        if not Follower.objects.filter(follower_user_id=freq.requester_user_id, user_id=ss).exists():
            Follower.objects.create(follower_user_id=freq.requester_user_id, user_id=ss)
        freq.delete()
    return redirect('/index/index4/')

def reject_follow(request, req_id):
    ss = request.session.get('u_id')
    if not ss: return redirect('/login/login/')
    from register.models import FollowRequest
    FollowRequest.objects.filter(request_id=req_id, target_user_id=ss).delete()
    return redirect('/index/index4/')

def unfollow_user(request, user_id):
    ss = request.session.get('u_id')
    if not ss:
        return redirect('/login/login/')
        
    Follower.objects.filter(follower_user_id=ss, user_id=user_id).delete()
    return redirect(request.META.get('HTTP_REFERER', '/index/index3/'))

def remove_follower(request, user_id):
    ss = request.session.get('u_id')
    if not ss:
        return redirect('/login/login/')
        
    Follower.objects.filter(follower_user_id=user_id, user_id=ss).delete()
    return redirect(request.META.get('HTTP_REFERER', '/index/index3/'))

@never_cache
def chat_user(request, user_id):
    ss = request.session.get('u_id')
    if not ss or request.session.get('type') != 'user':
        return redirect('/login/login/')
        
    if str(ss) == str(user_id):
        return redirect('/index/index3/')
        
    # Check mutual follow
    am_following = Follower.objects.filter(follower_user_id=ss, user_id=user_id).exists()
    is_following_me = Follower.objects.filter(follower_user_id=user_id, user_id=ss).exists()
    
    if not (am_following and is_following_me):
        # Render a sweet alert rejection and redirect without leaking outside UI (Login Page)
        from django.http import HttpResponse # pyre-ignore
        return HttpResponse(f"""
        <html><head>
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&display=swap" rel="stylesheet">
        </head><body style="background:#050505; margin:0;">
        <script>
            Swal.fire({{
                icon: 'error',
                title: '<span style="font-family:\\'Orbitron\\', sans-serif;">Protocol Blocked</span>',
                html: 'Permission Denied: You must <b>mutually follow</b> each other to initiate an encrypted chat.',
                background: 'rgba(15, 15, 20, 0.95)',
                color: '#fff',
                confirmButtonColor: '#bc13fe',
                backdrop: 'rgba(0,0,0,0.9)'
            }}).then(function() {{
                window.location.href = '/index/index3/';
            }});
        </script>
        </body></html>
        """)
        
    target_user = Register.objects.filter(register_id=user_id).first()
    current_user_obj = Register.objects.get(register_id=ss)
    if not target_user:
        return redirect('/login/messages/')
    timer = timer_for(ss, user_id)
    
    # Handle new message submission
    if request.method == 'POST':
        msg_content = request.POST.get('content')
        duration = timer.duration
        if msg_content:
            # The Apex Protocol: Deep-Linguistic Cognitive Behavioral Interceptor
            # Extensively upgraded with advanced Transliterated Malayalam / Hindi phonetic variations
            financial_kws = [
                'money', 'transfer', 'bank', 'gpay', 'pay', 'urgent', 'help', 'cash', 'paytm',
                'paisa', 'paise', 'rupee', 'rs', 'amount', 'send', 
                'panam', 'kaash', 'phonepe', 'upi', 'gugle', 'google pay',
                'ayacho', 'ayachal', 'mathi', 'madhi', 'kodu', 'kodukk', 'numberlekk',
                'tharam', 'tharaoh', 'fund', 'wallet', 'deposit', 'account'
            ]
            
            # Smart conversational scan using phonetics
            lower_content = msg_content.lower()
            is_financial = any(kw in lower_content for kw in financial_kws)
            if is_financial:
                from login.otp import clear_pending, issue_challenge
                clear_pending(request.session)
                request.session['pending_financial_msg'] = msg_content
                request.session['pending_financial_receiver'] = user_id
                request.session['pending_is_disappearing'] = bool(duration)
                request.session['pending_disappearing_seconds'] = duration
                sent, notice = issue_challenge(request.session, current_user_obj)
                request.session['financial_email_notice'] = notice
                request.session['financial_email_sent'] = sent
                return redirect('/login/financial_otp_verify/')
                
            create_message(ss, user_id, msg_content, duration)
            return redirect(f'/login/chat/{user_id}/')
            
    messages = list(conversation_messages(ss, user_id))
    
    context = {
        'target_user': target_user,
        'chat_messages': messages,
        'current_user_id': int(ss),
        'current_user': current_user_obj,
        'timer': timer_payload(timer), 'timer_choices': TIMER_CHOICES,
        'server_now': timezone.now().isoformat(),
    }
    
    return render(request, 'login/chat.html', context)

def messages_inbox(request):
    ss = request.session.get('u_id')
    if not ss:
        return redirect('/login/login/')
        
    # Get all users I'm following
    following = Follower.objects.filter(follower_user_id=ss).values_list('user_id', flat=True)
    # Get all users following me
    followers = Follower.objects.filter(user_id=ss).values_list('follower_user_id', flat=True)
    
    # Mutual followers intersection
    mutual_ids = set(following).intersection(set(followers))
    
    # Fetch those user objects
    mutual_users = Register.objects.filter(register_id__in=mutual_ids)
    current_user_obj = Register.objects.get(register_id=ss)
    
    context = {
        'mutual_users': mutual_users,
        'current_user': current_user_obj
    }
    return render(request, 'login/messages.html', context)

@require_POST
def read_disappearing_message(request, message_id):
    ss = request.session.get('u_id')
    if not ss or request.session.get('type') != 'user':
        return redirect('/login/login/')
    msg = Message.objects.filter(message_id=message_id, receiver_id=ss).first()
    if not msg or not can_chat(ss, msg.sender_id):
        return JsonResponse({'error': 'Message unavailable.'}, status=404)
    if msg.expires_at and msg.expires_at <= timezone.now():
        msg.delete()
        return JsonResponse({'error': 'Message expired.'}, status=404)
    msg.is_read = 1
    msg.save(update_fields=['is_read'])
    return redirect(f'/login/chat/{msg.sender_id}/')


@never_cache
@require_GET
def chat_state(request, user_id):
    ss = request.session.get('u_id')
    if not ss or request.session.get('type') != 'user':
        return JsonResponse({'error': 'Please sign in again.'}, status=401)
    if not can_chat(ss, user_id):
        return JsonResponse({'error': 'This conversation is no longer available.'}, status=403)
    timer = timer_for(ss, user_id)
    now = timezone.now()
    messages = list(conversation_messages(ss, user_id, now))
    html = render_to_string('login/chat_messages.html',
                            {'chat_messages': messages, 'current_user_id': int(ss)})
    return JsonResponse({'timer': timer_payload(timer), 'server_now': now.isoformat(), 'html': html})


@never_cache
@require_POST
def chat_timer(request, user_id):
    ss = request.session.get('u_id')
    if not ss or request.session.get('type') != 'user':
        return JsonResponse({'error': 'Please sign in again.'}, status=401)
    if not can_chat(ss, user_id):
        return JsonResponse({'error': 'Both people must follow each other.'}, status=403)
    try:
        duration = int(request.POST['duration'])
        revision = int(request.POST['revision'])
        if duration not in dict(TIMER_CHOICES) or revision < 0:
            raise ValueError
    except (KeyError, ValueError):
        return JsonResponse({'error': 'Choose a valid message timer.'}, status=400)
    timer, saved = update_timer(timer_for(ss, user_id), duration, revision, ss)
    payload = {'timer': timer_payload(timer), 'server_now': timezone.now().isoformat()}
    if not saved:
        payload['error'] = 'The timer changed in another window. Review the current setting and try again.'
    return JsonResponse(payload, status=200 if saved else 409)

def financial_otp_verify(request):
    from login.otp import challenge_state, clear_pending, issue_challenge, verify_challenge
    ss = request.session.get('u_id')
    if not ss or request.session.get('type') != 'user':
        return redirect('/login/login/')
    if not request.session.get('pending_financial_msg') or not request.session.get('pending_financial_receiver'):
        return redirect('/index/index3/')
    current_user = Register.objects.filter(register_id=ss).first()
    if not current_user:
        clear_pending(request.session)
        return redirect('/login/login/')
    notice = request.session.pop('financial_email_notice', '')
    sent = request.session.pop('financial_email_sent', False)
    context = {
        'current_user': current_user, 'email': current_user.email,
        'email_domain': current_user.email.rsplit('@', 1)[-1],
        'delivery_notice': notice, 'delivery_status': 'success' if sent else 'error',
    }
    if request.method == 'POST':
        action = request.POST.get('action', 'verify')
        if action == 'cancel':
            clear_pending(request.session)
            return redirect('/index/index3/')
        if action == 'resend':
            sent, notice = issue_challenge(request.session, current_user)
            context.update(delivery_notice=notice, delivery_status='success' if sent else 'error')
        else:
            receiver = request.session.get('pending_financial_receiver')
            # Recheck permission: a follow relationship may have changed since sending the email.
            mutual = (Follower.objects.filter(follower_user_id=ss, user_id=receiver).exists()
                      and Follower.objects.filter(follower_user_id=receiver, user_id=ss).exists())
            if not mutual or str(ss) == str(receiver):
                clear_pending(request.session)
                return redirect('/login/messages/')
            valid, error = verify_challenge(request.session, current_user, request.POST.get('otp', '').strip())
            if valid:
                create_message(ss, receiver, request.session['pending_financial_msg'],
                               request.session.get('pending_disappearing_seconds',
                                   86400 if request.session.get('pending_is_disappearing') else 0))
                clear_pending(request.session)
                notices.success(request, 'Your email was verified and your message was sent.', extra_tags='verification')
                return redirect(f'/login/chat/{receiver}/')
            context.update(delivery_notice=error, delivery_status='error')
    state = challenge_state(request.session, current_user)
    context.update(state)
    if state['code_expired'] and not context.get('delivery_notice'):
        context.update(delivery_notice='Your code expired. Resend OTP to receive a new code.', delivery_status='error')
    return render(request, 'login/financial_otp.html', context)
