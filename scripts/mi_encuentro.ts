import { Fighter } from "../src/classes/Fighter";
import { Character } from "../src/sim/Character";
import { Target } from "../src/sim/Target";
import { Simulation } from "../src/sim/Simulation";
import { Greatsword } from "../src/weapons/martial/melee/Greatsword";

// 1. Definimos la Clase (Guerrero)
const miClase = new Fighter();

// 2. Definimos las Estadísticas (Stats)
// Esto era lo que causaba el error principal: Character necesita stats base.
const misStats = { 
    str: 18, // Fuerza alta para pegar duro
    dex: 14, 
    con: 14, 
    int: 10, 
    wis: 10, 
    cha: 10 
};

// 3. Creamos el Personaje
// Eliminamos la propiedad 'name' que causaba el error
const miPersonaje = new Character({
    level: 5,
    stats: misStats,
    items: [
        new Greatsword()
    ]
});

// 4. Configurar el Objetivo (Target)
// Un enemigo con stats apropiados para un CR 15 (ajusta según tu sistema)
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

console.log("Iniciando simulación...");
console.log(`Personaje: Nivel 5 Fighter con Espadón vs Target Nivel 15`);

// 6. Ejecutar
const sim = new Simulation(config);
const resultados = sim.run();

// 7. Ver resultados
console.log("----------------Resultados----------------");
console.log(resultados);