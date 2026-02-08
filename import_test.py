import importlib
modules = ['pygame', 'LogicLock.camera', 'LogicLock.map', 'LogicLock.sprite', 'LogicLock.player', 'LogicLock.input']
for m in modules:
    mod = importlib.import_module(m)
    print(m, '->', mod.__file__)
print('IMPORT TEST OK')
