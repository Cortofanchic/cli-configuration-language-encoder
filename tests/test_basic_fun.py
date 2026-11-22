import glob
import os
import subprocess


os.makedirs("basic_tests", exist_ok=True)
files = sorted(glob.glob("basic_tests/*.txt"))

for f in files:
    name = os.path.splitext(f)[0]
    print(f"{name.upper().split('\\')[-1]}")
    res = subprocess.run(
        ["python", "../src/cli.py", f],
        capture_output=True, text=True, check=True
    )
    lines = res.stdout.splitlines()
    print("\n".join(lines), end="\n\n")

print("End task")