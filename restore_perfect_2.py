import os

BASE_DIR = r"d:\AssentTag\assentag - Copy (2)"

files = {}

# 4. dashboard.html
files[os.path.join(BASE_DIR, "temp", "templates", "temp", "dashboard.html")] = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AssentTag - Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
    <style>
        :root { --neon-blue: #00f3ff; --magenta: #ff00ff; }
        body { font-family: 'Inter', sans-serif; background: url('/static/assets/user_bg.jpg') center/cover fixed; color: #fff; margin:0; }
        
        .secure-card {
            background: rgba(15,15,15,0.7); backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
            border-radius: 16px; padding: 2rem; box-shadow: 0 15px 35px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1); position: relative; transition: all 0.4s ease; overflow: hidden;
            max-width: 650px; margin: 2rem auto;
        }
        
        /* Animated Hover Border */
        .secure-card::before {
            content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 3px;
            background: linear-gradient(90deg, transparent, var(--neon-blue), var(--magenta), transparent);
            transition: left 0.5s ease;
        }
        .secure-card:hover::before { left: 100%; animation: sweep 2s linear infinite; }
        @keyframes sweep { 0% {left: -100%;} 100% {left: 100%;} }
        .secure-card:hover { transform: translateY(-5px); box-shadow: 0 25px 45px rgba(0,0,0,0.8); border-color: rgba(255,255,255,0.2); }

        .pill-btn {
            background: rgba(255,255,255,0.05); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.1);
            color: #fff; padding: 12px 24px; border-radius: 30px; font-weight: 800; cursor: pointer; text-transform: uppercase;
            box-shadow: 0 5px 15px rgba(0,0,0,0.3); transition: all 0.3s; margin: 5px; display: inline-flex; align-items: center; gap: 8px; text-decoration: none;
        }
        .pill-btn:hover { background: linear-gradient(135deg, rgba(0,243,255,0.2), rgba(255,0,255,0.2)); border-color: var(--neon-blue); transform: translateY(-2px); }
        
        .pill-btn i { font-size: 1.1rem; color: var(--magenta); }
        .pill-btn:hover i { color: var(--neon-blue); }
        
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 1rem; margin-bottom: 1.5rem; }
        
        .post-header { display: flex; gap: 10px; align-items: center; margin-bottom: 15px; }
        .avatar { width: 45px; height: 45px; border-radius: 50%; border: 2px solid var(--neon-blue); object-fit: cover; }
        .post-user { font-weight: 800; font-size: 1rem; color: #fff; }
        .post-time { font-size: 0.75rem; color: #999; }
        
        .post-img { width: 100%; border-radius: 8px; margin-bottom: 15px; object-fit: cover; max-height: 500px; display: block; border: 1px solid #333; }
        .post-text { font-size: 0.95rem; margin-bottom: 15px; line-height: 1.5; color: #eee; }
        
        .live-badge { position: fixed; bottom: 20px; left: 20px; background: rgba(0,0,0,0.8); border: 1px solid var(--neon-blue); padding: 8px 16px; border-radius: 30px; color: var(--neon-blue); font-weight: 800; font-size: 0.75rem; display: flex; align-items: center; gap: 8px; box-shadow: 0 0 15px rgba(0,243,255,0.3); z-index: 1000; text-transform: uppercase; }
        .live-dot { width: 8px; height: 8px; background: var(--neon-blue); border-radius: 50%; box-shadow: 0 0 10px var(--neon-blue); animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% {transform: scale(1); opacity:1;} 50% {transform: scale(1.5); opacity:0.5;} }
        
    </style>
</head>
<body>
    
    <div style="text-align: center; margin-top: 2rem;">
        <a href="/temp/user_home/" class="pill-btn"><i class="fas fa-home"></i> Home</a>
        <a href="/login/messages/" class="pill-btn"><i class="fas fa-comment-dots"></i> Messages</a>
        <a href="/image/user_view_image/" class="pill-btn"><i class="fas fa-image"></i> My Media</a>
        <a href="/login/login/" class="pill-btn" style="border-color: #ff3333;"><i class="fas fa-power-off" style="color:#ff3333;"></i> Logout</a>
    </div>

    <!-- Main Feed -->
    <div>
        {% for photo_item in p %}
        <div class="secure-card">
            <div class="post-header">
                <img class="avatar" src="/static/{{ photo_item.register.photo }}" onerror="this.src='/static/assets/default_avatar.jpg'">
                <div>
                    <div class="post-user">{{ photo_item.username|default:"assent_user" }}</div>
                    <div class="post-time">{{ photo_item.date|default:"Just now" }} • {{ photo_item.time|default:"" }}</div>
                </div>
            </div>
            
            <img src="/static/{{ photo_item.photo }}" class="post-img">
            
            <div class="post-text">
                <strong style="color:var(--magenta);">{{ photo_item.username|default:"assent_user" }}</strong> 
                {{ photo_item.caption|default:"Shared a moment on AssentTag ✨" }}
            </div>
            
            <div style="display: flex; gap: 10px;">
                <button class="pill-btn" style="padding: 8px 16px; font-size: 0.8rem;"><i class="fas fa-heart"></i> Like</button>
                <button class="pill-btn" style="padding: 8px 16px; font-size: 0.8rem;"><i class="fas fa-comment"></i> Comment</button>
            </div>
        </div>
        {% endfor %}
        
        <!-- Fallback if empty -->
        {% if not p %}
        <div class="secure-card" style="text-align: center; color: #999;">
            <i class="fas fa-eye-slash" style="font-size: 3rem; color: #333; margin-bottom: 1rem; display:block;"></i>
            <p>No public posts available in your feed.</p>
        </div>
        {% endif %}
    </div>

    <div class="live-badge">
        <div class="live-dot"></div> Live Sync: Active
    </div>

</body>
</html>"""

# 5. profile-edit.html
files[os.path.join(BASE_DIR, "register", "templates", "register", "profile-edit.html")] = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AssentTag - Profile Settings</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <style>
        :root { --neon-blue: #00f3ff; --magenta: #ff00ff; }
        body { font-family: 'Inter', sans-serif; background: url('/static/assets/user_bg.jpg') center/cover fixed; color: #fff; margin:0; display:flex; justify-content:center; align-items:center; min-height:100vh; padding: 2rem;}
        
        .profile-card {
            background: rgba(15,15,15,0.85); backdrop-filter: blur(25px);
            border-radius: 16px; padding: 2.5rem; width: 100%; max-width: 500px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.1);
        }
        
        /* Toggle Switch */
        .toggle-container { display: flex; justify-content: space-between; align-items: center; background: rgba(0,0,0,0.5); padding: 15px 20px; border-radius: 8px; border: 1px solid #333; margin-bottom: 1.5rem; }
        .toggle-label { font-weight: 800; font-size: 0.9rem; text-transform: uppercase; }
        .toggle-desc { font-size: 0.75rem; color: #999; margin-top: 4px; }
        
        .switch { position: relative; display: inline-block; width: 60px; height: 34px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #333; transition: .4s; border-radius: 34px; }
        .slider:before { position: absolute; content: ""; height: 26px; width: 26px; left: 4px; bottom: 4px; background-color: #fff; transition: .4s; border-radius: 50%; box-shadow: 0 0 10px rgba(0,0,0,0.5); }
        input:checked + .slider { background: linear-gradient(135deg, var(--neon-blue), var(--magenta)); }
        input:checked + .slider:before { transform: translateX(26px); }
        
        input[type="text"], input[type="file"] { width: 100%; background: #000; border: 1px solid #333; color: #fff; padding: 12px; border-radius: 4px; margin-bottom: 1rem; font-family: 'Inter', sans-serif; }
        .btn-save { background: linear-gradient(135deg, var(--magenta), var(--neon-blue)); border: none; padding: 14px; width: 100%; color: #fff; font-weight: 800; border-radius: 4px; cursor: pointer; text-transform: uppercase; margin-top: 1rem; }
        
    </style>
</head>
<body>
    <div class="profile-card">
        <h2 style="border-left: 4px solid var(--magenta); padding-left: 10px; margin-bottom: 2rem;">Profile Settings</h2>
        
        <form method="POST" enctype="multipart/form-data">
            {% csrf_token %}
            
            <div class="toggle-container">
                <div>
                    <div class="toggle-label">Private Account</div>
                    <div class="toggle-desc">Only approved followers can view your media feed.</div>
                </div>
                <label class="switch">
                    <input type="checkbox" name="is_private" {% if j.is_private %}checked{% endif %}>
                    <span class="slider"></span>
                </label>
            </div>
            
            <label style="font-size:0.8rem; color:#999; font-weight:800; text-transform:uppercase;">UPDATE BIO</label>
            <input type="text" name="bio" value="{{ j.bio }}">
            
            <label style="font-size:0.8rem; color:#999; font-weight:800; text-transform:uppercase;">PHONE NUMBER</label>
            <input type="text" name="mobile" value="{{ j.mobile }}">
            
            <label style="font-size:0.8rem; color:#999; font-weight:800; text-transform:uppercase;">CHANGE AVATAR</label>
            <input type="file" name="photo">
            
            <button type="submit" class="btn-save">Save Changes</button>
            <a href="/temp/user_home/" style="display:block; text-align:center; padding:12px; color:#fff; text-decoration:none; border:1px solid #333; margin-top:10px; border-radius:4px;">CANCEL</a>
        </form>
    </div>
    
    {% if msg %}
    <script>Swal.fire({ title: 'Success', text: '{{ msg }}', icon: '{{ msg_type }}', background: '#161b22', color: '#fff' });</script>
    {% endif %}
</body>
</html>"""

for file_path, content in files.items():
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
print("Perfect pristine Dashboard & Profile synthesis restored.")
