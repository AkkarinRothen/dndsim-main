"""
conftest.py - Configuración compartida de pytest para D&D Combat Simulator

Este archivo contiene fixtures y configuración que se comparten entre todos los tests.
"""

import os
import sys
import time
import logging
from typing import Dict, Any, Generator
from pathlib import Path

import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

class Config:
    """Configuración global de tests."""
    
    # URLs
    BASE_URL = os.getenv("TEST_BASE_URL", "http://127.0.0.1:5000/")
    
    # Timeouts
    DEFAULT_TIMEOUT = int(os.getenv("TEST_TIMEOUT", "10"))
    PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "30"))
    IMPLICIT_WAIT = int(os.getenv("IMPLICIT_WAIT", "2"))
    
    # Combate
    MAX_COMBAT_TURNS = int(os.getenv("MAX_COMBAT_TURNS", "50"))
    
    # Browser
    HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
    WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1920"))
    WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "1080"))
    
    # Directorios
    SCREENSHOT_DIR = Path("screenshots")
    REPORT_DIR = Path("test_reports")
    
    # Flask
    FLASK_STARTUP_TIMEOUT = int(os.getenv("FLASK_STARTUP_TIMEOUT", "30"))
    
    @classmethod
    def ensure_directories(cls):
        """Crea directorios necesarios si no existen."""
        cls.SCREENSHOT_DIR.mkdir(exist_ok=True)
        cls.REPORT_DIR.mkdir(exist_ok=True)


# ============================================================================
# HOOKS DE PYTEST
# ============================================================================

def pytest_configure(config):
    """Hook que se ejecuta al inicio de la sesión de pytest."""
    Config.ensure_directories()
    logger.info("="*80)
    logger.info("INICIANDO SESIÓN DE TESTS D&D COMBAT SIMULATOR")
    logger.info("="*80)
    logger.info(f"Base URL: {Config.BASE_URL}")
    logger.info(f"Headless: {Config.HEADLESS}")
    logger.info(f"Screenshot dir: {Config.SCREENSHOT_DIR}")
    logger.info("="*80)
    
    # Registrar markers personalizados
    config.addinivalue_line(
        "markers", "smoke: Tests rápidos de verificación básica"
    )
    config.addinivalue_line(
        "markers", "ui: Tests de interfaz de usuario"
    )
    config.addinivalue_line(
        "markers", "integration: Tests de integración completa"
    )
    config.addinivalue_line(
        "markers", "slow: Tests que toman más de 10 segundos"
    )


def pytest_unconfigure(config):
    """Hook que se ejecuta al final de la sesión de pytest."""
    logger.info("="*80)
    logger.info("FINALIZANDO SESIÓN DE TESTS")
    logger.info("="*80)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook para capturar el resultado de cada test."""
    outcome = yield
    report = outcome.get_result()
    
    # Agregar información adicional al reporte
    if report.when == "call":
        if report.failed:
            logger.error(f"❌ Test FAILED: {item.nodeid}")
        elif report.passed:
            logger.info(f"✓ Test PASSED: {item.nodeid}")
        elif report.skipped:
            logger.warning(f"⊘ Test SKIPPED: {item.nodeid}")


# ============================================================================
# FIXTURES DE CONFIGURACIÓN
# ============================================================================

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Fixture que proporciona la configuración de tests.
    
    Returns:
        Dict con toda la configuración
    """
    return {
        "base_url": Config.BASE_URL,
        "default_timeout": Config.DEFAULT_TIMEOUT,
        "max_combat_turns": Config.MAX_COMBAT_TURNS,
        "headless": Config.HEADLESS,
        "screenshot_dir": Config.SCREENSHOT_DIR,
        "window_size": (Config.WINDOW_WIDTH, Config.WINDOW_HEIGHT)
    }


@pytest.fixture(scope="session")
def screenshot_dir() -> Path:
    """Fixture que proporciona el directorio de screenshots.
    
    Returns:
        Path del directorio de screenshots
    """
    return Config.SCREENSHOT_DIR


# ============================================================================
# FIXTURES DE WEBDRIVER
# ============================================================================

