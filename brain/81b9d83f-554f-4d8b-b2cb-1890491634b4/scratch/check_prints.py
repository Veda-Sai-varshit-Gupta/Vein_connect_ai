import os

app_dir = r"C:\Users\VARSHITH\Downloads\Vein_connect_ai\backend\app"
found = False

for root, dirs, files in os.walk(app_dir):
    for file in files:
        if file.endswith(".py"):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if "print(" in line:
                            # Check if the print line contains any emoji / non-ASCII character
                            non_ascii = [c for c in line if ord(c) > 127]
                            if non_ascii:
                                rel_path = os.path.relpath(file_path, app_dir)
                                print(f"File: app/{rel_path} | Line {i+1}: {line.strip()}")
                                found = True
            except Exception as e:
                pass

if not found:
    print("No print calls containing emojis or non-ASCII characters found.")
