import React, { useState } from 'react';

function SimulationForm({ onSubmit, loading }) {
  const [characters, setCharacters] = useState('fighter,barbarian');
  const [levels, setLevels] = useState('1-20');
  const [numRounds, setNumRounds] = useState(5);
  const [numFights, setNumFights] = useState(3);
  const [iterations, setIterations] = useState(500);
  const [debug, setDebug] = useState(false);
  const [monster, setMonster] = useState('generic');

  const handleSubmit = (e) => {
    e.preventDefault();
    const characterList = characters.split(',').map(char => char.trim()).filter(char => char !== '');
    onSubmit({
      characters: characterList,
      levels,
      num_rounds: numRounds,
      num_fights: numFights,
      iterations,
      debug,
      monster,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="simulation-form">
      <div className="form-group">
        <label htmlFor="characters">Characters (comma-separated):</label>
        <input
          type="text"
          id="characters"
          value={characters}
          onChange={(e) => setCharacters(e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="levels">Levels (e.g., "1-20" or "5"):</label>
        <input
          type="text"
          id="levels"
          value={levels}
          onChange={(e) => setLevels(e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="numRounds">Number of Rounds per Fight:</label>
        <input
          type="number"
          id="numRounds"
          value={numRounds}
          onChange={(e) => setNumRounds(Number(e.target.value))}
          min="1"
        />
      </div>

      <div className="form-group">
        <label htmlFor="numFights">Number of Fights per Long Rest:</label>
        <input
          type="number"
          id="numFights"
          value={numFights}
          onChange={(e) => setNumFights(Number(e.target.value))}
          min="1"
        />
      </div>

      <div className="form-group">
        <label htmlFor="iterations">Number of Simulation Iterations:</label>
        <input
          type="number"
          id="iterations"
          value={iterations}
          onChange={(e) => setIterations(Number(e.target.value))}
          min="1"
        />
      </div>

      <div className="form-group">
        <label htmlFor="monster">Monster (e.g., "generic", "goblin"):</label>
        <input
          type="text"
          id="monster"
          value={monster}
          onChange={(e) => setMonster(e.target.value)}
        />
      </div>

      <div className="form-group checkbox-group">
        <input
          type="checkbox"
          id="debug"
          checked={debug}
          onChange={(e) => setDebug(e.target.checked)}
        />
        <label htmlFor="debug">Enable Debug Logging</label>
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Simulating...' : 'Run Simulation'}
      </button>
    </form>
  );
}

export default SimulationForm;