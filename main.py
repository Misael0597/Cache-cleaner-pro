"""
main.py
Punto de entrada de CacheCleaner Pro.
"""

import sys
import os

# Agregar src al path para desarrollo y para el exe
if getattr(sys, 'frozen', False):
    # Corriendo como .exe
    base_path = sys._MEIPASS
else:
    # Corriendo como script normal
    base_path = os.path.dirname(os.path.abspath(__file__))

src_path = os.path.join(base_path, "src")
sys.path.insert(0, src_path)

from ui.app import App

if __name__ == "__main__":
    app = App()
    app.mainloop()