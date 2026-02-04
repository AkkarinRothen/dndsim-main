# Configuración Avanzada y Ejemplos

## pytest.ini - Configuración del Proyecto

```ini
[pytest]
# Configuración básica
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Opciones por defecto
addopts = 
    -v
    --strict-markers
    --tb=short
    --disable-warnings
    -ra

# Markers personalizados
markers =
    slow: Tests lentos que toman más de 10 segundos
    smoke: Tests de humo para verificación rápida
    integration: Tests de integración
    ui: Tests de interfaz de usuario
    
# Timeout por defecto
timeout = 300

# Logging
log_cli = true
log_cli_level = INFO
log_file = tests.log
log_file_level = DEBUG
```

## conftest.py - Fixtures Compartidas

```python
"""
Configuración compartida de pytest para todos los tests.
"""
import pytest
import logging
from typing import Generator
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_config():
    """Configuración global de tests."""
    return {
        "base_url": "http://127.0.0.1:5000/",
        "default_timeout": 10,
        "max_combat_turns": 50,
        "screenshot_dir": "screenshots",
        "headless": True,
    }


@pytest.fixture(scope="function")
def chrome_driver(test_config) -> Generator[webdriver.Chrome, None, None]:
    """WebDriver con configuración avanzada."""
    options = webdriver.ChromeOptions()
    
    if test_config["headless"]:
        options.add_argument("--headless")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    
    # Opciones de performance
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Preferencias del navegador
    prefs = {
        "download.default_directory": "/tmp/downloads",
        "download.prompt_for_download": False,
        "profile.default_content_setting_values.notifications": 2,
    }
    options.add_experimental_option("prefs", prefs)
    
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # Configuración adicional
    driver.implicitly_wait(2)
    driver.set_page_load_timeout(30)
    
    logger.info(f"WebDriver iniciado - Headless: {test_config['headless']}")
    
    yield driver
    
    try:
        driver.quit()
        logger.info("WebDriver cerrado correctamente")
    except Exception as e:
        logger.error(f"Error cerrando WebDriver: {e}")


@pytest.fixture(autouse=True)
def log_test_name(request):
    """Log automático del nombre del test."""
    logger.info(f"\n{'='*80}")
    logger.info(f"Iniciando test: {request.node.name}")
    logger.info(f"{'='*80}\n")
    yield
    logger.info(f"\n{'='*80}")
    logger.info(f"Finalizando test: {request.node.name}")
    logger.info(f"{'='*80}\n")


@pytest.fixture
def screenshot_dir(tmp_path):
    """Directorio temporal para screenshots."""
    screenshot_path = tmp_path / "screenshots"
    screenshot_path.mkdir()
    return screenshot_path
```

## Ejemplo: Test con Data-Driven

