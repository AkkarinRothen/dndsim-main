# Guía Rápida de Solución de Problemas - Windows

## 🚨 Problemas Comunes y Soluciones

### 1. Error: "Python no reconocido como comando"

**Causa**: Python no está en el PATH del sistema.

**Solución**:
1. Reinstala Python desde https://www.python.org/downloads/
2. ✅ **IMPORTANTE**: Marca la casilla "Add Python to PATH" durante la instalación
3. O añade Python manualmente al PATH:
   - Busca "Variables de entorno" en Windows
   - Edita la variable PATH
   - Añade: `C:\Users\TuUsuario\AppData\Local\Programs\Python\Python3XX`

### 2. Error: "No module named 'flask'"

**Causa**: Flask no está instalado o no estás en el entorno virtual.

**Solución**:
```cmd
# Activa el entorno virtual
venv\Scripts\activate.bat

# Instala las dependencias
pip install -r requirements.txt
```

### 3. Error: "TemplateNotFound: index.html"

**Causa**: El archivo `index.html` no está en la carpeta `templates/`.

**Solución**:
```cmd
# Opción 1: Mover el archivo
move index.html templates\

# Opción 2: Verificar estructura
dir templates\
```

**Estructura correcta**:
```
C:\Users\yacri\Downloads\dndsim-main\dndsim-main\python\
├── app.py
├── templates\
│   └── index.html
├── combat_manager.py
├── monster_parser.py
└── ...
```

### 4. Error: "No such file or directory: configs.py"

**Causa**: Faltan archivos del proyecto original.

**Solución**:
Asegúrate de tener estos archivos en la raíz:
- `configs.py`
- `monster_configs.py`
- `colors.py`
- `constants.py`
- `simulator_exceptions.py`
- Carpeta `sim/` con los módulos de simulación

### 5. Error al ejecutar: "Cannot find venv\Scripts\activate.bat"

**Causa**: El entorno virtual no se creó correctamente.

**Solución**:
```cmd
# Elimina la carpeta venv si existe
rmdir /s /q venv

# Crea un nuevo entorno virtual
python -m venv venv

# Actívalo
venv\Scripts\activate.bat
```

### 6. Error: "Address already in use" (Puerto 5000 ocupado)

**Causa**: Otro programa está usando el puerto 5000.

**Solución A - Cambiar puerto**:
```cmd
# En .env, cambia:
FLASK_PORT=8000
```

**Solución B - Liberar el puerto**:
```cmd
# Ver qué proceso usa el puerto 5000
netstat -ano | findstr :5000

# Matar el proceso (reemplaza PID con el número que aparece)
taskkill /PID <PID> /F
```

### 7. Error de JavaScript en el navegador

**Causa**: Caché del navegador o archivos antiguos.

**Solución**:
1. Presiona `Ctrl + Shift + R` para recargar sin caché
2. O abre DevTools (F12) → Network → Marca "Disable cache"
3. Cierra y vuelve a abrir el navegador

### 8. Error: "Secret key not set"

**Causa**: Falta la variable SECRET_KEY.

**Solución**:
Asegúrate de que existe el archivo `.env` con:
```
SECRET_KEY=cualquier-texto-aleatorio-aqui
```

### 9. La página carga pero no responde

**Causa**: Error en la API o en el backend.

**Solución**:
1. Abre DevTools del navegador (F12)
2. Ve a la pestaña "Console"
3. Ve a la pestaña "Network"
4. Intenta iniciar combate y busca errores rojos
5. Revisa la consola donde corre Flask para ver errores del servidor

### 10. Error: "ImportError: cannot import name 'X'"

**Causa**: Estructura de módulos incorrecta o archivos faltantes.

**Solución**:
```cmd
# Verifica la estructura del proyecto
dir /s *.py

# Asegúrate de tener:
# - sim\__init__.py
# - sim\party_sim.py
# - sim\monster.py
# - sim\resource_tracker.py
```

## 📋 Checklist de Verificación

Antes de ejecutar, verifica:

- [ ] Python 3.8+ instalado (`python --version`)
- [ ] Entorno virtual creado (`venv\Scripts\activate.bat`)
- [ ] Dependencias instaladas (`pip list | findstr Flask`)
- [ ] `index.html` en carpeta `templates\`
- [ ] Archivo `.env` existe
- [ ] Archivos del proyecto presentes (`app.py`, `configs.py`, etc.)
- [ ] Carpeta `sim\` con módulos

## 🔍 Comandos Útiles de Diagnóstico

```cmd
REM Ver versión de Python
python --version

REM Ver paquetes instalados
pip list

REM Ver estructura de archivos
tree /F

REM Verificar puerto 5000
netstat -ano | findstr :5000

REM Ver variables de entorno
set

REM Probar importaciones
python -c "import flask; print('Flask OK')"
python -c "import configs; print('Configs OK')"
```

## 🆘 Si Nada Funciona

1. **Borra todo y empieza de nuevo**:
   ```cmd
   rmdir /s /q venv
   del .env
   ```

2. **Ejecuta el setup**:
   ```cmd
   setup.bat
   ```

3. **Corre el programa**:
   ```cmd
   run.bat
   ```

4. **Revisa los logs** en la consola donde corre Flask

5. **Abre DevTools** (F12) en el navegador y revisa errores

## 📞 Información de Debug Útil

Si necesitas pedir ayuda, proporciona:
- Versión de Python (`python --version`)
- Sistema operativo (`winver`)
- Mensaje de error completo
- Resultado de `pip list`
- Estructura de archivos (`dir /s *.py`)

## 🔗 Recursos

- [Python para Windows](https://www.python.org/downloads/windows/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Python venv](https://docs.python.org/3/library/venv.html)
