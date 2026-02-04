import { Fighter } from "../src/classes/Fighter";
import { Character } from "../src/sim/Character";
import { Target } from "../src/sim/Target";
import { Simulation } from "../src/sim/Simulation";
import { Greatsword } from "../src/weapons/martial/melee/Greatsword";

describe('MiEncuentro Simulation', () => {
  test('should produce consistent simulation results', () => {
    // 1. Definimos la Clase (Guerrero)
    const miClase = new Fighter();

    // 2. Definimos las Estadísticas (Stats)
    const misStats = { 
        str: 18, 
        dex: 14, 
        con: 14, 
        int: 10, 
        wis: 10, 
        cha: 10 
    };

    // 3. Creamos el Personaje
    const miPersonaje = new Character({
        level: 5,
        stats: misStats,
        classes: [miClase],
        items: [
            new Greatsword()
        ]
    });

    // 4. Configurar el Objetivo (Target)
    const statsObjetivo = { 
        str: 18, 
        dex: 14, 
        con: 16, 
        int: 10, 
        wis: 12, 
        cha: 10 
    };
    const miObjetivo = new Target({ stats: statsObjetivo }); 

    // 5. Configurar la Simulación
    const config = {
        character: miPersonaje,
        target: miObjetivo,
        numRounds: 4,
        numFights: 10000
    };

    // 6. Ejecutar
    const sim = new Simulation(config);
    const resultados = sim.run();

    // 7. Ver resultados y comparar con el snapshot
    // Esto reemplaza el console.log. La primera vez que corras el test,
    // se creará un archivo "snapshot". En las siguientes ejecuciones,
    // el resultado se comparará con ese snapshot.
    expect(resultados).toMatchSnapshot();
  });
});
