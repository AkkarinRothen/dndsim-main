# 🎮 D&D 5e Combat Simulator - Inicio Rápido para Windows

## ⚡ Instalación en 3 Pasos

### Paso 1: Preparar el Proyecto

1. **Extrae todos los archivos** en una carpeta, por ejemplo:
   ```
   C:\Users\yacri\Downloads\dndsim-main\dndsim-main\python\
   ```

2. **Verifica que tengas esta estructura**:
   ```
   python\
   ├── app.py                    ← Nuevo (mejorado)
   ├── index.html               ← Nuevo (mejorado)
   ├── combat_manager.py        ← Nuevo (mejorado)
   ├── combat_presets.py        ← Nuevo (mejorado)
   ├── monster_parser.py        ← Nuevo (mejorado)
   ├── test_app.py              ← Nuevo (mejorado)
   ├── setup.bat                ← Script de instalación
   ├── run.bat                  ← Script para ejecutar
   ├── requirements.txt         ← Dependencias
   ├── configs.py               ← Existente
   ├── monster_configs.py       ← Existente
   ├── colors.py                ← Existente
   ├── constants.py             ← Existente
   ├── simulator_exceptions.py  ← Existente
   └── sim\                     ← Carpeta existente
       ├── __init__.py
       ├── party_sim.py
       ├── monster.py
       └── resource_tracker.py
   ```

### Paso 2: Ejecutar la Instalación

1. **Haz doble clic en `setup.bat`**
   
   Esto automáticamente:
   - ✅ Verifica que Python esté instalado
   - ✅ Crea un entorno virtual
   - ✅ Instala todas las dependencias
   - ✅ Crea el archivo `.env`
   - ✅ Mueve `index.html` a `templates/`

2. **Espera a que termine** (puede tomar 1-2 minutos)

### Paso 3: Ejecutar la Aplicación

1. **Haz doble clic en `run.bat`**

2. **Abre tu navegador** y ve a:
   ```
   http://127.0.0.1:5000
   ```

3. **¡Listo!** Deberías ver el simulador de combate

## 🎯 Uso del Simulador

### Iniciar un Combate

1. **Selecciona el nivel** del grupo (1-20)

2. **Elige los miembros del grupo**:
   - Mantén presionado `Ctrl` para seleccionar múltiples
   - Ejemplo: Fighter, Wizard, Rogue, Cleric

3. **Agrega enemigos**:
   - Selecciona el tipo de monstruo
   - Indica la cantidad
   - Presiona "+ Add Enemy Type" para más tipos

4. **Presiona "⚔️ Start Combat"**

### Durante el Combate

- **▶️ Next Turn**: Ejecuta el siguiente turno
- **🔄 New Combat**: Reinicia y vuelve a la configuración

### Usar Presets

En lugar de configurar manualmente:
1. Selecciona un preset del menú desplegable
2. Se cargarán automáticamente:
   - Nivel del grupo
   - Personajes
   - Enemigos
3. Presiona "⚔️ Start Combat"

## 📁 Estructura de Archivos

### Archivos que DEBES tener

**Nuevos (mejorados)**:
- `app.py` - Backend Flask mejorado
- `combat_manager.py` - Gestor de combate mejorado
- `combat_presets.py` - Presets de combate
- `monster_parser.py` - Parser de monstruos mejorado
- `test_app.py` - Tests completos
- `templates/index.html` - Interfaz web mejorada

**Existentes (del proyecto original)**:
- `configs.py` - Configuraciones de personajes
- `monster_configs.py` - Configuraciones de monstruos
- `colors.py` - Colores para CLI
- `constants.py` - Constantes del proyecto
- `simulator_exceptions.py` - Excepciones
- `sim/` - Módulos de simulación

**Generados automáticamente**:
- `venv/` - Entorno virtual (no tocar)
- `.env` - Variables de entorno
- `custom_chars/` - Personajes personalizados

## 🔧 Solución de Problemas Rápida

