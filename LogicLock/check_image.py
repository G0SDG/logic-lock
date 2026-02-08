from pathlib import Path
p = Path('LogicLock/images/dirt.png')
print('exists', p.exists())
print('size', p.stat().st_size)
print('head', p.read_bytes()[:16])