```python
import pytest
from test_web_ui_improved import *

# Datos de prueba
COMBAT_SCENARIOS = [
    # (hero_name, hero_hp, enemy_name, enemy_hp, expected_winner)
    ("Warrior", 100, "Goblin", 30, "hero"),
    ("Mage", 60, "Dragon", 200, "enemy"),
    ("Rogue", 80, "Skeleton", 80, "any"),
]


@pytest.mark.parametrize(
    "hero_name,hero_hp,enemy_name,enemy_hp,expected_winner",
    COMBAT_SCENARIOS,
    ids=["warrior_vs_goblin", "mage_vs_dragon", "rogue_vs_skeleton"]
)
def test_combat_scenarios(
    chrome_driver,
    flask_app,
    hero_name,
    hero_hp,
    enemy_name,
    enemy_hp,
    expected_winner
):
    """Test diferentes escenarios de combate."""
    driver = chrome_driver
    
    with screenshot_on_failure(driver, f"combat_{hero_name}_vs_{enemy_name}"):
        driver.get(BASE_URL)
        verify_page_loaded(driver, BASE_URL)
        
        # Configurar combate (asumiendo que hay campos de input)
        # Esto depende de tu implementación real
        # driver.find_element(By.ID, "hero-name").send_keys(hero_name)
        # driver.find_element(By.ID, "hero-hp").send_keys(str(hero_hp))
        # etc...
        
        # Iniciar combate
        start_button = wait_for_element(
            driver, By.ID, TestConfig.START_COMBAT_BTN, condition="clickable"
        )
        safe_click(driver, start_button)
        
        # Ejecutar combate completo
        turn_count = 0
        while turn_count < MAX_COMBAT_TURNS:
            try:
                next_button = wait_for_element_enabled(
                    driver, By.ID, TestConfig.NEXT_TURN_BTN, timeout=5
                )
                safe_click(driver, next_button)
                turn_count += 1
                
                combat_log = get_element_text_safe(driver, By.ID, TestConfig.COMBAT_LOG)
                if TestConfig.COMBAT_ENDED_TEXT in combat_log:
                    break
            except TimeoutException:
                break
        
        # Verificar resultado según esperado
        combat_log = get_element_text_safe(driver, By.ID, TestConfig.COMBAT_LOG)
        
        if expected_winner == "hero":
            assert "Hero wins" in combat_log or hero_name in combat_log
        elif expected_winner == "enemy":
            assert "Enemy wins" in combat_log or enemy_name in combat_log
        # Si es "any", solo verificamos que terminó
        
        logger.info(f"Combate {hero_name} vs {enemy_name} completado en {turn_count} turnos")
```

## Ejemplo: Test de Performance

```python
import time
import pytest
from test_web_ui_improved import *

@pytest.mark.slow
def test_combat_performance(chrome_driver, flask_app):
    """Verifica que el combate se ejecute en tiempo razonable."""
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "combat_performance"):
        driver.get(BASE_URL)
        
        # Iniciar combate
        start_time = time.time()
        
        start_button = wait_for_element(
            driver, By.ID, TestConfig.START_COMBAT_BTN, condition="clickable"
        )
        safe_click(driver, start_button)
        
        combat_start_time = time.time()
        
        # Ejecutar un turno
        next_button = wait_for_element_enabled(
            driver, By.ID, TestConfig.NEXT_TURN_BTN
        )
        safe_click(driver, next_button)
        
        turn_duration = time.time() - combat_start_time
        
        # Verificar que un turno tome menos de 2 segundos
        assert turn_duration < 2.0, f"Turn took {turn_duration:.2f}s, expected < 2.0s"
        
        logger.info(f"Turn duration: {turn_duration:.3f}s")
        logger.info(f"Setup time: {combat_start_time - start_time:.3f}s")
```

## Ejemplo: Test de Accesibilidad Básica

```python
import pytest
from selenium.webdriver.common.by import By
from test_web_ui_improved import *

def test_accessibility_basics(chrome_driver, flask_app):
    """Verifica aspectos básicos de accesibilidad."""
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "accessibility"):
        driver.get(BASE_URL)
        verify_page_loaded(driver, BASE_URL)
        
        # Verificar que los botones tengan texto o aria-label
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        for idx, button in enumerate(buttons):
            button_text = button.text.strip()
            aria_label = button.get_attribute("aria-label")
            
            assert button_text or aria_label, \
                f"Button {idx} has no text or aria-label"
            
            logger.info(f"Button {idx}: text='{button_text}', aria-label='{aria_label}'")
        
        # Verificar contraste de colores (ejemplo básico)
        # Esto requeriría una biblioteca adicional como axe-selenium
        
        # Verificar navegación por teclado
        start_button = driver.find_element(By.ID, TestConfig.START_COMBAT_BTN)
        start_button.send_keys("\n")  # Presionar Enter
        
        time.sleep(1)
        
        # Verificar que el combate inició
        combat_log = wait_for_element(driver, By.ID, TestConfig.COMBAT_LOG)
        assert combat_log is not None
```

## Ejemplo: Test con Mocking de Red

