import os
import sys

files_to_modify = [
    r"d:\AssentTag\assentag - Copy (2)\temp\templates\temp\dashboard.html",
    r"d:\AssentTag\assentag - Copy (2)\temp\templates\temp\feed_partial.html",
    r"d:\AssentTag\assentag - Copy (2)\temp\templates\temp\notifications.html"
]

replacements = {
    "post-card": "feed-item-card",
    "post-header": "feed-item-header",
    "post-avatar": "feed-item-avatar",
    "post-user-info": "feed-item-user-info",
    "post-username": "feed-item-username",
    "post-time": "feed-item-time",
    "post-image-container": "feed-item-image-container",
    "post-image": "feed-item-image",
    "post-actions": "feed-item-actions",
    "post-stats": "feed-item-stats",
    "post-caption": "feed-item-caption",
    "post-action-links": "feed-item-action-links",
    "create-post-card": "create-feed-card",
    "comment-post-btn": "comment-feed-btn"
}

for filepath in files_to_modify:
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for old_str, new_str in replacements.items():
            content = content.replace(old_str, new_str)
            
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Sanitized: {filepath}")
    else:
        print(f"File not found: {filepath}")

print("DOM sanitation complete.")
