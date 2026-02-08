from pathlib import Path
import shutil

imgdir = Path('images')
backup = imgdir / 'bak'
backup.mkdir(exist_ok=True)

for p in sorted(imgdir.iterdir()):
    if not p.is_file():
        continue
    data = p.read_bytes()
    # Heuristic: file is ASCII list of numbers separated by commas if it starts with digits and commas
    if data[:8].decode('ascii', errors='ignore').strip().startswith(('137,','255,') ):
        print('Fixing', p.name)
        shutil.copy2(p, backup / p.name)
        txt = data.decode('ascii')
        nums = [int(x) for x in txt.split(',') if x.strip()]
        new = bytes(nums)
        p.write_bytes(new)
    else:
        print('Skipping (looks binary)', p.name)

print('Done')
