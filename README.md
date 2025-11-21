# Django Observatory 🔭

Django Observatory is a monitoring and debugging toolkit for Django inspired by Laravel Telescope. It provides real-time insights into requests, queries, logs, and exceptions through a clean, centralized dashboard running on a separate port to help developers analyze and optimize their applications.

## ✨ Estado actual

- ✅ Estructura del paquete configurada
- ✅ Comando de management `observatory` funcionando
- ✅ Servidor HTTP en puerto separado (8001)
- ✅ Proyecto de prueba en `src/testproject/`
- ✅ Instalación en modo desarrollo (`uv pip install -e .`)
- ✅ "Hola mundo" funcionando en http://127.0.0.1:8001

## 🚀 Quick Start

### Para desarrollo

```bash
# 1. Instalar el paquete en modo desarrollo
uv pip install -e .

# 2. Ir al proyecto de prueba
cd src/testproject

# 3. Ejecutar el panel Observatory
./run_observatory.fish
# o manualmente:
# /path/to/.venv/bin/python manage.py observatory --port 8001
```

Abre http://127.0.0.1:8001 y verás el "Hola mundo" del Observatory.

### Para usar en otros proyectos

1. **Instalar el paquete:**

```bash
pip install django-observatory
```

2. **Añadir a `INSTALLED_APPS` en `settings.py`:**

```python
INSTALLED_APPS = [
    # ... otras apps
    'django_observatory',
]
```

3. **Ejecutar el panel Observatory:**

```bash
python manage.py observatory --port 8001
```

4. **Abrir en el navegador:** http://127.0.0.1:8001

## 🔧 Desarrollo

El proyecto incluye un proyecto Django de prueba en `src/testproject/` configurado para desarrollo rápido:

- **Scripts Fish** para facilitar el desarrollo (`run_server.fish`, `run_observatory.fish`)
- **Modo editable**: Los cambios en `src/django_observatory/` se aplican inmediatamente
- Ver [src/testproject/README.md](src/testproject/README.md) para más detalles

## 📁 Estructura del proyecto

```
Django-Observatory/
├── src/
│   ├── django_observatory/          # El paquete
│   │   ├── __init__.py
│   │   ├── apps.py                 # DjangoObservatoryConfig
│   │   └── management/
│   │       └── commands/
│   │           └── observatory.py   # Comando: python manage.py observatory
│   └── testproject/                 # Proyecto de prueba
│       ├── manage.py
│       ├── run_observatory.fish     # Script helper
│       └── testproject/
│           └── settings.py          # django_observatory configurado
├── pyproject.toml
└── README.md
```

## 🎯 Roadmap

- [x] Configuración básica del paquete
- [x] Comando de management
- [x] Servidor en puerto separado con "Hola mundo"
- [ ] Integrar Django templates y sistema de rutas
- [ ] Panel con interfaz web moderna (HTML/CSS/JS)
- [ ] Captura de requests HTTP
- [ ] Logging de queries SQL
- [ ] Visualización de cache hits/misses
- [ ] Monitoreo de jobs y tasks
- [ ] Autenticación y seguridad
- [ ] WebSockets para updates en tiempo real

## 📄 Licencia

MIT
