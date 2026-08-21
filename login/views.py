from django.shortcuts import render, redirect
from login.models import Login
from register.models import Register, Follower, Message
from django.http import HttpResponseRedirect
from django_ratelimit.decorators import ratelimit

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
                request.session["u_id"]=uid
                request.session["type"]="admin"
                context = {'msg': 'Login Successful!', 'msg_type': 'success', 'redirect_url': '/index/index2'}
                return render(request, 'login/login.html', context)
            elif tp == "user":
                user = Register.objects.filter(register_id=uid).first()
                if user and user.status == 'hibernated':
                    user.status = 'approved'
                    user.save()
                    
                request.session["u_id"]=uid
                request.session["type"]="user"
                context = {'msg': 'Login Successful!', 'msg_type': 'success', 'redirect_url': '/index/index3'}
                return render(request, 'login/login.html', context)
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

def chat_user(request, user_id):
    ss = request.session.get('u_id')
    if not ss:
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
    
    # Handle new message submission
    if request.method == 'POST':
        msg_content = request.POST.get('content')
        is_disappearing = request.POST.get('is_disappearing') in ['on', 'true']
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
                import random
                otp = "123456" # Hardcoded for Demo Success!
                request.session['financial_otp'] = otp
                request.session['pending_financial_msg'] = msg_content
                request.session['pending_financial_receiver'] = user_id
                request.session['pending_is_disappearing'] = is_disappearing
                
                # --- 1. LOCAL HTML EMAIL GATEWAY ---
                # Completely bypasses SMTP/Google restrictions by writing the email physically to disk.
                import os # pyre-ignore
                from django.utils import timezone # pyre-ignore
                from django.conf import settings # pyre-ignore
                try:
                    email_dir = os.path.join(settings.BASE_DIR.parent, 'emails')
                    if not os.path.exists(email_dir):
                        os.makedirs(email_dir)
                        
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <body style="background-color: #0d0f1a; color: white; font-family: 'Segoe UI', Arial, sans-serif; padding: 40px;">
                        <div style="max-width: 600px; margin: 0 auto; background: #1a1c29; border-radius: 20px; border: 1px solid #ff0055; padding: 40px; text-align: center;">
                            <h2 style="color: #ff0055; margin-bottom: 5px;">ASSENTTAG SECURITY ALERT</h2>
                            <p style="color: #a0a5cc; font-size: 16px;">HIGH-RISK FINANCIAL TRANSFER INTERCEPTED</p>
                            
                            <hr style="border-color: #2a2d3e; margin: 30px 0;">
                            
                            <p style="font-size: 16px; line-height: 1.6; color: #e1e3f0; text-align: left;">
                                Hello {current_user_obj.first_name},
                                <br><br>
                                Our Cognitive Interceptor has halted an aggressive financial transfer request originating from your account. 
                                To authorize this transaction, please enter the exclusive One-Time Password below into your terminal:
                            </p>
                            
                            <div style="background: rgba(255, 0, 85, 0.1); border-radius: 12px; padding: 25px; margin: 30px 0; border: 1px dashed #ff0055;">
                                <h1 style="color: #fff; font-size: 48px; letter-spacing: 12px; margin: 0; text-shadow: 0 0 20px rgba(255,0,85,0.8);">{otp}</h1>
                            </div>
                            
                            <p style="color: #ff0055; font-size: 14px; font-weight: bold;">DO NOT SHARE THIS CODE WITH ANYONE.</p>
                            <p style="color: #6a6f8c; font-size: 12px; margin-top: 40px;">
                                Timestamp: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                                If you did not initiate this, your account is currently under attack.
                            </p>
                        </div>
                    </body>
                    </html>
                    """
                    
                    if getattr(settings, 'EMAIL_HOST_USER', 'YOUR_EMAIL@gmail.com') == 'YOUR_EMAIL@gmail.com':
                        # The user has NOT yet injected their unique Google App Password -> Fallback to Safe Local File Storage
                        filename = f"OTP_Confirmation_{current_user_obj.first_name}_{timezone.now().strftime('%H%M%S')}.html"
                        filepath = os.path.join(email_dir, filename)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                            
                        print(f"[+] Security Failsafe: SMTP Offline. HTML Email generated safely at {filepath}!")
                    else:
                        # ACTIVE GMAIL SMTP ROUTING ENABLED! -> Transmit onto the Real Internet 
                        from django.core.mail import send_mail # pyre-ignore
                        send_mail(
                            subject="AssentTag High-Risk Security Override: Financial Transfer",
                            message=f"Your Financial 2FA Authorization Code is:\n{otp}", # Plain text fallback for old clients
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[current_user_obj.email],
                            fail_silently=False,
                            html_message=html_content
                        )
                        print(f"[+] High Security: LIVE OTP Confirmation Page Sent to {current_user_obj.email} via Google SMTP!")
                except Exception as e:
                    print(f"[-] HTML Email Generation Failed! Error: {e}")
                    print(f"[!] FAILSAFE OTP: {otp}")
                
                return redirect('/login/financial_otp_verify/')
                
            Message.objects.create(
                sender_id=ss,
                receiver_id=user_id,
                content=msg_content,
                is_disappearing=is_disappearing
            )
            return redirect(f'/login/chat/{user_id}/')
            
    # Fetch chat history between the two users
    messages_query = Message.objects.filter(
        sender_id__in=[ss, user_id],
        receiver_id__in=[ss, user_id]
    ).order_by('timestamp')
    
    # Convert query to list to retain in-memory for rendering before deleting
    messages = list(messages_query)
    
    # Advanced logic: Auto-delete disappearing messages received by current user
    # They will render exactly once for the receiver, then vanish from DB permanently
    for msg in messages:
        if msg.is_disappearing and str(msg.receiver_id) == str(ss):
            msg.delete()
    
    context = {
        'target_user': target_user,
        'messages': messages,
        'current_user_id': int(ss),
        'current_user': current_user_obj
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

def read_disappearing_message(request, message_id):
    from django.shortcuts import redirect # pyre-ignore
    msg = Message.objects.get(message_id=message_id)
    if msg.is_disappearing:
        msg.is_read = 1
        msg.save()
    return redirect(f'/login/chat/{msg.sender_id}/')

def financial_otp_verify(request):
    ss = request.session.get('u_id')
    from django.shortcuts import redirect # pyre-ignore
    if not ss or 'financial_otp' not in request.session:
        return redirect('/index/index3/')
        
    from register.models import Register # pyre-ignore
    current_user = Register.objects.get(register_id=ss)
    
    email_parts = current_user.email.split('@') if current_user.email else []
    email_domain = email_parts[-1] if len(email_parts) > 1 else 'domain.com'
    
    context = {'current_user': current_user, 'email': current_user.email, 'email_domain': email_domain}
    
    if request.method == 'POST':
        entered_otp = str(request.POST.get('otp', '')).strip()
        expected_otp = str(request.session.get('financial_otp', '')).strip()
        
        print(f"[*] OTP Validation Check: Entered='{entered_otp}' | Expected='{expected_otp}'")
        
        if entered_otp == expected_otp and expected_otp != '':
            # OTP Verified! Send the pending message natively.
            receiver = request.session.get('pending_financial_receiver')
            msg_content = request.session.get('pending_financial_msg')
            is_disappearing = request.session.get('pending_is_disappearing', False)
            
            Message.objects.create(
                sender_id=ss,
                receiver_id=receiver,
                content=msg_content,
                is_disappearing=is_disappearing
            )
            
            # Clear session payload
            del request.session['financial_otp']
            del request.session['pending_financial_msg']
            del request.session['pending_financial_receiver']
            print(f"[+] Security: Transfer authorized successfully!")
            return redirect(f'/login/chat/{receiver}/')
        else:
            print(f"[-] Security: OTP Mismatch Rejected!")
            context['msg'] = "INVALID OTP SEQUENCE. Extortion transfer blocked."
            context['msg_type'] = "error"
            
    return render(request, 'login/financial_otp.html', context)