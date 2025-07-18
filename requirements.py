import subprocess
import sys

dependencias = ['pyautogui', 'keyboard','tkinter']

for paquete in dependencias:
    try:
        __import__(paquete)
        print(f"{paquete} already installed")
    except ImportError:
        print(f"downloading {paquete}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', paquete])

print("dependencies have been succesfully installed")
