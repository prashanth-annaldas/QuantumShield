import os

backend_dir = r"c:\Users\annal\Desktop\Full Stack Application\SIH-QDS\backend"

count = 0
for root, _, files in os.walk(backend_dir):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = content.replace("from app", "from app")
            new_content = new_content.replace("import app", "import app")
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated {filepath}")
                count += 1

print(f"Updated {count} files.")
