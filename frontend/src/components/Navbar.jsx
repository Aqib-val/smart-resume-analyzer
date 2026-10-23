import { useState, useEffect } from 'react';
import './Navbar.css';

export default function Navbar({ showBack, onBack }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    function onScroll() {
      setScrolled(window.scrollY > 40);
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav className={`navbar${scrolled ? ' navbar--scrolled' : ''}`} id="navbar">
      <div className="navbar__inner">
        <a href="#" className="navbar__brand" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>
          <span className="navbar__logo-mark">◆</span>
          <span className="navbar__logo-text">Resume Analyzer</span>
        </a>

        {showBack ? (
          <button className="navbar__cta" onClick={onBack} id="nav-back-btn">
            ← New Analysis
          </button>
        ) : (
          <a
            href="#upload-section"
            className="navbar__cta"
            onClick={(e) => {
              e.preventDefault();
              document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' });
            }}
          >
            Analyze Resume →
          </a>
        )}
      </div>
    </nav>
  );
}
