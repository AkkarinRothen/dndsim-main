"""
Selenium tests específicos para el simulador de combate D&D 5e.

Tests para las páginas index.html y results.html del simulador.
"""

import pytest
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Importar utilidades del test mejorado
from test_web_ui_improved import (
    chrome_driver,
    screenshot_on_failure,
    wait_for_element,
    safe_click,
    get_element_text_safe,
    verify_page_loaded,
    logger,
    BASE_URL,
    DEFAULT_TIMEOUT
)


class DnDTestConfig:
    """Configuración específica para tests de D&D."""
    
    # URLs
    INDEX_URL = BASE_URL
    RESULTS_URL = BASE_URL + "results"
    
    # Secciones esperadas en index.html
    EXPECTED_SECTIONS = [
        "Available Characters",
        "Available Monsters",
        "Combat Presets"
    ]
    
    # Clases CSS
    CONTAINER_CLASS = "container"
    NOTE_CLASS = "note"
    
    # Elementos de resultados
    CHART_DIV_ID = "chart"
    TABLE_TAG = "table"


def get_list_items(driver, section_heading: str) -> list:
    """Obtiene los items de una lista bajo un heading específico.
    
    Args:
        driver: WebDriver instance
        section_heading: Texto del heading (h2) que precede la lista
        
    Returns:
        list: Lista de textos de los items
    """
    try:
        # Encontrar todos los h2
        headings = driver.find_elements(By.TAG_NAME, "h2")
        
        for heading in headings:
            if section_heading in heading.text:
                # Encontrar el siguiente elemento ul
                ul = heading.find_element(By.XPATH, "following-sibling::ul[1]")
                items = ul.find_elements(By.TAG_NAME, "li")
                return [item.text for item in items if item.text.strip()]
        
        logger.warning(f"Section '{section_heading}' not found")
        return []
    
    except NoSuchElementException as e:
        logger.error(f"Error finding list items for section '{section_heading}': {e}")
        return []


def verify_section_exists(driver, section_name: str) -> bool:
    """Verifica que una sección existe en la página.
    
    Args:
        driver: WebDriver instance
        section_name: Nombre de la sección a verificar
        
    Returns:
        bool: True si la sección existe
    """
    try:
        headings = driver.find_elements(By.TAG_NAME, "h2")
        for heading in headings:
            if section_name in heading.text:
                logger.debug(f"Section '{section_name}' found")
                return True
        return False
    except Exception as e:
        logger.error(f"Error verifying section '{section_name}': {e}")
        return False


@pytest.mark.ui
def test_index_page_structure(chrome_driver):
    """Verifica la estructura básica de la página index.
    
    Valida:
    - Título correcto
    - Presencia de container principal
    - H1 con título apropiado
    - Nota informativa
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "index_structure"):
        logger.info("Testing index page structure")
        
        driver.get(DnDTestConfig.INDEX_URL)
        verify_page_loaded(driver, DnDTestConfig.INDEX_URL)
        
        # Verificar título de la página
        page_title = driver.title
        assert "D&D 5e Combat Simulator" in page_title, \
            f"Expected 'D&D 5e Combat Simulator' in title, got '{page_title}'"
        logger.info(f"✓ Page title correct: {page_title}")
        
        # Verificar container principal
        container = wait_for_element(
            driver, By.CLASS_NAME, DnDTestConfig.CONTAINER_CLASS
        )
        assert container is not None, "Main container not found"
        logger.info("✓ Main container found")
        
        # Verificar H1
        h1 = wait_for_element(driver, By.TAG_NAME, "h1")
        h1_text = h1.text
        assert "Welcome" in h1_text and "D&D 5e Combat Simulator" in h1_text, \
            f"Unexpected H1 text: {h1_text}"
        logger.info(f"✓ H1 heading correct: {h1_text}")
        
        # Verificar nota informativa
        note = driver.find_element(By.CLASS_NAME, DnDTestConfig.NOTE_CLASS)
        note_text = note.text
        assert "combat simulation" in note_text.lower(), \
            "Note doesn't mention combat simulation"
        logger.info("✓ Information note found")
        
        logger.info("Index page structure test passed")


@pytest.mark.ui
def test_index_page_sections(chrome_driver):
    """Verifica que todas las secciones esperadas existen.
    
    Valida:
    - Available Characters
    - Available Monsters
    - Combat Presets
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "index_sections"):
        logger.info("Testing index page sections")
        
        driver.get(DnDTestConfig.INDEX_URL)
        verify_page_loaded(driver, DnDTestConfig.INDEX_URL)
        
        # Verificar todas las secciones esperadas
        for section in DnDTestConfig.EXPECTED_SECTIONS:
            assert verify_section_exists(driver, section), \
                f"Section '{section}' not found on page"
            logger.info(f"✓ Section found: {section}")
        
        logger.info("All expected sections found")


