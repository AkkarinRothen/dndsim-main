import csv
import click
import prettytable
from typing import Set, List, Dict, Tuple
import random

# Import everything from the sim package that was moved there
from sim import (
    Args,
    test_dpr,
    test_character,
    test_characters,
    parse_levels,
    CharacterConfig, # Still need this
    Simulation # Still need this
)
import configs
import sim.character
import sim.target
import monster_configs # Import monster_configs
from util.log import log # Need log for print_data

# random.seed(1234)

def write_data(file: str, data):
    with open(file, "w") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)


def print_data(data):
    table = prettytable.PrettyTable()
    levels = set()
    classes = dict()
    for [level, name, dpr, _] in data:
        if name not in classes:
            classes[name] = dict()
        classes[name][level] = "{:.2f}".format(dpr)
        levels.add(level)
    levels = sorted(list(levels))
    table.add_column("Level", levels)
    for name in sorted(classes.keys()):
        table.add_column(name, [classes[name][level] for level in levels])
    print(table)





@click.command()
@click.option("--characters", default="all", help="Characters to test")
@click.option("-o", "--output", default=None, help="Output file")
@click.option("--num_rounds", default=5, help="Number of rounds per fight")
@click.option("--num_fights", default=3, help="Number of fights per long rest")
@click.option("--iterations", default=500, help="Number of simulations to run")
@click.option("--debug", is_flag=True, help="Enable debug metrics")
@click.option("--levels", default="1-20", help="Levels to test")
@click.option("--monster", default="generic", help="Monster to test against (e.g., 'goblin', 'orc', or 'generic')") # Added monster option
def run(
    characters: str,
    output: str,
    num_rounds: int,
    num_fights: int,
    iterations: int,
    debug: bool,
    levels: str,
    monster: str, # Added monster parameter
):
    start, end = parse_levels(levels)
    characters = configs.break_out_shortcuts(characters.split(","))
    data = test_characters(
        characters,
        start_level=start,
        end_level=end,
        num_rounds=num_rounds,
        num_fights=num_fights,
        iterations=iterations,
        debug=debug,
        monster_name=monster, # Pass monster_name
    )
    if output:
        write_data(output, data)
    print_data(data[1:])


if __name__ == "__main__":
    run()
