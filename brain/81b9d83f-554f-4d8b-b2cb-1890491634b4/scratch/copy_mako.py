import os
import shutil
import alembic

# Find the alembic package directory
alembic_dir = os.path.dirname(alembic.__file__)
mako_src = os.path.join(alembic_dir, "templates", "generic", "script.py.mako")

dest_dir = r"C:\Users\VARSHITH\Downloads\Vein_connect_ai\backend\alembic"
mako_dest = os.path.join(dest_dir, "script.py.mako")

if os.path.exists(mako_src):
    print(f"Found standard template at: {mako_src}")
    shutil.copy(mako_src, mako_dest)
    print(f"Successfully copied to: {mako_dest}")
else:
    # Check other templates directories in case
    print(f"Not found at {mako_src}. Checking other templates...")
    templates_dir = os.path.join(alembic_dir, "templates")
    if os.path.exists(templates_dir):
        print("Available templates folders:", os.listdir(templates_dir))
    else:
        print("Templates folder not found in alembic package.")