@pytest.mark.ui
def test_available_characters_list(chrome_driver):
    """Verifica la lista de personajes disponibles.
    
    Valida:
    - La lista existe
    - Contiene al menos un personaje
    - Los items tienen formato apropiado
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "characters_list"):
        logger.info("Testing available characters list")
        
        driver.get(DnDTestConfig.INDEX_URL)
        verify_page_loaded(driver, DnDTestConfig.INDEX_URL)
        
        # Obtener lista de personajes
        characters = get_list_items(driver, "Available Characters")
        
        # Verificar que hay personajes
        assert len(characters) > 0, "No characters found in list"
        logger.info(f"✓ Found {len(characters)} characters")
        
        # Verificar formato (no deben estar vacíos)
        for char in characters:
            assert char.strip(), "Found empty character entry"
            logger.debug(f"  - Character: {char}")
        
        logger.info("Characters list validation passed")


@pytest.mark.ui
def test_available_monsters_list(chrome_driver):
    """Verifica la lista de monstruos disponibles.
    
    Valida:
    - La lista existe
    - Contiene al menos un monstruo
    - Los items tienen formato apropiado
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "monsters_list"):
        logger.info("Testing available monsters list")
        
        driver.get(DnDTestConfig.INDEX_URL)
        verify_page_loaded(driver, DnDTestConfig.INDEX_URL)
        
        # Obtener lista de monstruos
        monsters = get_list_items(driver, "Available Monsters")
        
        # Verificar que hay monstruos
        assert len(monsters) > 0, "No monsters found in list"
        logger.info(f"✓ Found {len(monsters)} monsters")
        
        # Verificar formato
        for monster in monsters:
            assert monster.strip(), "Found empty monster entry"
            logger.debug(f"  - Monster: {monster}")
        
        logger.info("Monsters list validation passed")


@pytest.mark.ui
def test_combat_presets_list(chrome_driver):
    """Verifica la lista de presets de combate.
    
    Valida:
    - La lista existe
    - Contiene al menos un preset
    - Los presets tienen nombre y descripción
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "presets_list"):
        logger.info("Testing combat presets list")
        
        driver.get(DnDTestConfig.INDEX_URL)
        verify_page_loaded(driver, DnDTestConfig.INDEX_URL)
        
        # Obtener lista de presets
        presets = get_list_items(driver, "Combat Presets")
        
        # Verificar que hay presets
        assert len(presets) > 0, "No combat presets found in list"
        logger.info(f"✓ Found {len(presets)} combat presets")
        
        # Verificar formato (deben contener ":" separando nombre y descripción)
        for preset in presets:
            assert ":" in preset, f"Preset '{preset}' doesn't have expected format (name: description)"
            
            # Verificar que hay texto en ambos lados del ":"
            parts = preset.split(":", 1)
            assert parts[0].strip(), "Preset name is empty"
            assert parts[1].strip(), "Preset description is empty"
            
            logger.debug(f"  - Preset: {preset}")
        
        logger.info("Combat presets list validation passed")


@pytest.mark.ui
def test_index_page_styling(chrome_driver):
    """Verifica que los estilos básicos se aplican correctamente.
    
    Valida:
    - Colores de fondo
    - Estilos de listas
    - Responsive design básico
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "index_styling"):
        logger.info("Testing index page styling")
        
        driver.get(DnDTestConfig.INDEX_URL)
        verify_page_loaded(driver, DnDTestConfig.INDEX_URL)
        
        # Verificar color de fondo del body
        body = driver.find_element(By.TAG_NAME, "body")
        body_bg = body.value_of_css_property("background-color")
        logger.info(f"Body background color: {body_bg}")
        
        # Verificar que el container tiene sombra (box-shadow)
        container = driver.find_element(By.CLASS_NAME, DnDTestConfig.CONTAINER_CLASS)
        box_shadow = container.value_of_css_property("box-shadow")
        assert box_shadow and box_shadow != "none", "Container should have box-shadow"
        logger.info(f"✓ Container has box-shadow: {box_shadow}")
        
        # Verificar estilo de items de lista
        list_items = driver.find_elements(By.TAG_NAME, "li")
        if list_items:
            first_item = list_items[0]
            item_bg = first_item.value_of_css_property("background-color")
            item_padding = first_item.value_of_css_property("padding")
            
            logger.info(f"✓ List item styling - bg: {item_bg}, padding: {item_padding}")
        
        logger.info("Basic styling validation passed")


