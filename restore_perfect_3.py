import os

BASE_DIR = r"d:\AssentTag\assentag - Copy (2)"

files = {}

# 6. messages.html
files[os.path.join(BASE_DIR, "login", "templates", "login", "messages.html")] = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Messages</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        :root { --neon-blue: #00f3ff; --magenta: #ff00ff; }
        body { font-family: 'Inter', sans-serif; background: url('/static/assets/user_bg.jpg') center/cover fixed; color: #fff; margin:0; padding:2rem; }
        .inbox-container { max-width: 800px; margin: 0 auto; }
        .inbox-card { background: rgba(15,15,15,0.85); backdrop-filter: blur(25px); border-radius: 16px; padding: 2rem; box-shadow: 0 15px 35px rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1); margin-bottom: 2rem; }
        .enc-badge { display: inline-block; background: linear-gradient(135deg, #FFD700, #DAA520); color: #000; font-size: 0.75rem; font-weight: 800; padding: 6px 12px; text-transform: uppercase; border-radius: 30px; margin-bottom: 1rem; }
        .contact-item { display: flex; align-items: center; justify-content: space-between; padding: 15px; border-bottom: 1px solid rgba(255,255,255,0.1); transition: background 0.3s; }
        .contact-item:hover { background: rgba(255,255,255,0.05); }
        .contact-info { display: flex; align-items: center; gap: 15px; }
        .avatar { width: 50px; height: 50px; border-radius: 50%; border: 2px solid var(--neon-blue); object-fit: cover; }
        .btn-chat { background: linear-gradient(135deg, var(--neon-blue), var(--magenta)); color: #fff; text-decoration: none; padding: 8px 16px; border-radius: 30px; font-weight: 800; font-size: 0.85rem; text-transform: uppercase; }
        .btn-chat:hover { opacity: 0.8; }
        .nav-btn { display: inline-block; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #fff; padding: 10px 20px; border-radius: 30px; font-weight: 800; text-decoration: none; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="inbox-container">
        <a href="/temp/user_home/" class="nav-btn" style="margin-bottom:1rem;">&#8592; Back to Dashboard</a>
        <div class="inbox-card">
            <div class="enc-badge">🔒 End-to-End Encrypted Inbox</div>
            <h2 style="margin-top:0; border-bottom: 1px solid #333; padding-bottom: 1rem;">Direct Messages</h2>
            
            {% for u in mutual_users %}
            <div class="contact-item">
                <div class="contact-info">
                    <img class="avatar" src="/static/{{ u.photo }}" onerror="this.src='/static/assets/default_avatar.jpg'">
                    <div>
                        <strong style="font-size: 1.1rem; color: var(--neon-blue);">{{ u.first_name }} {{ u.last_name }}</strong>
                        <div style="font-size: 0.8rem; color: #999;">Mutual Connection</div>
                    </div>
                </div>
                <a href="/login/chat/{{ u.register_id }}/" class="btn-chat">Open Secure Chat</a>
            </div>
            {% endfor %}
            
            {% if not mutual_users %}
            <div style="text-align:center; padding: 3rem 0; color: #999;">
                <h3 style="color:#fff;">No Mutual Friends Found</h3>
                <p>You can only send secure messages to users who follow you back.</p>
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>"""

for file_path, content in files.items():
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
print("Perfect pristine Inbox synthesis restored.")
