# code_tools.py
import os

def save_code_snapshot(output_file="code_snapshot.txt"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, output_file)

    with open(output_path, "w", encoding="utf-8") as out:
        for root, _, files in os.walk(base_dir):
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                # skip this helper file to avoid recursion confusion
                if os.path.abspath(os.path.join(root, fname)) == os.path.abspath(__file__):
                    continue
                path = os.path.join(root, fname)
                rel_path = os.path.relpath(path, base_dir)
                out.write(f"\n===== [{rel_path}] =====\n")
                try:
                    with open(path, "r", encoding="utf-8") as src:
                        out.write(src.read())
                        out.write("\n")
                except Exception:
                    out.write("# Error reading file\n")
    print(f"[OK] Снимок кода сохранён в: {output_path}")
