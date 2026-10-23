import { useState } from 'react';
import './App.css';
import { useScrollPosition } from './hooks';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import HowItWorks from './components/HowItWorks';
import AnalysisPreview from './components/AnalysisPreview';
import UploadForm from './components/UploadForm';
import ResultsDashboard from './components/ResultsDashboard';
import Footer from './components/Footer';

export default function App() {
  const [result, setResult] = useState(null);
  const scrollNorm = useScrollPosition();

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
      {/* Scroll progress indicator */}
      <div
        className="scroll-progress"
        style={{ transform: `scaleX(${scrollNorm})`, width: '100%' }}
        aria-hidden="true"
      />

      <Navbar showBack={!!result} onBack={handleReset} />

      <main className="app__main">
        {result ? (
          <ResultsDashboard data={result} onReset={handleReset} />
        ) : (
          <>
            <Hero />
            <HowItWorks />
            <AnalysisPreview />
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
