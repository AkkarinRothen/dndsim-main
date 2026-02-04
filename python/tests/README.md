# D&D 5e Combat Simulator - Test Suite 🎲⚔️

Suite completa de tests automatizados para el simulador de combate de Dungeons & Dragons 5ta Edición.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Instalación](#instalación)
- [Uso Rápido](#uso-rápido)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Tests Disponibles](#tests-disponibles)
- [Configuración](#configuración)
- [Comandos Útiles](#comandos-útiles)
- [CI/CD](#cicd)
- [Troubleshooting](#troubleshooting)
- [Contribuir](#contribuir)

## ✨ Características

- ✅ **Tests Robustos**: Manejo avanzado de errores con retry logic
- 📸 **Screenshots Automáticos**: Captura en cada fallo para debugging
- 📊 **Reportes Detallados**: HTML, JSON, y coverage reports
- 🔄 **Retry Logic**: Reintentos automáticos en fallos transitorios
- 📝 **Logging Completo**: Trazabilidad total de la ejecución
- ⚡ **Ejecución Paralela**: Tests más rápidos con pytest-xdist
- 🎯 **Tests Específicos**: Smoke, UI, Integration, etc.
- 🔍 **Accesibilidad**: Validaciones básicas de a11y

## 🚀 Instalación

### Requisitos Previos

- Python 3.8+
- Google Chrome (para Selenium)
- Flask app corriendo en `http://127.0.0.1:5000/`

### Instalación de Dependencias

```bash
# Clonar el repositorio
git clone <tu-repo>
cd dnd-combat-simulator

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🏃 Uso Rápido

### Opción 1: Script Bash (Recomendado)

```bash
# Hacer el script ejecutable
chmod +x run_tests.sh

# Ejecutar todos los tests
./run_tests.sh all

# Ejecutar smoke tests (rápido)
./run_tests.sh smoke

# Ver ayuda
./run_tests.sh help
```

### Opción 2: pytest Directo

```bash
# Todos los tests
pytest -v

# Solo smoke tests
pytest -v -m smoke

# Solo UI tests
pytest -v -m ui

# Con reporte HTML
pytest -v --html=report.html --self-contained-html
```

## 📁 Estructura del Proyecto

```
.
├── test_web_ui_improved.py       # Tests generales mejorados
├── test_dnd_simulator_pages.py   # Tests específicos D&D
├── conftest.py                    # Configuración compartida de pytest
├── pytest.ini                     # Configuración de pytest
├── requirements.txt               # Dependencias
├── run_tests.sh                   # Script de ejecución
├── screenshots/                   # Screenshots de fallos
│   ├── failed_*.png
│   └── failed_*.html
├── test_reports/                  # Reportes generados
│   ├── report_*.html
│   └── report_*.json
└── README.md                      # Este archivo
```

## 🧪 Tests Disponibles

### Tests Generales (`test_web_ui_improved.py`)

| Test | Descripción | Duración |
|------|-------------|----------|
| `test_homepage_loads` | Verifica carga de la página principal | ~2s |
| `test_combat_setup_form_validation` | Valida formulario de configuración | ~3s |
| `test_full_combat_flow` | Flujo completo de combate | ~15s |
| `test_multiple_combat_cycles` | Estabilidad con múltiples ciclos | ~20s |

### Tests D&D Específicos (`test_dnd_simulator_pages.py`)

| Test | Descripción | Duración |
|------|-------------|----------|
| `test_index_page_structure` | Estructura de index.html | ~2s |
| `test_index_page_sections` | Secciones de contenido | ~2s |
| `test_available_characters_list` | Lista de personajes | ~2s |
| `test_available_monsters_list` | Lista de monstruos | ~2s |
| `test_combat_presets_list` | Presets de combate | ~2s |
| `test_index_page_styling` | Estilos CSS | ~3s |
| `test_results_page_structure` | Estructura de resultados | ~3s |
| `test_results_page_table_structure` | Tabla de datos | ~3s |
| `test_results_page_plotly_integration` | Gráficos Plotly | ~4s |
| `test_navigation_link_functionality` | Navegación entre páginas | ~3s |
| `test_full_index_page_smoke` | Smoke test completo | ~2s |
| `test_accessibility_basic_index` | Accesibilidad básica | ~2s |

### Markers Disponibles

```bash
pytest -m smoke         # Tests rápidos de verificación
pytest -m ui           # Tests de interfaz de usuario
pytest -m integration  # Tests de integración
pytest -m slow         # Tests lentos (>10s)
```

## ⚙️ Configuración

### Variables de Entorno

Puedes configurar el comportamiento de los tests con variables de entorno:

```bash
# URL de la aplicación
export TEST_BASE_URL="http://127.0.0.1:8000/"

# Modo headless (sin GUI)
export HEADLESS="true"  # o "false" para ver el navegador

# Tamaño de ventana
export WINDOW_WIDTH="1920"
export WINDOW_HEIGHT="1080"

# Máximo de turnos de combate
export MAX_COMBAT_TURNS="100"

# Timeout de carga de página
export PAGE_LOAD_TIMEOUT="30"
```

### Configuración en pytest.ini

Edita `pytest.ini` para cambiar configuración por defecto:

```ini
[pytest]
addopts = 
    -v           # Verbosidad
    -n auto      # Paralelo automático
    --tb=short   # Traceback corto
```

## 🔧 Comandos Útiles

### Ejecución

```bash
# Tests específicos
pytest test_dnd_simulator_pages.py::test_homepage_loads -v

# Tests que coincidan con patrón
pytest -k "homepage" -v

# Solo tests que fallaron
pytest --lf -v

# Tests que fallaron primero, luego el resto
pytest --ff -v

# Detener en el primer fallo
pytest -x -v

# Mostrar variables locales en fallos
pytest -l -v

# Sin capturar stdout
pytest -s -v
```

### Reportes

```bash
# Reporte HTML
pytest --html=report.html --self-contained-html

# Coverage
pytest --cov=. --cov-report=html --cov-report=term

# JSON report
pytest --json-report --json-report-file=report.json

# Ver los 10 tests más lentos
pytest --durations=10
```

### Debugging

```bash
# Logs detallados
pytest -v -s --log-cli-level=DEBUG

# Abrir debugger en fallo
pytest --pdb

# Modo verbose máximo
pytest -vv

# Ver warnings
pytest -v -Wd
```

### Paralelo

```bash
# Usar todos los cores
pytest -n auto

# Usar 4 workers
pytest -n 4

# Con estrategia loadscope (mejor para fixtures costosas)
pytest -n auto --dist loadscope
```

### Watch Mode

```bash
# Re-ejecutar automáticamente al detectar cambios
ptw -- -v

# Con patrón específico
ptw -- -v -k "homepage"
```

## 🔄 CI/CD

### GitHub Actions

Ejemplo de workflow para GitHub Actions (`.github/workflows/tests.yml`):

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Install Chrome
      uses: browser-actions/setup-chrome@latest
    
    - name: Start Flask app
      run: |
        python app.py &
        sleep 5
    
    - name: Run smoke tests
      run: pytest -m smoke -v
    
    - name: Run all tests
      run: pytest -v --html=report.html --self-contained-html
    
    - name: Upload screenshots
      if: failure()
      uses: actions/upload-artifact@v3
      with:
        name: screenshots
        path: screenshots/
    
    - name: Upload test report
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-report
        path: report.html
```

## 🐛 Troubleshooting

### Flask no está corriendo

```
Error: Flask app no está corriendo en http://127.0.0.1:5000/
```

**Solución**: Inicia tu aplicación Flask:
```bash
python app.py &
```

### ChromeDriver no encontrado

```
Error: ChromeDriver executable needs to be available in path
```

**Solución**: webdriver-manager debería descargar automáticamente. Si falla:
```bash
pip install --upgrade webdriver-manager
```

### Tests muy lentos

**Solución**: Usa ejecución paralela:
```bash
pytest -n auto
```

### Screenshots no se guardan

**Solución**: Verifica que el directorio existe:
```bash
mkdir -p screenshots
```

### Elementos no encontrados

```
Error: ElementNotFoundError: Element 'combat-log' not found
```

**Solución**: 
1. Verifica que la app esté corriendo
2. Revisa el screenshot generado
3. Verifica que los IDs en el HTML coincidan
4. Aumenta el timeout:

```python
wait_for_element(driver, By.ID, "combat-log", timeout=20)
```

### Tests fallan aleatoriamente

**Solución**: Usa retry logic:
```bash
pytest --reruns 2 --reruns-delay 1
```

O en pytest.ini:
```ini
addopts = --reruns 2 --reruns-delay 1
```

## 📊 Métricas de Calidad

### Coverage Objetivo

- **Páginas HTML**: 100%
- **Flujos de usuario**: 90%
- **Casos edge**: 70%
- **Manejo de errores**: 85%

### Tiempos Esperados

- **Suite completa**: < 2 minutos
- **Smoke tests**: < 10 segundos
- **Tests UI individuales**: < 10 segundos
- **Tests de integración**: < 30 segundos

## 🤝 Contribuir

### Agregar Nuevos Tests

1. Crea el test en el archivo apropiado
2. Usa las utilidades existentes en `conftest.py`
3. Agrega markers apropiados (`@pytest.mark.ui`, etc.)
4. Documenta el test con docstring
5. Ejecuta y verifica que pasa
6. Actualiza este README si es necesario

Ejemplo:

```python
@pytest.mark.ui
def test_mi_nuevo_feature(chrome_driver, flask_app):
    """Test para verificar mi nuevo feature.
    
    Valida:
    - Feature carga correctamente
    - Interacción funciona
    - Resultado es correcto
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "mi_nuevo_feature"):
        driver.get(BASE_URL + "mi-feature")
        verify_page_loaded(driver)
        
        # Tu código aquí
        assert "esperado" in driver.page_source
```

### Checklist de PR

- [ ] Todos los tests pasan localmente
- [ ] Se agregaron tests para nuevo código
- [ ] Tests siguen las convenciones del proyecto
- [ ] README actualizado si es necesario
- [ ] Sin warnings de pytest
- [ ] Coverage no disminuyó

## 📚 Recursos

### Documentación

- [Selenium Python](https://selenium-python.readthedocs.io/)
- [pytest](https://docs.pytest.org/)
- [pytest-html](https://pytest-html.readthedocs.io/)
- [WebDriver Manager](https://github.com/SergeyPirogov/webdriver_manager)

### D&D 5e

- [D&D Beyond](https://www.dndbeyond.com/)
- [D&D 5e SRD](https://www.5esrd.com/)

### Testing Best Practices

- [Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Selenium Best Practices](https://www.selenium.dev/documentation/test_practices/)

## 📝 Licencia

[Tu licencia aquí]

## 👥 Autores

[Tus datos aquí]

---

¿Preguntas? Abre un issue o contacta al equipo de desarrollo.

Happy Testing! 🎲⚔️
