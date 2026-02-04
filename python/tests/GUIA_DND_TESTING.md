# Guía de Tests para D&D 5e Combat Simulator

## Descripción del Proyecto

Este proyecto es un **simulador de combate para Dungeons & Dragons 5ta Edición** con una interfaz web que permite:
- Visualizar personajes y monstruos disponibles
- Configurar presets de combate
- Ejecutar simulaciones de combate interactivas
- Ver resultados con gráficos y tablas

## Estructura de Tests

### Tests Creados

#### 1. `test_web_ui_improved.py`
**Tests generales mejorados** con manejo robusto de errores:
- ✅ Carga de homepage
- ✅ Validación de formularios
- ✅ Flujo completo de combate
- ✅ Múltiples ciclos de combate
- ✅ Screenshots automáticos en fallos
- ✅ Logging detallado

#### 2. `test_dnd_simulator_pages.py`
**Tests específicos para D&D Simulator**:
- ✅ Estructura de página index
- ✅ Validación de listas (Characters, Monsters, Presets)
- ✅ Página de resultados
- ✅ Integración con Plotly
- ✅ Navegación entre páginas
- ✅ Tests de accesibilidad

## Ejecutar Tests

### Instalación de Dependencias

```bash
# Instalar dependencias
pip install -r requirements.txt

# O manualmente
pip install pytest selenium webdriver-manager requests pytest-html
```

### Comandos de Ejecución

```bash
# Todos los tests
pytest test_*.py -v

# Solo tests del simulador D&D
pytest test_dnd_simulator_pages.py -v

# Solo tests UI
pytest -m ui -v

# Tests de humo (smoke tests)
pytest -m smoke -v

# Con reporte HTML
pytest test_dnd_simulator_pages.py --html=report_dnd.html --self-contained-html

# Con logs detallados
pytest test_dnd_simulator_pages.py -v -s --log-cli-level=DEBUG

# Tests específicos
pytest test_dnd_simulator_pages.py::test_available_characters_list -v
```

## Cobertura de Tests por Página

### Index.html (Página Principal)

| Test | Verifica |
|------|----------|
| `test_index_page_structure` | Título, container, H1, nota informativa |
| `test_index_page_sections` | Secciones: Characters, Monsters, Presets |
| `test_available_characters_list` | Lista de personajes existe y tiene contenido |
| `test_available_monsters_list` | Lista de monstruos existe y tiene contenido |
| `test_combat_presets_list` | Lista de presets con formato nombre:descripción |
| `test_index_page_styling` | Estilos CSS aplicados correctamente |
| `test_full_index_page_smoke` | Test rápido de carga y contenido básico |
| `test_accessibility_basic_index` | Lang, viewport, estructura de headings |

### Results.html (Página de Resultados)

| Test | Verifica |
|------|----------|
| `test_results_page_structure` | Título, div de gráfico, tabla, link de navegación |
| `test_results_page_table_structure` | Thead, tbody, headers, filas de datos |
| `test_results_page_plotly_integration` | Plotly cargado y gráfico renderizado |
| `test_navigation_link_functionality` | Link funcional de vuelta a index |

## Personalización para Tu Proyecto

### 1. Configurar URL Base

En `test_dnd_simulator_pages.py`:
```python
# Si tu app corre en otro puerto
BASE_URL = "http://127.0.0.1:8000/"
```

### 2. Agregar Test para Formulario de Combate

Si tienes un formulario de configuración de combate:

```python
@pytest.mark.ui
def test_combat_setup_form(chrome_driver):
    """Test del formulario de configuración de combate."""
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "combat_setup"):
        driver.get(BASE_URL + "setup")  # Tu URL de setup
        verify_page_loaded(driver)
        
        # Seleccionar personaje
        character_select = wait_for_element(
            driver, By.ID, "character-select", condition="clickable"
        )
        character_select.click()
        
        # Seleccionar primera opción
        options = driver.find_elements(By.TAG_NAME, "option")
        options[1].click()  # Primera opción real (0 suele ser placeholder)
        
        # Seleccionar monstruo
        monster_select = wait_for_element(
            driver, By.ID, "monster-select", condition="clickable"
        )
        # ... similar al de arriba
        
        # Submit formulario
        submit_btn = wait_for_element(
            driver, By.ID, "start-combat-btn", condition="clickable"
        )
        safe_click(driver, submit_btn)
        
        # Verificar que la simulación inició
        time.sleep(1)
        assert "combat" in driver.current_url.lower() or \
               "simulation" in driver.page_source.lower()
```

### 3. Test de Validación de Datos en Resultados

