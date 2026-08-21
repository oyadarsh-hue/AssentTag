import os

def sanitize(directory):
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name.endswith('.html'):
                filepath = os.path.join(root, name)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                new_content = content.replace('feed-item-', 'secure-card-').replace('feed-container', 'content-wrapper')
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Sanitized: {filepath}")

if __name__ == '__main__':
    sanitize('temp/templates/temp')
