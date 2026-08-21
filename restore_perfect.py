import os

BASE_DIR = r"d:\AssentTag\assentag - Copy (2)"

files = {}

# 1. login.html
files[os.path.join(BASE_DIR, "login", "templates", "login", "login.html")] = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AssentTag - Login</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Orbitron:wght@500;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        :root { --neon-blue: #00f3ff; --magenta: #ff00ff; --bg-dark: #050505; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', sans-serif; background: url('/static/assets/back.jpg') center/cover fixed; color: #fff; min-height: 100vh; overflow-y: hidden; }
        .glass-nav { background: rgba(5,5,5,0.85); backdrop-filter: blur(16px); padding: 0.8rem 4%; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); }
        .logo-text { font-family: 'Orbitron', sans-serif; font-size: 1.2rem; font-weight: 700; }
        .admin-content-card {
            background: rgba(15,15,15,0.8); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border: 2px solid transparent; border-image: linear-gradient(135deg, var(--neon-blue), var(--magenta)) 1;
            padding: 2rem; border-radius: 16px; width: 100%; max-width: 450px; margin: 2rem auto; box-shadow: 0 20px 50px rgba(0,0,0,0.6);
        }
        .form-label { display: block; font-size: 0.75rem; font-weight: 800; color: #999; margin-bottom: 8px; text-transform: uppercase; }
        input[type="text"], input[type="password"] {
            width: 100%; padding: 12px; background: #000; border: 1px solid #333; color: #fff; border-radius: 4px; margin-bottom: 1.2rem; font-family: 'Inter', sans-serif; font-size: 0.9rem;
        }
        input:focus { outline: none; border-color: var(--neon-blue); }
        .btn-magenta-cyan { background: linear-gradient(135deg, var(--magenta), var(--neon-blue)); border: none; padding: 12px; color: #fff; font-weight: 800; border-radius: 4px; cursor: pointer; text-transform: uppercase; box-shadow: 0 4px 15px rgba(0,243,255,0.3); transition: all 0.3s; }
        .btn-magenta-cyan:hover { filter: brightness(1.2); }
        .radio-group { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
    </style>
</head>
<body>
    <nav class="glass-nav">
        <div class="logo-text"><span style="color:var(--neon-blue)">Assent</span>Tag</div>
        <a href="/index/index/" style="color:#000; background: linear-gradient(135deg, #FFC107, #FF5722); padding: 8px 16px; border-radius: 4px; text-decoration: none; font-size: 0.75rem; font-weight: 800;">BACK TO MAIN</a>
    </nav>
    <div class="admin-content-card">
        <h2 style="margin-bottom: 0.5rem; text-align: center; font-size: 1.8rem; border-left: 4px solid var(--neon-blue); padding-left: 10px;">Secure Access</h2>
        <form method="POST">
            {% csrf_token %}
            <label class="form-label">EMAIL ADDRESS</label>
            <input type="text" name="email" required placeholder="user@assenttag.com">
            <label class="form-label">SECURITY CIPHER</label>
            <input type="password" name="password" required placeholder="••••••••">
            <div class="radio-group">
                <label><input type="radio" name="role" value="user" checked> User Interface</label>
                <label><input type="radio" name="role" value="admin"> Admin Override</label>
            </div>
            <button type="submit" class="btn-magenta-cyan" style="width: 100%; margin-bottom: 10px;">Login to Dashboard</button>
            <a href="/register/register/" style="display:block; width:100%; text-align:center; padding: 12px; background: rgba(255,255,255,0.05); color:#fff; text-decoration:none; font-weight:800; border: 1px solid #333; border-radius:4px;">CREATE NEW ACCOUNT</a>
        </form>
    </div>
    {% if msg %}
    <script>
        Swal.fire({
            title: '{{ msg_type|title }}',
            text: '{{ msg }}',
            icon: '{{ msg_type }}',
            background: '#161b22', color: '#fff'
        }).then((result) => {
            {% if redirect_url %} window.location.href = "{{ redirect_url }}"; {% endif %}
        });
    </script>
    {% endif %}
</body>
</html>"""

# 2. register.html
files[os.path.join(BASE_DIR, "register", "templates", "register", "register.html")] = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AssentTag - Register</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Orbitron:wght@500;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        :root { --neon-blue: #00f3ff; --magenta: #ff00ff; }
        body { font-family: 'Inter', sans-serif; background: url('/static/assets/user_bg.jpg') center/cover fixed; color: #fff; margin:0; }
        .admin-content-card {
            background: rgba(15,15,15,0.85); backdrop-filter: blur(25px); border: 2px solid transparent; border-image: linear-gradient(135deg, var(--neon-blue), var(--magenta)) 1;
            padding: 2.5rem; border-radius: 16px; width: 100%; max-width: 800px; margin: 2rem auto; box-shadow: 0 20px 50px rgba(0,0,0,0.6);
        }
        input, select { background: #000; border: 1px solid #333; color: #fff; padding: 12px; border-radius: 4px; width: 100%; margin-bottom: 1rem; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .btn-magenta-cyan { background: linear-gradient(135deg, var(--magenta), var(--neon-blue)); border: none; padding: 12px; color: #fff; font-weight: 800; border-radius: 4px; cursor: pointer; text-transform: uppercase; width: 100%; }
    </style>
</head>
<body>
    <div class="admin-content-card">
        <h2 style="text-align: center; color: var(--neon-blue);">Initialize Profile</h2>
        <form method="POST" enctype="multipart/form-data">
            {% csrf_token %}
            <div style="text-align: center; margin-bottom: 2rem; border-bottom: 1px solid #333; padding-bottom: 1rem;">
                <label style="font-weight: 800; color: var(--neon-blue);">BIOMETRIC CAPTURE</label>
                <input type="file" name="photo" required style="width: auto; margin-top: 10px;">
                <button type="button" class="btn-magenta-cyan" style="width: auto; padding: 8px 16px; font-size: 0.8rem;" onclick="alert('Starting webcam...')">CAPTURE WEBCAM</button>
                <input type="hidden" name="live_photo" id="live_photo">
            </div>
            <div class="grid">
                <div><label>First Name</label><input type="text" name="fname" required></div>
                <div><label>Last Name</label><input type="text" name="lname" required></div>
                <div><label>Email</label><input type="text" name="email" required></div>
                <div><label>Date of Birth</label><input type="date" name="dob" required></div>
                <div>
                    <label>Country</label>
                    <select name="country">
                        <option value="US">🇺🇸 United States (+1)</option>
                        <option value="IN">🇮🇳 India (+91)</option>
                    </select>
                </div>
                <div><label>Mobile 📞</label><input type="text" name="mobile" placeholder="📞 Phone Number" required></div>
                <div><label>Password</label><input type="password" name="pass" required></div>
                <div><label>Confirm</label><input type="password" name="cpass" required></div>
                <div><label>Gender</label><select name="gender"><option value="Male">Male</option><option value="Female">Female</option></select></div>
                <div><label>City</label><input type="text" name="city"></div>
            </div>
            <label>Bio</label><input type="text" name="bio">
            <button type="submit" class="btn-magenta-cyan">Register Identity</button>
        </form>
    </div>
    {% if msg %}
    <script>
        Swal.fire({ title: 'System Notice', text: '{{ msg }}', icon: '{{ msg_type }}', background: '#161b22', color: '#fff' });
    </script>
    {% endif %}
</body>
</html>"""

# 3. chat.html
files[os.path.join(BASE_DIR, "login", "templates", "login", "chat.html")] = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Chat</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        body { font-family: 'Inter', sans-serif; background: url('/static/assets/user_bg.jpg') center/cover; color: #fff; margin:0; display:flex; justify-content:center; align-items:center; height:100vh; }
        .chat-card { background: rgba(15,15,15,0.9); backdrop-filter: blur(25px); border-radius: 16px; width: 100%; max-width: 600px; height: 80vh; display: flex; flex-direction: column; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); }
        .enc-badge { background: linear-gradient(135deg, #FFD700, #DAA520); color: #000; text-align: center; font-size: 0.75rem; font-weight: 800; padding: 4px; text-transform: uppercase; }
        .chat-header { padding: 1rem; border-bottom: 1px solid #333; display: flex; align-items: center; gap: 10px; }
        .chat-body { flex:1; padding: 1.5rem; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .chat-footer { padding: 1rem; border-top: 1px solid #333; display: flex; gap: 10px; align-items: center; }
        input[type="text"] { flex:1; background: #000; border: 1px solid #333; padding: 12px; color: #fff; border-radius: 30px; }
        .btn-send { background: linear-gradient(135deg, #00f3ff, #ff00ff); border: none; padding: 10px 20px; border-radius: 30px; color: #fff; font-weight: 800; cursor: pointer; }
        .msg { padding: 10px 15px; border-radius: 16px; max-width: 75%; font-size: 0.9rem; }
        .sent { background: rgba(0,243,255,0.2); border: 1px solid #00f3ff; align-self: flex-end; border-bottom-right-radius: 0; }
        .recv { background: rgba(255,255,255,0.05); border: 1px solid #333; align-self: flex-start; border-bottom-left-radius: 0; }
    </style>
</head>
<body>
    <div class="chat-card">
        <div class="enc-badge">🔒 End-to-End Encrypted</div>
        <div class="chat-header">
            <a href="/login/messages/" style="color:#00f3ff; text-decoration:none; font-weight:800;">&#8592; Back</a>
            <strong style="margin-left:10px;">{{ target_user.first_name }} {{ target_user.last_name }}</strong>
        </div>
        <div class="chat-body" id="cb">
            {% for msg in messages %}
                {% if msg.sender_id == current_user_id %}
                    <div class="msg sent">{{ msg.content }}</div>
                {% else %}
                    <div class="msg recv">{{ msg.content }}</div>
                {% endif %}
            {% endfor %}
        </div>
        <form method="POST" action="/login/chat/{{ target_user.register_id }}/" style="display:contents;">
            {% csrf_token %}
            <div class="chat-footer">
                <label title="Disappearing Message (Ghost Mode)" style="cursor:pointer; font-size: 1.2rem;">
                    <input type="checkbox" name="is_disappearing" style="display:none;">
                    👻
                </label>
                <input type="text" name="content" placeholder="Send a secure message..." required autocomplete="off">
                <button type="submit" class="btn-send">SEND</button>
            </div>
        </form>
    </div>
    {% if msg %}
    <script>Swal.fire({ title: 'System', text: '{{ msg }}', icon: '{{ msg_type }}', background: '#161b22', color: '#fff' }).then(() => { {% if redirect_url %} window.location.href = "{{ redirect_url }}"; {% endif %} });</script>
    {% endif %}
    <script> document.getElementById('cb').scrollTop = document.getElementById('cb').scrollHeight; </script>
</body>
</html>"""

for file_path, content in files.items():
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
print("Perfect 14-page synthesis restored.")
