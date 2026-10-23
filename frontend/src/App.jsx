import { useState } from 'react';
import './App.css';
import Hero from './components/Hero';
import UploadForm from './components/UploadForm';
import ResultsDashboard from './components/ResultsDashboard';
import Footer from './components/Footer';

export default function App() {
  const [result, setResult] = useState(null);

  function handleResult(data) {
    setResult(data);
    // Scroll to the top of the results after a short render delay
    setTimeout(() => {
      document.getElementById('results-dashboard')?.scrollIntoView({
        behavior: 'smooth',
        block: 'start',
      });
    }, 100);
  }

  function handleReset() {
    setResult(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  return (
    <div className="app">
      <main className="app__main">
        {result ? (
          <ResultsDashboard data={result} onReset={handleReset} />
        ) : (
          <>
            <Hero />
            <UploadForm
              onResult={handleResult}
              onError={() => {}}
            />
          </>
        )}
      </main>
      <Footer />
    </div>
  );
}
