"""
Módulo de visualización para combates.
"""
from prettytable import PrettyTable
from colors import Colors
from constants import UIConstants
from ui_utils import display_hp_bar, print_section_header


class CombatDisplay:
    """Maneja toda la visualización del combate"""
    
    @staticmethod
    def show_combat_state(combat, round_number):
        """
        Muestra el estado actual del combate.
        
        Args:
            combat: Instancia de Combat
            round_number: Número de ronda actual
        """
        print_section_header(f"RONDA {round_number}", "🔄")
        
        table = PrettyTable()
        table.field_names = [
            f"{Colors.BOLD}Combatiente{Colors.ENDC}",
            f"{Colors.BOLD}Equipo{Colors.ENDC}",
            f"{Colors.BOLD}HP{Colors.ENDC}",
            f"{Colors.BOLD}Estado{Colors.ENDC}"
        ]
        table.align = UIConstants.TABLE_ALIGN
        
        all_combatants = combat.party + combat.enemies
        for combatant_wrapper in all_combatants:
            entity = combatant_wrapper.entity
            team_color = Colors.OKGREEN if combatant_wrapper.team == 'party' else Colors.FAIL
            status_text = "Derrotado" if combatant_wrapper.is_down else "Activo"
            status_color = Colors.GRAY if combatant_wrapper.is_down else Colors.WHITE
            
            table.add_row([
                f"{Colors.WHITE}{entity.name}{Colors.ENDC}",
                f"{team_color}{combatant_wrapper.team}{Colors.ENDC}",
                f"{Colors.WARNING}{entity.hp}/{entity.max_hp}{Colors.ENDC}",
                f"{status_color}{status_text}{Colors.ENDC}"
            ])
        
        print(table)
    
    @staticmethod
    def show_combat_state_with_bars(combat, round_number):
        """
        Muestra el estado del combate con barras de HP visuales.
        
        Args:
            combat: Instancia de Combat
            round_number: Número de ronda actual
        """
        print_section_header(f"RONDA {round_number}", "🔄")
        
        print(f"\n{Colors.BOLD}{Colors.OKGREEN}🛡️  PARTY{Colors.ENDC}")
        for combatant in combat.party:
            entity = combatant.entity
            if combatant.is_down:
                print(f"{entity.name:20s} {Colors.GRAY}[DERROTADO]{Colors.ENDC}")
            else:
                display_hp_bar(entity.name, entity.hp, entity.max_hp)
        
        print(f"\n{Colors.BOLD}{Colors.FAIL}👹 ENEMIGOS{Colors.ENDC}")
        for combatant in combat.enemies:
            entity = combatant.entity
            if combatant.is_down:
                print(f"{entity.name:20s} {Colors.GRAY}[DERROTADO]{Colors.ENDC}")
            else:
                display_hp_bar(entity.name, entity.hp, entity.max_hp)
        
        print()
    
    @staticmethod
    def show_combatant_details(combatant):
        """
        Muestra detalles completos de un combatante.
        
        Args:
            combatant: Wrapper de Combatant a inspeccionar
        """
        entity = combatant.entity
        
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'═' * 70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKGREEN}🔍 INSPECCIÓN: {entity.name}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.OKCYAN}{'═' * 70}{Colors.ENDC}\n")
        
        # Información básica
        print(f"{Colors.BOLD}Equipo:{Colors.ENDC} {combatant.team}")
        print(f"{Colors.BOLD}Estado:{Colors.ENDC} {'Derrotado' if combatant.is_down else 'Activo'}")
        print(f"{Colors.BOLD}Iniciativa:{Colors.ENDC} {combatant.initiative}")
        
        # HP con barra visual
        print(f"\n{Colors.BOLD}Puntos de Vida:{Colors.ENDC}")
        display_hp_bar(entity.name, entity.hp, entity.max_hp)
        
        # Clase de Armadura
        print(f"\n{Colors.BOLD}AC:{Colors.ENDC} {entity.ac}")
        
        # Estadísticas
        if hasattr(entity, 'stats'):
            print(f"\n{Colors.BOLD}Estadísticas:{Colors.ENDC}")
            for stat_name, stat_value in entity.stats.items():
                modifier = (stat_value - 10) // 2
                sign = "+" if modifier >= 0 else ""
                print(f"  {stat_name.upper()}: {stat_value} ({sign}{modifier})")
        
        # Condiciones
        conditions = []
        if hasattr(entity, 'prone') and entity.prone:
            conditions.append("Derribado")
        if hasattr(entity, 'grappled') and entity.grappled:
            conditions.append("Agarrado")
        if hasattr(entity, 'stunned') and entity.stunned:
            conditions.append("Aturdido")
        if hasattr(entity, 'poisoned') and entity.poisoned:
            conditions.append("Envenenado")
        
        if conditions:
            print(f"\n{Colors.BOLD}Condiciones:{Colors.ENDC} {', '.join(conditions)}")
        else:
            print(f"\n{Colors.BOLD}Condiciones:{Colors.ENDC} Ninguna")
        
        # Resistencias, vulnerabilidades, inmunidades (si es monstruo)
        if hasattr(entity, 'resistances') and entity.resistances:
            print(f"\n{Colors.BOLD}Resistencias:{Colors.ENDC} {', '.join(entity.resistances)}")
        if hasattr(entity, 'vulnerabilities') and entity.vulnerabilities:
            print(f"\n{Colors.BOLD}Vulnerabilidades:{Colors.ENDC} {', '.join(entity.vulnerabilities)}")
        if hasattr(entity, 'immunities') and entity.immunities:
            print(f"\n{Colors.BOLD}Inmunidades:{Colors.ENDC} {', '.join(entity.immunities)}")
        
        print(f"\n{Colors.BOLD}{Colors.OKCYAN}{'═' * 70}{Colors.ENDC}")
    
    @staticmethod
    def show_combat_result(combat_result, combat_number=None):
        """
        Muestra el resultado de un combate.
        
        Args:
            combat_result: Diccionario con resultado del combate
            combat_number: Número del combate (opcional)
        """
        title = f"RESULTADO DEL COMBATE #{combat_number}" if combat_number else "RESULTADO DEL COMBATE"
        print_section_header(title, "🏁")
        
        winner = combat_result.get('winner', 'nobody')
        rounds = combat_result.get('rounds', 0)
        
        if winner == 'party':
            print(f"{Colors.OKGREEN}🎉 ¡El party ha ganado en {rounds} rondas!{Colors.ENDC}")
        elif winner == 'enemies' or winner == 'monsters':
            print(f"{Colors.FAIL}💀 ¡El party ha sido derrotado en {rounds} rondas!{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}🤝 Combate terminó en empate o por salida temprana.{Colors.ENDC}")
        
        # Mostrar estado final
        print(f"\n{Colors.BOLD}Estado Final:{Colors.ENDC}")
        final_state = combat_result.get('final_state', [])
        
        for combatant_info in final_state:
            name = combatant_info.get('name', 'Unknown')
            team = combatant_info.get('team', 'unknown')
            status = combatant_info.get('status', 'unknown')
            hp = combatant_info.get('hp', '?/?')
            
            team_color = Colors.OKGREEN if team == 'party' else Colors.FAIL
            status_color = Colors.WHITE if status == 'alive' else Colors.GRAY
            
            print(f"  {team_color}{name:20s}{Colors.ENDC} [{status_color}{status:10s}{Colors.ENDC}] HP: {hp}")
    
    @staticmethod
    def show_combat_summary(results):
        """
        Muestra resumen de múltiples combates.
        
        Args:
            results: Lista de resultados de combate
        """
        if not results:
            print(f"{Colors.WARNING}No hay resultados para mostrar.{Colors.ENDC}")
            return
        
        print_section_header("RESUMEN DE COMBATES", "📊")
        
        total_combats = len(results)
        party_wins = sum(1 for r in results if r.get('winner') == 'party')
        enemy_wins = sum(1 for r in results if r.get('winner') in ['enemies', 'monsters'])
        draws = total_combats - party_wins - enemy_wins
        
        avg_rounds = sum(r.get('rounds', 0) for r in results) / total_combats if total_combats > 0 else 0
        
        print(f"Total de combates: {Colors.BOLD}{total_combats}{Colors.ENDC}")
        print(f"Victorias del party: {Colors.OKGREEN}{party_wins}{Colors.ENDC} ({party_wins/total_combats*100:.1f}%)")
        print(f"Victorias de enemigos: {Colors.FAIL}{enemy_wins}{Colors.ENDC} ({enemy_wins/total_combats*100:.1f}%)")
        if draws > 0:
            print(f"Empates: {Colors.WARNING}{draws}{Colors.ENDC} ({draws/total_combats*100:.1f}%)")
        print(f"Rondas promedio: {Colors.BOLD}{avg_rounds:.1f}{Colors.ENDC}")