@pytest.fixture(scope="function")
def chrome_options() -> ChromeOptions:
    """Fixture que configura las opciones de Chrome.
    
    Returns:
        ChromeOptions configurado
    """
    options = ChromeOptions()
    
    # Modo headless
    if Config.HEADLESS:
        options.add_argument("--headless")
    
    # Opciones de estabilidad
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={Config.WINDOW_WIDTH},{Config.WINDOW_HEIGHT}")
    
    # Deshabilitar características innecesarias
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    
    # Optimizaciones de performance
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # Preferencias del navegador
    prefs = {
        "download.default_directory": str(Path.cwd() / "downloads"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
    }
    options.add_experimental_option("prefs", prefs)
    
    # User agent (evitar detección de automation)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    return options


@pytest.fixture(scope="function")
def chrome_driver(chrome_options, request) -> Generator[webdriver.Chrome, None, None]:
    """Fixture principal de WebDriver con manejo de errores mejorado.
    
    Args:
        chrome_options: Opciones configuradas de Chrome
        request: Request object de pytest
        
    Yields:
        webdriver.Chrome: Driver configurado
    """
    driver = None
    test_name = request.node.name
    
    try:
        # Inicializar servicio de ChromeDriver
        service = ChromeService(ChromeDriverManager().install())
        
        # Crear driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Configurar timeouts
        driver.set_page_load_timeout(Config.PAGE_LOAD_TIMEOUT)
        driver.implicitly_wait(Config.IMPLICIT_WAIT)
        
        logger.info(f"WebDriver iniciado para test: {test_name}")
        logger.info(f"Window size: {driver.get_window_size()}")
        
        yield driver
        
    except Exception as e:
        logger.error(f"Error inicializando WebDriver para {test_name}: {e}")
        raise
        
    finally:
        if driver:
            try:
                # Capturar información final
                if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
                    # El test falló - tomar screenshot
                    screenshot_path = Config.SCREENSHOT_DIR / f"failed_{test_name}_{int(time.time())}.png"
                    driver.save_screenshot(str(screenshot_path))
                    logger.error(f"Screenshot guardado: {screenshot_path}")
                    
                    # Guardar HTML
                    html_path = Config.SCREENSHOT_DIR / f"failed_{test_name}_{int(time.time())}.html"
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(driver.page_source)
                    logger.error(f"HTML guardado: {html_path}")
                
                # Cerrar driver
                driver.quit()
                logger.info(f"WebDriver cerrado para test: {test_name}")
                
            except Exception as e:
                logger.warning(f"Error al cerrar WebDriver: {e}")


@pytest.fixture(scope="function")
def chrome_driver_no_implicit_wait(chrome_options) -> Generator[webdriver.Chrome, None, None]:
    """WebDriver sin implicit wait para tests que requieren control fino.
    
    Útil para tests que necesitan verificar que algo NO aparece.
    """
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(Config.PAGE_LOAD_TIMEOUT)
    # No configurar implicit_wait
    
    yield driver
    
    try:
        driver.quit()
    except Exception as e:
        logger.warning(f"Error cerrando driver sin implicit wait: {e}")


# ============================================================================
# FIXTURES DE FLASK APP
# ============================================================================

@pytest.fixture(scope="session")
def flask_app():
    """Fixture que verifica que la aplicación Flask está disponible.
    
    Este fixture NO inicia la aplicación - asume que ya está corriendo.
    Para auto-start, ver flask_app_autostart.
    """
    logger.info("Verificando disponibilidad de Flask app...")
    
    start_time = time.time()
    max_wait = Config.FLASK_STARTUP_TIMEOUT
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(Config.BASE_URL, timeout=2)
            if response.status_code == 200:
                logger.info(f"✓ Flask app disponible en {Config.BASE_URL}")
                yield
                return
        except requests.exceptions.RequestException:
            time.sleep(1)
    
    error_msg = f"Flask app no disponible en {Config.BASE_URL} después de {max_wait} segundos"
    logger.error(error_msg)
    pytest.fail(error_msg)


# ============================================================================
# FIXTURES DE DATOS DE PRUEBA
# ============================================================================

@pytest.fixture
def sample_characters():
    """Datos de ejemplo de personajes."""
    return [
        {
            "name": "Fighter",
            "class": "Fighter",
            "level": 5,
            "hp": 100,
            "ac": 18,
            "str": 18,
            "dex": 14,
            "con": 16,
            "int": 10,
            "wis": 12,
            "cha": 8
        },
        {
            "name": "Wizard",
            "class": "Wizard",
            "level": 5,
            "hp": 60,
            "ac": 12,
            "str": 8,
            "dex": 14,
            "con": 12,
            "int": 18,
            "wis": 14,
            "cha": 10
        },
        {
            "name": "Rogue",
            "class": "Rogue",
            "level": 5,
            "hp": 80,
            "ac": 15,
            "str": 10,
            "dex": 18,
            "con": 14,
            "int": 12,
            "wis": 12,
            "cha": 14
        }
    ]


@pytest.fixture
def sample_monsters():
    """Datos de ejemplo de monstruos."""
    return [
        {
            "name": "Goblin",
            "type": "Humanoid",
            "cr": 0.25,
            "hp": 30,
            "ac": 14,
            "str": 8,
            "dex": 14,
            "con": 10,
            "int": 10,
            "wis": 8,
            "cha": 8
        },
        {
            "name": "Dragon",
            "type": "Dragon",
            "cr": 13,
            "hp": 250,
            "ac": 20,
            "str": 22,
            "dex": 10,
            "con": 20,
            "int": 16,
            "wis": 14,
            "cha": 18
        },
        {
            "name": "Skeleton",
            "type": "Undead",
            "cr": 0.5,
            "hp": 40,
            "ac": 13,
            "str": 10,
            "dex": 14,
            "con": 15,
            "int": 6,
            "wis": 8,
            "cha": 5
        }
    ]


@pytest.fixture
def sample_presets():
    """Datos de ejemplo de presets de combate."""
    return {
        "Quick Skirmish": {
            "description": "1 Fighter vs 2 Goblins",
            "party": ["Fighter"],
            "enemies": ["Goblin", "Goblin"],
            "expected_duration": "short"
        },
        "Balanced Fight": {
            "description": "Fighter and Rogue vs 3 Skeletons",
            "party": ["Fighter", "Rogue"],
            "enemies": ["Skeleton", "Skeleton", "Skeleton"],
            "expected_duration": "medium"
        },
        "Epic Battle": {
            "description": "Full party vs Ancient Dragon",
            "party": ["Fighter", "Wizard", "Rogue"],
            "enemies": ["Dragon"],
            "expected_duration": "long"
        }
    }


# ============================================================================
# FIXTURES AUXILIARES
# ============================================================================

@pytest.fixture(autouse=True)
def log_test_info(request):
    """Fixture automático que loguea información de cada test."""
    test_name = request.node.name
    test_module = request.node.module.__name__
    
    logger.info("")
    logger.info("="*80)
    logger.info(f"INICIANDO TEST: {test_module}::{test_name}")
    logger.info("="*80)
    
    start_time = time.time()
    
    yield
    
    duration = time.time() - start_time
    logger.info("="*80)
    logger.info(f"FINALIZANDO TEST: {test_name}")
    logger.info(f"Duración: {duration:.2f} segundos")
    logger.info("="*80)
    logger.info("")


@pytest.fixture
def slow_test_warning():
    """Fixture para marcar tests lentos y advertir."""
    start_time = time.time()
    
    yield
    
    duration = time.time() - start_time
    if duration > 10:
        logger.warning(f"⚠️ Test lento detectado: {duration:.2f} segundos")


# ============================================================================
# HOOKS PARA CAPTURA DE FALLOS
# ============================================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Captura el reporte del test para usar en fixtures."""
    outcome = yield
    report = outcome.get_result()
    
    # Guardar el reporte en el item para acceso desde fixtures
    setattr(item, f"rep_{report.when}", report)


# ============================================================================
# FUNCIONES AUXILIARES COMPARTIDAS
# ============================================================================

def wait_for_flask_ready(url: str = None, timeout: int = None) -> bool:
    """Espera hasta que Flask esté listo.
    
    Args:
        url: URL a verificar (default: Config.BASE_URL)
        timeout: Timeout en segundos (default: Config.FLASK_STARTUP_TIMEOUT)
        
    Returns:
        bool: True si Flask está listo, False en caso contrario
    """
    url = url or Config.BASE_URL
    timeout = timeout or Config.FLASK_STARTUP_TIMEOUT
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    
    return False


def get_test_data_path(filename: str) -> Path:
    """Obtiene la ruta a un archivo de datos de prueba.
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        Path al archivo
    """
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    return test_data_dir / filename