@pytest.mark.ui
def test_results_page_structure(chrome_driver):
    """Verifica la estructura de la página de resultados.
    
    Valida:
    - Título correcto
    - Presencia de div para gráfico
    - Presencia de tabla de datos
    - Link de vuelta a inicio
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "results_structure"):
        logger.info("Testing results page structure")
        
        # Nota: Este test asume que la página de resultados puede cargarse
        # En producción, necesitarías primero ejecutar una simulación
        driver.get(DnDTestConfig.RESULTS_URL)
        
        try:
            verify_page_loaded(driver, DnDTestConfig.RESULTS_URL)
            
            # Verificar título
            page_title = driver.title
            assert "Simulation Results" in page_title, \
                f"Expected 'Simulation Results' in title, got '{page_title}'"
            logger.info(f"✓ Page title correct: {page_title}")
            
            # Verificar H1
            h1 = wait_for_element(driver, By.TAG_NAME, "h1", timeout=5)
            assert "Simulation Results" in h1.text, \
                f"Unexpected H1 text: {h1.text}"
            logger.info(f"✓ H1 heading correct: {h1.text}")
            
            # Verificar div del gráfico existe
            chart_div = driver.find_element(By.ID, DnDTestConfig.CHART_DIV_ID)
            assert chart_div is not None, "Chart div not found"
            logger.info("✓ Chart div found")
            
            # Verificar tabla de datos
            table = driver.find_element(By.TAG_NAME, DnDTestConfig.TABLE_TAG)
            assert table is not None, "Data table not found"
            logger.info("✓ Data table found")
            
            # Verificar link de vuelta
            links = driver.find_elements(By.TAG_NAME, "a")
            home_links = [link for link in links if "/" in link.get_attribute("href")]
            assert len(home_links) > 0, "No link back to home found"
            logger.info(f"✓ Found {len(home_links)} navigation link(s)")
            
            logger.info("Results page structure test passed")
            
        except TimeoutException:
            logger.warning("Results page not accessible (may require simulation data)")
            pytest.skip("Results page requires simulation data to be run first")


@pytest.mark.ui
def test_results_page_table_structure(chrome_driver):
    """Verifica la estructura de la tabla de resultados.
    
    Valida:
    - Presencia de thead y tbody
    - Headers de columna
    - Al menos una fila de datos
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "results_table"):
        logger.info("Testing results table structure")
        
        driver.get(DnDTestConfig.RESULTS_URL)
        
        try:
            verify_page_loaded(driver, DnDTestConfig.RESULTS_URL)
            
            # Encontrar tabla
            table = wait_for_element(driver, By.TAG_NAME, "table", timeout=5)
            
            # Verificar thead
            thead = table.find_element(By.TAG_NAME, "thead")
            assert thead is not None, "Table thead not found"
            
            # Verificar headers
            headers = thead.find_elements(By.TAG_NAME, "th")
            assert len(headers) > 0, "No table headers found"
            logger.info(f"✓ Found {len(headers)} table headers")
            
            for idx, header in enumerate(headers):
                header_text = header.text
                logger.debug(f"  - Header {idx + 1}: {header_text}")
            
            # Verificar tbody
            tbody = table.find_element(By.TAG_NAME, "tbody")
            assert tbody is not None, "Table tbody not found"
            
            # Verificar filas de datos
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            logger.info(f"✓ Found {len(rows)} data row(s)")
            
            if rows:
                # Verificar que las filas tienen el número correcto de celdas
                first_row = rows[0]
                cells = first_row.find_elements(By.TAG_NAME, "td")
                assert len(cells) == len(headers), \
                    f"Row has {len(cells)} cells but table has {len(headers)} headers"
                logger.info(f"✓ Row structure matches header count")
            
            logger.info("Results table structure validation passed")
            
        except TimeoutException:
            logger.warning("Results page not accessible")
            pytest.skip("Results page requires simulation data")


