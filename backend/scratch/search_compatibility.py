import os

backend_path = r"c:\Users\VARSHITH\Downloads\Vein_connect_ai\backend"
for root, dirs, files in os.walk(backend_path):
    if "venv" in root or ".git" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    if "COMPATIBILITY" in content:
                        print(f"Found in: {filepath}")
            except Exception as e:
                pass
