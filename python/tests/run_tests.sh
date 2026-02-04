#!/bin/bash

# ============================================================================
# Script de Ejecución de Tests - D&D Combat Simulator
# ============================================================================
# 
# Este script facilita la ejecución de tests con diferentes configuraciones.
# 
# Uso:
#   ./run_tests.sh [opción]
# 
# Opciones:
#   all         - Ejecutar todos los tests
#   smoke       - Ejecutar solo smoke tests
#   ui          - Ejecutar solo tests de UI
#   integration - Ejecutar solo tests de integración
#   failed      - Ejecutar solo tests que fallaron anteriormente
#   coverage    - Ejecutar con reporte de coverage
#   parallel    - Ejecutar tests en paralelo
#   watch       - Modo watch (re-ejecutar en cambios)
#   clean       - Limpiar archivos de cache y reportes
#   help        - Mostrar esta ayuda
# 
# ============================================================================

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Función para imprimir header
print_header() {
    echo ""
    print_color "$BLUE" "========================================================================"
    print_color "$BLUE" "  $1"
    print_color "$BLUE" "========================================================================"
    echo ""
}

# Función para verificar dependencias
check_dependencies() {
    if ! command -v pytest &> /dev/null; then
        print_color "$RED" "❌ pytest no está instalado"
        print_color "$YELLOW" "Ejecuta: pip install -r requirements.txt"
        exit 1
    fi
    
    if ! command -v python &> /dev/null; then
        print_color "$RED" "❌ Python no está instalado"
        exit 1
    fi
    
    print_color "$GREEN" "✓ Dependencias verificadas"
}

# Función para verificar Flask
check_flask() {
    print_color "$YELLOW" "Verificando si Flask está corriendo..."
    
    # Intentar hacer request a la app
    if curl -s http://127.0.0.1:5000/ > /dev/null 2>&1; then
        print_color "$GREEN" "✓ Flask está corriendo en http://127.0.0.1:5000/"
    else
        print_color "$RED" "❌ Flask no está corriendo en http://127.0.0.1:5000/"
        print_color "$YELLOW" "Por favor, inicia tu aplicación Flask antes de ejecutar los tests"
        print_color "$YELLOW" "Ejemplo: python app.py &"
        exit 1
    fi
}

