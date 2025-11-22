import os
import sys
from pathlib import Path

# Agregar el src al path para que pytest pueda encontrar los módulos
BASE_DIR = Path(__file__).resolve().parent
src_path = str(BASE_DIR / "src")
testproject_path = str(BASE_DIR / "src" / "testproject")

if src_path not in sys.path:
    sys.path.insert(0, src_path)
if testproject_path not in sys.path:
    sys.path.insert(0, testproject_path)

# Configurar Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "testproject.settings")

# No llamar a django.setup() aquí, pytest-django lo manejará