```python
import pytest
from unittest.mock import patch, MagicMock
from test_web_ui_improved import *

def test_network_error_handling(chrome_driver, monkeypatch):
    """Verifica manejo de errores de red."""
    driver = chrome_driver
    
    # Configurar mock para simular fallo de red
    def mock_get(*args, **kwargs):
        raise requests.exceptions.ConnectionError("Network error")
    
    with screenshot_on_failure(driver, "network_error"):
        # Intentar cargar la página con red simulada
        # Esto requiere más configuración según tu aplicación
        pass
```

## Comandos Útiles de pytest

```bash
# Ejecutar tests con diferentes verbosidades
pytest -v                          # Verbose
pytest -vv                         # Muy verbose
pytest -q                          # Quiet

# Ejecutar tests específicos
pytest test_web_ui.py::test_homepage_loads
pytest -k "combat"                 # Tests que contengan "combat"
pytest -m "smoke"                  # Tests marcados como smoke

# Generar reportes
pytest --html=report.html --self-contained-html
pytest --junit-xml=results.xml
pytest --cov=app --cov-report=html

# Debugging
pytest -s                          # No capturar stdout
pytest --pdb                       # Abrir debugger en fallo
pytest --lf                        # Last failed - solo tests que fallaron
pytest --ff                        # Failed first - ejecutar primero los que fallaron

# Performance
pytest -n 4                        # Ejecutar con 4 workers (requiere pytest-xdist)
pytest --durations=10              # Mostrar los 10 tests más lentos

# Modo watch (requiere pytest-watch)
ptw                                # Re-ejecutar tests al detectar cambios
```

## Estructura de Proyecto Recomendada

```
project/
├── app/
│   ├── __init__.py
│   ├── routes.py
│   └── models.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Fixtures compartidas
│   ├── test_web_ui_improved.py  # Tests UI
│   ├── test_unit.py             # Tests unitarios
│   └── test_integration.py      # Tests de integración
├── screenshots/                  # Screenshots de fallos
├── pytest.ini                    # Configuración pytest
├── requirements.txt              # Dependencias
└── .github/
    └── workflows/
        └── tests.yml             # CI/CD
```

## GitHub Actions - CI/CD Example

```yaml
name: UI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Install Chrome
      run: |
        wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
        sudo sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
        sudo apt-get update
        sudo apt-get install -y google-chrome-stable
    
    - name: Start Flask app
      run: |
        python app.py &
        sleep 5
    
    - name: Run tests
      run: |
        pytest tests/test_web_ui_improved.py -v --html=report.html --self-contained-html
    
    - name: Upload screenshots on failure
      if: failure()
      uses: actions/upload-artifact@v2
      with:
        name: screenshots
        path: screenshots/
    
    - name: Upload test report
      if: always()
      uses: actions/upload-artifact@v2
      with:
        name: test-report
        path: report.html
```

## requirements.txt

```txt
# Testing
pytest==7.4.0
pytest-html==3.2.0
pytest-cov==4.1.0
pytest-timeout==2.1.0
pytest-xdist==3.3.1
pytest-watch==4.2.0

# Selenium
selenium==4.11.0
webdriver-manager==3.9.0

# Utilities
requests==2.31.0

# Optional pero recomendadas
pytest-sugar==0.9.7          # Mejor output visual
pytest-instafail==0.5.0      # Mostrar fallos inmediatamente
pytest-rerunfailures==12.0   # Re-ejecutar tests que fallen
```

## Tips de Optimización

### 1. Reutilizar Sesión del Navegador
```python
@pytest.fixture(scope="session")
def chrome_driver_session():
    """Driver que persiste durante toda la sesión de tests."""
    # ... configuración ...
    yield driver
    driver.quit()
```

### 2. Paralelización con pytest-xdist
```bash
pytest -n auto  # Usa todos los cores disponibles
```

### 3. Caché de Resultados
```python
@pytest.fixture(scope="session")
@pytest.mark.usefixtures("flask_app")
def combat_data():
    """Datos pre-cargados para tests."""
    # Cargar datos una vez y reutilizar
    return load_combat_data()
```

### 4. Skip de Tests Condicional
```python
@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Test no soportado en Windows"
)
def test_linux_specific():
    pass
```
