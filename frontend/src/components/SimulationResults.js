import React from 'react';

function SimulationResults({ results }) {
  if (!results) {
    return null;
  }

  return (
    <div className="results-container">
      <h2>Simulation Results</h2>
      <h3>Damage Per Round (DPR)</h3>
      <table>
        <thead>
          <tr>
            {results.dpr_results && results.dpr_results.length > 0 && results.dpr_results[0].map((header, index) => (
              <th key={index}>{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {results.dpr_results && results.dpr_results.slice(1).map((row, rowIndex) => (
            <tr key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <td key={cellIndex}>{typeof cell === 'number' ? cell.toFixed(2) : cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {results.debug_log && Object.keys(results.debug_log).length > 0 && (
        <div className="debug-log">
          <h3>Debug Log</h3>
          <pre>
            {Object.entries(results.debug_log).map(([key, value]) => (
              `${key} - ${value}
`
            ))}
          </pre>
        </div>
      )}
    </div>
  );
}

export default SimulationResults;