```python
@pytest.mark.ui
def test_results_data_integrity(chrome_driver):
    """Verifica que los datos en la tabla son consistentes."""
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "results_data"):
        # Primero ejecutar una simulación o navegar a resultados mock
        driver.get(BASE_URL + "results")
        
        try:
            table = wait_for_element(driver, By.TAG_NAME, "table", timeout=5)
            
            # Obtener todas las filas
            rows = table.find_elements(By.XPATH, ".//tbody/tr")
            
            for row_idx, row in enumerate(rows):
                cells = row.find_elements(By.TAG_NAME, "td")
                
                # Verificar que no hay celdas vacías
                for cell_idx, cell in enumerate(cells):
                    cell_text = cell.text.strip()
                    assert cell_text, \
                        f"Empty cell at row {row_idx}, column {cell_idx}"
                
                # Si hay columnas numéricas, validar formato
                # Por ejemplo, columna de HP
                if len(cells) > 2:  # Asumiendo HP es columna 2
                    hp_text = cells[2].text
                    try:
                        hp_value = int(hp_text)
                        assert hp_value >= 0, \
                            f"HP value {hp_value} should be non-negative"
                    except ValueError:
                        logger.warning(f"HP cell contains non-numeric: {hp_text}")
            
            logger.info(f"✓ Validated {len(rows)} data rows")
            
        except TimeoutException:
            pytest.skip("Results page requires simulation data")
```

### 4. Test de Integración Completa

```python
@pytest.mark.integration
def test_full_simulation_workflow(chrome_driver):
    """Test de workflow completo: index → setup → combat → results."""
    driver = chrome_driver
    
    with screenshot_on_failure(driver, "full_workflow"):
        # 1. Cargar index
        logger.info("Step 1: Loading index page")
        driver.get(BASE_URL)
        verify_page_loaded(driver)
        
        # 2. Navegar a setup (asumiendo que hay un link/botón)
        logger.info("Step 2: Navigating to combat setup")
        setup_link = wait_for_element(
            driver, By.LINK_TEXT, "Start Combat", condition="clickable"
        )
        safe_click(driver, setup_link)
        time.sleep(1)
        
        # 3. Configurar combate
        logger.info("Step 3: Configuring combat")
        # Seleccionar preset o configurar manualmente
        # ... (tu lógica aquí)
        
        # 4. Iniciar combate
        logger.info("Step 4: Starting combat")
        start_btn = wait_for_element(
            driver, By.ID, "start-combat-btn", condition="clickable"
        )
        safe_click(driver, start_btn)
        
        # 5. Ejecutar turnos de combate
        logger.info("Step 5: Running combat turns")
        turn_count = 0
        max_turns = 20
        
        while turn_count < max_turns:
            try:
                next_turn_btn = wait_for_element_enabled(
                    driver, By.ID, "next-turn-btn", timeout=5
                )
                safe_click(driver, next_turn_btn)
                turn_count += 1
                
                combat_log = get_element_text_safe(driver, By.ID, "combat-log")
                if "ended" in combat_log.lower() or "victory" in combat_log.lower():
                    break
            except TimeoutException:
                break
        
        logger.info(f"Combat completed in {turn_count} turns")
        
        # 6. Ir a resultados
        logger.info("Step 6: Viewing results")
        results_link = wait_for_element(
            driver, By.LINK_TEXT, "View Results", condition="clickable"
        )
        safe_click(driver, results_link)
        time.sleep(2)
        
        # 7. Verificar página de resultados
        logger.info("Step 7: Verifying results page")
        assert "results" in driver.current_url.lower()
        
        chart_div = wait_for_element(driver, By.ID, "chart")
        assert chart_div is not None
        
        table = wait_for_element(driver, By.TAG_NAME, "table")
        assert table is not None
        
        logger.info("✓ Full workflow completed successfully")
```

## Datos de Prueba

### Mock Data para Tests

Si necesitas datos de prueba, puedes crear fixtures:

```python
@pytest.fixture
def sample_characters():
    """Lista de personajes para pruebas."""
    return [
        {"name": "Fighter", "hp": 100, "ac": 18},
        {"name": "Wizard", "hp": 60, "ac": 12},
        {"name": "Rogue", "hp": 80, "ac": 15},
    ]

@pytest.fixture
def sample_monsters():
    """Lista de monstruos para pruebas."""
    return [
        {"name": "Goblin", "hp": 30, "ac": 14},
        {"name": "Dragon", "hp": 250, "ac": 20},
        {"name": "Skeleton", "hp": 40, "ac": 13},
    ]

@pytest.fixture
def sample_presets():
    """Presets de combate para pruebas."""
    return {
        "Quick Skirmish": {
            "description": "1 Fighter vs 2 Goblins",
            "party": ["Fighter"],
            "enemies": ["Goblin", "Goblin"]
        },
        "Epic Battle": {
            "description": "Full party vs Dragon",
            "party": ["Fighter", "Wizard", "Rogue"],
            "enemies": ["Dragon"]
        }
    }
```

