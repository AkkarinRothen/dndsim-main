import React, { useState } from 'react';
import './App.css';
import SimulationForm from './components/SimulationForm';
import SimulationResults from './components/SimulationResults';

function App() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleFormSubmit = async (params) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch('http://localhost:8000/simulate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Something went wrong');
      }

      const data = await response.json();
      setResults(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>D&D 5e Combat Simulator</h1>
      </header>
      <main>
        <SimulationForm onSubmit={handleFormSubmit} loading={loading} />

        {error && <div className="error-message">Error: {error}</div>}

        <SimulationResults results={results} />
      </main>
    </div>
  );
}

export default App;