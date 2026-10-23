import { useEffect, useRef } from 'react';
import './OrbitalBackground.css';

/**
 * Abstract orbital composition — decorative SVG ellipses
 * with CSS 3D transforms. Subtle scroll-linked and pointer-linked
 * parallax on desktop. Pointer-events: none; fully inert.
 */
export default function OrbitalBackground() {
  const containerRef = useRef(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const motionOk = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!motionOk) return;

    /* Pointer parallax — desktop only, lightweight */
    const isMobile = window.matchMedia('(max-width: 768px)').matches;
    if (isMobile) return;

    function onPointerMove(e) {
      const cx = (e.clientX / window.innerWidth - 0.5) * 2;  /* -1 to 1 */
      const cy = (e.clientY / window.innerHeight - 0.5) * 2;
      el.style.setProperty('--px', cx.toFixed(3));
      el.style.setProperty('--py', cy.toFixed(3));
    }

    window.addEventListener('pointermove', onPointerMove, { passive: true });
    return () => window.removeEventListener('pointermove', onPointerMove);
  }, []);

  return (
    <div className="orbital" ref={containerRef} aria-hidden="true">
      {/* Ring layers at different angles */}
      <div className="orbital__ring orbital__ring--1">
        <svg viewBox="0 0 600 600" fill="none">
          <ellipse cx="300" cy="300" rx="280" ry="120" stroke="rgba(244,243,237,0.06)" strokeWidth="1" />
        </svg>
      </div>

      <div className="orbital__ring orbital__ring--2">
        <svg viewBox="0 0 600 600" fill="none">
          <ellipse cx="300" cy="300" rx="240" ry="100" stroke="rgba(244,243,237,0.04)" strokeWidth="0.75" />
        </svg>
      </div>

      <div className="orbital__ring orbital__ring--3">
        <svg viewBox="0 0 600 600" fill="none">
          <ellipse cx="300" cy="300" rx="200" ry="80" stroke="rgba(200,241,105,0.15)" strokeWidth="1.25" />
        </svg>
      </div>

      <div className="orbital__ring orbital__ring--4">
        <svg viewBox="0 0 600 600" fill="none">
          <ellipse cx="300" cy="300" rx="160" ry="65" stroke="rgba(244,243,237,0.03)" strokeWidth="0.5" />
        </svg>
      </div>

      {/* Accent glow point */}
      <div className="orbital__glow" />
    </div>
  );
}
