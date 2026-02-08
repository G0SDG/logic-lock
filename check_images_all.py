from pathlib import Path
p = Path('LogicLock/images')
for f in sorted(p.iterdir()):
    b = f.read_bytes()
    print(f.name, len(b), b[:64])