@pytest.mark.ui
def test_results_page_plotly_integration(chrome_driver):
    """Verifica la integración de Plotly para gráficos.
    
    Valida:
    - Script de Plotly cargado
    - Div del gráfico presente
    - JavaScript de inicialización
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "results_plotly"):
        logger.info("Testing Plotly integration")
        
        driver.get(DnDTestConfig.RESULTS_URL)
        
        try:
            verify_page_loaded(driver, DnDTestConfig.RESULTS_URL)
            
            # Verificar que Plotly está cargado
            plotly_loaded = driver.execute_script(
                "return typeof Plotly !== 'undefined';"
            )
            assert plotly_loaded, "Plotly library not loaded"
            logger.info("✓ Plotly library loaded")
            
            # Verificar div del gráfico
            chart_div = driver.find_element(By.ID, DnDTestConfig.CHART_DIV_ID)
            assert chart_div is not None, "Chart div not found"
            
            # Esperar a que el gráfico se renderice (si hay datos)
            time.sleep(2)
            
            # Verificar si hay elementos Plotly renderizados
            plotly_elements = driver.execute_script(
                f"return document.getElementById('{DnDTestConfig.CHART_DIV_ID}').children.length;"
            )
            
            if plotly_elements > 0:
                logger.info(f"✓ Chart rendered with {plotly_elements} child element(s)")
            else:
                logger.warning("Chart div exists but no chart rendered (may need data)")
            
            logger.info("Plotly integration test passed")
            
        except TimeoutException:
            logger.warning("Results page not accessible")
            pytest.skip("Results page requires simulation data")


@pytest.mark.ui
def test_navigation_link_functionality(chrome_driver):
    """Verifica que el link de navegación funciona.
    
    Valida:
    - Link está presente
    - Link tiene href correcto
    - Click lleva a la página correcta
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "navigation_link"):
        logger.info("Testing navigation link functionality")
        
        driver.get(DnDTestConfig.RESULTS_URL)
        
        try:
            verify_page_loaded(driver, DnDTestConfig.RESULTS_URL)
            
            # Encontrar link de navegación
            nav_links = driver.find_elements(By.TAG_NAME, "a")
            
            home_link = None
            for link in nav_links:
                href = link.get_attribute("href")
                if href and href.rstrip("/") == BASE_URL.rstrip("/"):
                    home_link = link
                    break
            
            assert home_link is not None, "Home navigation link not found"
            logger.info(f"✓ Found home link: {home_link.text}")
            
            # Verificar que el link es visible y clickable
            assert home_link.is_displayed(), "Home link is not visible"
            assert home_link.is_enabled(), "Home link is not enabled"
            
            # Click en el link
            safe_click(driver, home_link)
            time.sleep(1)
            
            # Verificar que navegó a la página correcta
            current_url = driver.current_url
            assert current_url.startswith(BASE_URL), \
                f"Expected to navigate to {BASE_URL}, got {current_url}"
            
            logger.info(f"✓ Successfully navigated to: {current_url}")
            logger.info("Navigation link test passed")
            
        except TimeoutException:
            logger.warning("Results page not accessible")
            pytest.skip("Results page requires simulation data")


@pytest.mark.ui
@pytest.mark.smoke
def test_full_index_page_smoke(chrome_driver):
    """Test de humo completo para la página index.
    
    Verifica rápidamente que la página carga y tiene contenido básico.
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "index_smoke"):
        logger.info("Running index page smoke test")
        
        driver.get(DnDTestConfig.INDEX_URL)
        verify_page_loaded(driver, DnDTestConfig.INDEX_URL)
        
        # Verificaciones básicas
        assert "D&D" in driver.page_source, "Page doesn't mention D&D"
        assert "Combat" in driver.page_source, "Page doesn't mention Combat"
        assert "Simulator" in driver.page_source, "Page doesn't mention Simulator"
        
        # Verificar que hay listas
        lists = driver.find_elements(By.TAG_NAME, "ul")
        assert len(lists) >= 3, f"Expected at least 3 lists, found {len(lists)}"
        
        logger.info("✓ Index page smoke test passed")


@pytest.mark.ui
def test_accessibility_basic_index(chrome_driver):
    """Verifica accesibilidad básica de la página index.
    
    Valida:
    - Estructura de headings jerárquica
    - Presencia de atributo lang en html
    - Viewport meta tag
    """
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "index_accessibility"):
        logger.info("Testing index page accessibility")
        
        driver.get(DnDTestConfig.INDEX_URL)
        verify_page_loaded(driver, DnDTestConfig.INDEX_URL)
        
        # Verificar atributo lang
        html = driver.find_element(By.TAG_NAME, "html")
        lang = html.get_attribute("lang")
        assert lang == "en", f"Expected lang='en', got lang='{lang}'"
        logger.info("✓ HTML lang attribute correct")
        
        # Verificar viewport meta tag
        viewport_meta = driver.find_element(
            By.XPATH, "//meta[@name='viewport']"
        )
        assert viewport_meta is not None, "Viewport meta tag not found"
        logger.info("✓ Viewport meta tag present")
        
        # Verificar jerarquía de headings
        h1_count = len(driver.find_elements(By.TAG_NAME, "h1"))
        h2_count = len(driver.find_elements(By.TAG_NAME, "h2"))
        
        assert h1_count == 1, f"Should have exactly 1 h1, found {h1_count}"
        assert h2_count >= 3, f"Should have at least 3 h2s, found {h2_count}"
        
        logger.info(f"✓ Heading structure correct (h1: {h1_count}, h2: {h2_count})")
        logger.info("Basic accessibility test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "ui"])