### ❌ Python no reconocido

**Instala Python**:
1. Ve a https://www.python.org/downloads/
2. Descarga Python 3.8 o superior
3. Durante la instalación: ✅ **MARCA "Add Python to PATH"**

### ❌ Error: TemplateNotFound

**Asegúrate de que `index.html` esté en `templates/`**:
```cmd
dir templates\index.html
```

Si no está ahí:
```cmd
mkdir templates
move index.html templates\
```

### ❌ La página no carga

1. Verifica que Flask esté corriendo (consola debe decir "Running on http://127.0.0.1:5000")
2. Presiona `Ctrl + Shift + R` en el navegador para recargar sin caché
3. Abre DevTools (F12) y busca errores en la consola

### ❌ Puerto 5000 ocupado

Cambia el puerto en `.env`:
```
FLASK_PORT=8000
```

Luego usa: `http://127.0.0.1:8000`

### ❌ Otros problemas

Consulta `TROUBLESHOOTING.md` para soluciones detalladas.

## 🚀 Comandos Manuales (Alternativa)

Si prefieres hacerlo manualmente en lugar de usar los scripts `.bat`:

```cmd
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
venv\Scripts\activate.bat

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear carpeta templates
mkdir templates
move index.html templates\

# 5. Ejecutar aplicación
python app.py
```

## 📊 Comparación: Antes vs Después

| Característica | Versión Original | Versión Mejorada |
|---------------|------------------|------------------|
| Interfaz | Terminal (CLI) | Web moderna |
| Accesibilidad | Solo programadores | Cualquier usuario |
| Visualización | Texto plano | Barras HP, colores |
| Tests | Básicos | Cobertura completa |
| Documentación | Mínima | Exhaustiva |
| Type hints | ~30% | 100% |
| Manejo errores | Básico | Robusto |

## 🎨 Capturas de Pantalla Esperadas

Cuando la aplicación esté corriendo, deberías ver:

1. **Pantalla de Configuración**:
   - Selector de nivel
   - Lista de personajes
   - Selector de enemigos
   - Botón "Start Combat"

2. **Durante el Combate**:
   - Contador de ronda
   - Tarjetas de personajes con HP
   - Tarjetas de enemigos con HP
   - Barras de vida en colores
   - Log de combate
   - Botones "Next Turn" y "New Combat"

3. **Fin del Combate**:
   - Mensaje de victoria o derrota
   - Resumen del combate

## 🆘 ¿Necesitas Ayuda?

1. **Lee `TROUBLESHOOTING.md`** para problemas comunes
2. **Revisa los logs** en la ventana donde corre `run.bat`
3. **Abre DevTools** (F12) en el navegador para ver errores JavaScript
4. **Verifica la estructura** de archivos con `tree /F`

## 📚 Archivos de Documentación

- `README.md` - Documentación completa del código
- `INSTALL.md` - Guía de instalación detallada
- `TROUBLESHOOTING.md` - Solución de problemas
- `WINDOWS_QUICKSTART.md` - Este archivo

## ✅ Checklist Final

Antes de reportar un problema, verifica:

- [ ] Python 3.8+ instalado (`python --version`)
- [ ] Ejecutaste `setup.bat` correctamente
- [ ] Carpeta `templates/` existe con `index.html` dentro
- [ ] Archivo `.env` existe
- [ ] Entorno virtual activado (consola dice `(venv)`)
- [ ] Flask corriendo sin errores en consola
- [ ] Probaste en navegador moderno (Chrome, Firefox, Edge)
- [ ] Revisaste DevTools (F12) en el navegador

## 🎉 ¡Disfruta!

Una vez configurado, el simulador te permite:
- ⚔️ Simular combates tácticos de D&D 5e
- 🎲 Probar diferentes composiciones de grupo
- 📊 Ver estadísticas en tiempo real
- 🎮 Experimentar con encuentros balanceados

¡Que tus dados siempre rueden a tu favor! 🎲✨
