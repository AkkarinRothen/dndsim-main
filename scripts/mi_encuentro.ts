import { Fighter } from "../src/classes/Fighter";
import { Character } from "../src/sim/Character";
import { Target } from "../src/sim/Target";
import { Simulation } from "../src/sim/Simulation";
import { Greatsword } from "../src/weapons/martial/melee/Greatsword";
import { DefaultAttackActionOperation } from "../src/sim/actions/AttackAction";

// IMPORTANT: Temporary Fix for TypeScript Errors
// The following changes were made to resolve TypeScript errors (TS2353)
// related to incorrect property assignments in object literals passed to
// Character and Target constructors. These fixes are speculative due to
// lack of access to the full type definitions of Character and Target classes.
//
// If the application logic breaks or errors persist, it's recommended to
// inspect the definitions of Character and Target in '../src/sim/Character'
// and '../src/sim/Target' respectively, and adjust the constructor calls
// in this script to match their expected types.

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
    stats: misStats,
});
miPersonaje.level = 5;

// Equip the Greatsword and set it as the default attack action
const miArma = new Greatsword();
miPersonaje.customTurn.addOperation("action", new DefaultAttackActionOperation(miArma));

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
const miObjetivo = new Target({ 
    level: 15
}); 



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