## Casos Edge a Considerar

### 1. Sin Datos
```python
def test_empty_lists_handling(chrome_driver):
    """Verifica manejo cuando no hay personajes/monstruos."""
    # Mockear respuesta vacía del backend
    # Verificar que la UI muestra mensaje apropiado
```

### 2. Errores de Red
```python
def test_network_timeout_handling(chrome_driver):
    """Verifica manejo de timeouts de red."""
    # Configurar proxy que simule latencia
    # Verificar que hay indicadores de carga
```

### 3. Datos Inválidos
```python
def test_invalid_combat_configuration(chrome_driver):
    """Verifica validación de configuración inválida."""
    # Intentar iniciar combate sin seleccionar personajes
    # Verificar mensajes de error apropiados
```

## Debugging Tips

### 1. Guardar HTML en Fallos
```python
def save_page_source_on_failure(driver, test_name):
    """Guarda el HTML completo en caso de fallo."""
    html_path = f"/home/claude/failed_{test_name}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    logger.info(f"Page source saved to: {html_path}")
```

### 2. Verificar Estado de Elementos
```python
def debug_element_state(driver, element_id):
    """Imprime información detallada de un elemento."""
    element = driver.find_element(By.ID, element_id)
    
    logger.info(f"Element: {element_id}")
    logger.info(f"  Displayed: {element.is_displayed()}")
    logger.info(f"  Enabled: {element.is_enabled()}")
    logger.info(f"  Selected: {element.is_selected()}")
    logger.info(f"  Tag: {element.tag_name}")
    logger.info(f"  Text: {element.text}")
    logger.info(f"  Value: {element.get_attribute('value')}")
    logger.info(f"  Classes: {element.get_attribute('class')}")
```

### 3. Pausar Ejecución para Inspección
```python
def pause_for_inspection(driver, duration=60):
    """Pausa la ejecución para inspección manual."""
    logger.info(f"Pausing for {duration} seconds for manual inspection...")
    logger.info(f"Current URL: {driver.current_url}")
    time.sleep(duration)
```

## Métricas de Calidad

### Coverage Esperado

| Componente | Coverage Objetivo |
|------------|-------------------|
| Páginas HTML | 100% |
| Flujos de usuario | 90% |
| Casos edge | 70% |
| Manejo de errores | 85% |

### Tiempos de Ejecución

| Tipo de Test | Tiempo Esperado |
|--------------|-----------------|
| Smoke tests | < 5 segundos |
| Tests unitarios de página | < 10 segundos |
| Tests de flujo completo | < 30 segundos |
| Suite completa | < 2 minutos |

## Mantenimiento

### Cuándo Actualizar Tests

✅ **SIEMPRE actualizar cuando:**
- Se cambian IDs de elementos HTML
- Se agregan nuevas páginas
- Se modifican flujos de usuario
- Se cambian URLs o rutas

⚠️ **Revisar cuando:**
- Se actualizan bibliotecas (Plotly, etc.)
- Se cambia estructura de datos
- Se modifican estilos CSS que afectan funcionalidad

### Checklist de PR

Antes de hacer merge, verificar:
- [ ] Todos los tests pasan
- [ ] Se agregaron tests para funcionalidad nueva
- [ ] Tests existentes siguen siendo relevantes
- [ ] No hay tests duplicados
- [ ] Coverage no bajó
- [ ] Screenshots de fallos revisados

## Recursos Adicionales

### Documentación Selenium
- [Selenium Python Docs](https://selenium-python.readthedocs.io/)
- [WebDriver Wait](https://selenium-python.readthedocs.io/waits.html)

### Documentación Pytest
- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/stable/how-to/mark.html)

### D&D 5e Referencias
- [D&D Beyond](https://www.dndbeyond.com/)
- [SRD Combat Rules](https://www.5esrd.com/combat/)

## Soporte

Si encuentras problemas:
1. Revisa los logs detallados (`-v -s`)
2. Examina los screenshots de fallos
3. Verifica que Flask esté corriendo
4. Comprueba que Chrome/ChromeDriver están actualizados
5. Revisa la configuración de red/firewall

## Próximos Pasos Sugeridos

1. **Agregar tests de rendimiento**
   - Tiempo de carga de páginas
   - Tiempo de respuesta de AJAX
   - Tamaño de payload

2. **Tests de compatibilidad**
   - Diferentes navegadores (Firefox, Safari)
   - Diferentes tamaños de pantalla
   - Modo móvil

3. **Tests de seguridad básica**
   - XSS prevention
   - CSRF tokens
   - Input sanitization

4. **Visual regression testing**
   - Percy.io o similar
   - Comparación de screenshots