# Función para limpiar archivos
clean() {
    print_header "Limpiando archivos de cache y reportes"
    
    # Eliminar cache de pytest
    rm -rf .pytest_cache
    print_color "$GREEN" "✓ Cache de pytest eliminado"
    
    # Eliminar archivos de coverage
    rm -rf htmlcov .coverage
    print_color "$GREEN" "✓ Archivos de coverage eliminados"
    
    # Eliminar reportes de tests
    rm -rf test_reports/*.html test_reports/*.json
    print_color "$GREEN" "✓ Reportes de tests eliminados"
    
    # Eliminar screenshots antiguos
    find screenshots -name "*.png" -mtime +7 -delete 2>/dev/null || true
    find screenshots -name "*.html" -mtime +7 -delete 2>/dev/null || true
    print_color "$GREEN" "✓ Screenshots antiguos (>7 días) eliminados"
    
    # Eliminar archivos de log
    rm -f tests.log test_execution.log
    print_color "$GREEN" "✓ Archivos de log eliminados"
    
    # Eliminar __pycache__
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    print_color "$GREEN" "✓ __pycache__ eliminado"
    
    echo ""
    print_color "$GREEN" "✓ Limpieza completada"
}

# Función para ejecutar tests
run_tests() {
    mode=$1
    
    case $mode in
        all)
            print_header "Ejecutando TODOS los tests"
            pytest -v
            ;;
            
        smoke)
            print_header "Ejecutando SMOKE TESTS"
            pytest -v -m smoke
            ;;
            
        ui)
            print_header "Ejecutando UI TESTS"
            pytest -v -m ui
            ;;
            
        integration)
            print_header "Ejecutando INTEGRATION TESTS"
            pytest -v -m integration
            ;;
            
        failed)
            print_header "Ejecutando tests FALLIDOS anteriormente"
            pytest -v --lf
            ;;
            
        coverage)
            print_header "Ejecutando tests con COVERAGE"
            pytest -v \
                --cov=. \
                --cov-report=html \
                --cov-report=term-missing \
                --cov-report=xml
            print_color "$GREEN" "✓ Reporte de coverage generado en htmlcov/index.html"
            ;;
            
        parallel)
            print_header "Ejecutando tests en PARALELO"
            pytest -v -n auto
            ;;
            
        watch)
            print_header "Modo WATCH activado"
            print_color "$YELLOW" "Los tests se re-ejecutarán automáticamente al detectar cambios"
            print_color "$YELLOW" "Presiona Ctrl+C para salir"
            ptw -- -v
            ;;
            
        html)
            print_header "Ejecutando tests con REPORTE HTML"
            pytest -v \
                --html=test_reports/report_$(date +%Y%m%d_%H%M%S).html \
                --self-contained-html
            print_color "$GREEN" "✓ Reporte HTML generado en test_reports/"
            ;;
            
        debug)
            print_header "Ejecutando tests en modo DEBUG"
            pytest -v -s --log-cli-level=DEBUG
            ;;
            
        specific)
            print_header "Ejecutando test específico"
            if [ -z "$2" ]; then
                print_color "$RED" "Error: Especifica el nombre del test"
                print_color "$YELLOW" "Ejemplo: ./run_tests.sh specific test_homepage_loads"
                exit 1
            fi
            pytest -v -k "$2"
            ;;
            
        *)
            print_color "$RED" "Opción desconocida: $mode"
            show_help
            exit 1
            ;;
    esac
}

# Función para mostrar ayuda
show_help() {
    cat << EOF

D&D Combat Simulator - Test Runner

Uso: ./run_tests.sh [opción] [argumentos]

Opciones disponibles:

  all           Ejecutar todos los tests
  smoke         Ejecutar solo smoke tests (verificación rápida)
  ui            Ejecutar solo tests de UI
  integration   Ejecutar solo tests de integración
  failed        Ejecutar solo tests que fallaron anteriormente
  coverage      Ejecutar tests con reporte de coverage
  parallel      Ejecutar tests en paralelo (más rápido)
  watch         Modo watch - re-ejecutar automáticamente en cambios
  html          Generar reporte HTML
  debug         Ejecutar con logging detallado
  specific      Ejecutar un test específico
                Ejemplo: ./run_tests.sh specific test_homepage_loads
  clean         Limpiar archivos de cache y reportes
  help          Mostrar esta ayuda

Ejemplos:

  ./run_tests.sh smoke              # Tests rápidos
  ./run_tests.sh coverage           # Con coverage
  ./run_tests.sh parallel           # Más rápido
  ./run_tests.sh specific test_*ui  # Tests que coincidan con patrón

Variables de entorno:

  TEST_BASE_URL       URL base de la aplicación (default: http://127.0.0.1:5000/)
  HEADLESS           Ejecutar en modo headless (default: true)
  MAX_COMBAT_TURNS   Máximo de turnos de combate (default: 50)

EOF
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Verificar si se pasó algún argumento
    if [ $# -eq 0 ]; then
        print_color "$YELLOW" "No se especificó ninguna opción"
        show_help
        exit 1
    fi
    
    option=$1
    
    # Manejo de opciones especiales
    case $option in
        help|--help|-h)
            show_help
            exit 0
            ;;
            
        clean)
            clean
            exit 0
            ;;
    esac
    
    # Verificar dependencias
    check_dependencies
    
    # Verificar Flask (excepto para watch que puede arrancar antes)
    if [ "$option" != "watch" ]; then
        check_flask
    fi
    
    # Crear directorios necesarios
    mkdir -p screenshots test_reports
    
    # Ejecutar tests
    run_tests "$@"
    
    # Resumen final
    echo ""
    print_header "Tests completados"
    
    # Mostrar ubicación de reportes si existen
    if [ -d "test_reports" ] && [ "$(ls -A test_reports)" ]; then
        print_color "$GREEN" "Reportes disponibles en: test_reports/"
    fi
    
    if [ -d "screenshots" ] && [ "$(ls -A screenshots)" ]; then
        print_color "$YELLOW" "Screenshots disponibles en: screenshots/"
    fi
}

# Ejecutar main con todos los argumentos
main "$@"
