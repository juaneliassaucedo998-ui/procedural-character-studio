"""Crea el ZIP del proyecto (excluye .venv, __pycache__ y workspace)."""
import os, sys, zipfile
root = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "..", "procedural_character_studio.zip")
skip = {".venv", "__pycache__", "workspace", ".git"}
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for d, dirs, files in os.walk(root):
        dirs[:] = [x for x in dirs if x not in skip]
        for f in files:
            p = os.path.join(d, f)
            if os.path.abspath(p) == os.path.abspath(out):
                continue
            z.write(p, os.path.join("procedural_character_studio", os.path.relpath(p, root)))
print("ZIP creado:", out)
