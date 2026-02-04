"""
Utilidades para la interfaz de usuario.
"""
import os
from colors import Colors
from constants import UIConstants


def clear_screen():
    """Limpia la pantalla de la consola."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_separator(char="═", length=None, color=Colors.GRAY):
    """Imprime una línea separadora."""
    if length is None:
        length = UIConstants.SEPARATOR_LENGTH
    print(f"{color}{char * length}{Colors.ENDC}")


def print_section_header(text, icon=""):
    """Imprime un encabezado de sección."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'─' * UIConstants.SEPARATOR_LENGTH}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}{icon}  {text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'─' * UIConstants.SEPARATOR_LENGTH}{Colors.ENDC}\n")


def print_banner():
    """Muestra un banner de bienvenida con arte ASCII."""
    banner = f"""
{Colors.BOLD}{Colors.OKBLUE}╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║  {Colors.FAIL}⚔️  {Colors.WARNING}🎲{Colors.OKGREEN}  D&D 5E DAMAGE SIMULATOR  {Colors.WARNING}🎲{Colors.FAIL}  ⚔️{Colors.OKBLUE}                     ║
║                                                                   ║
║        {Colors.OKCYAN}Simula combates épicos y calcula DPR como un héroe{Colors.OKBLUE}       ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝{Colors.ENDC}
"""
    print(banner)


def prompt_yes_no(question, default=True):
    """
    Pregunta sí/no al usuario.
    
    Args:
        question: Pregunta a hacer
        default: Valor por defecto (True para Sí, False para No)
    
    Returns:
        bool: True si sí, False si no
    """
    default_text = "S/n" if default else "s/N"
    response = input(f"{Colors.OKCYAN}{question} ({default_text}): {Colors.ENDC}").strip().lower()
    
    if not response:
        return default
    
    return response in ['s', 'si', 'sí', 'y', 'yes']


def get_positive_int_input(prompt, default=1, min_value=1, max_value=None):
    """
    Obtiene input de entero positivo con validación.
    
    Args:
        prompt: Mensaje a mostrar
        default: Valor por defecto
        min_value: Valor mínimo aceptable
        max_value: Valor máximo aceptable (None para sin límite)
    
    Returns:
        int: Valor ingresado por el usuario
    """
    while True:
        try:
            value = input(f"\n{Colors.OKCYAN}{prompt} (default: {default}): {Colors.ENDC}").strip()
            if not value:
                return default
            
            value = int(value)
            if value < min_value:
                print(f"{Colors.FAIL}❌ Valor debe ser al menos {min_value}{Colors.ENDC}")
                continue
            if max_value and value > max_value:
                print(f"{Colors.FAIL}❌ Valor no puede exceder {max_value}{Colors.ENDC}")
                continue
            
            return value
        except ValueError:
            print(f"{Colors.FAIL}❌ Por favor ingresa un número válido{Colors.ENDC}")


def select_from_menu(title, options, allow_multiple=False, show_numbers=True):
    """
    Muestra un menú y permite seleccionar opciones.
    
    Args:
        title: Título del menú
        options: Lista de opciones (strings o tuplas de (clave, nombre, descripción))
        allow_multiple: Si True, permite seleccionar múltiples opciones
        show_numbers: Si True, muestra números antes de cada opción
    
    Returns:
        int o List[int]: Índice(s) seleccionado(s)
    """
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}{title}{Colors.ENDC}\n")
    
    # Determinar si las opciones son simples strings o tuplas
    simple_options = isinstance(options[0], str) if options else True
    
    for i, option in enumerate(options, 1):
        if show_numbers:
            prefix = f"{Colors.WARNING}{i}.{Colors.ENDC} "
        else:
            prefix = "  "
        
        if simple_options:
            print(f"{prefix}{Colors.WHITE}{option}{Colors.ENDC}")
        else:
            # Asume tupla de (icono/clave, nombre, descripción)
            if len(option) >= 3:
                print(f"{prefix}{Colors.BOLD}{Colors.WHITE}{option[1]}{Colors.ENDC}")
                print(f"   {Colors.GRAY}{option[2]}{Colors.ENDC}\n")
            else:
                print(f"{prefix}{Colors.WHITE}{option[1] if len(option) > 1 else option[0]}{Colors.ENDC}")
    
    print_separator("─")
    
    if allow_multiple:
        prompt = "Selecciona opciones (ej: 1,3,5 o 'todos'): "
    else:
        prompt = f"Selecciona una opción (1-{len(options)}): "
    
    while True:
        choice = input(f"{Colors.OKCYAN}{prompt}{Colors.ENDC}").strip()
        
        if allow_multiple and choice.lower() in ['todos', 'all']:
            return list(range(len(options)))
        
        try:
            if allow_multiple and ',' in choice:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                if all(0 <= i < len(options) for i in indices):
                    return indices
            else:
                index = int(choice) - 1
                if 0 <= index < len(options):
                    return [index] if allow_multiple else index
            
            print(f"{Colors.FAIL}❌ Selección inválida. Intenta de nuevo.{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.FAIL}❌ Entrada inválida. Usa números separados por comas.{Colors.ENDC}")


def display_hp_bar(name, current_hp, max_hp):
    """
    Muestra una barra visual de HP para un combatiente.
    
    Args:
        name: Nombre del combatiente
        current_hp: HP actual
        max_hp: HP máximo
    """
    hp_percent = (current_hp / max_hp) * 100 if max_hp > 0 else 0
    
    # Determinar color basado en % de HP
    if hp_percent > 75:
        color = Colors.OKGREEN
    elif hp_percent > 50:
        color = Colors.WARNING
    elif hp_percent > 25:
        color = Colors.FAIL
    else:
        color = Colors.MAGENTA
    
    # Crear barra visual
    bar_length = UIConstants.HP_BAR_LENGTH
    filled = int(bar_length * hp_percent / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    print(f"{name:20s} [{color}{bar}{Colors.ENDC}] {current_hp}/{max_hp} ({hp_percent:.0f}%)")
