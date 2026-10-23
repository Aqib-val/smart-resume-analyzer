import { useScrollReveal } from '../hooks';
import OrbitalBackground from './OrbitalBackground';
import './Hero.css';

export default function Hero() {
  const labelRef = useScrollReveal(0.1);
  const titleRef = useScrollReveal(0.1);
  const subRef = useScrollReveal(0.1);
  const ctaRef = useScrollReveal(0.1);

  return (
    <section className="hero" id="hero">
      <OrbitalBackground />

      <div className="hero__content">
        <div className="hero__label reveal" ref={labelRef}>
          Resume Intelligence
        </div>

        <h1 className="hero__title reveal reveal--delay-1" ref={titleRef}>
          Know exactly where<br />
          your resume stands<span className="hero__title-dot">.</span>
        </h1>

        <p className="hero__subtitle reveal reveal--delay-2" ref={subRef}>
          Upload your resume, choose a target role, and get a transparent
          score breakdown with actionable suggestions to beat ATS filters.
        </p>

        <a
          href="#upload-section"
          className="hero__cta reveal reveal--delay-3"
          ref={ctaRef}
          onClick={(e) => {
            e.preventDefault();
            document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' });
          }}
        >
          Analyze Your Resume
          <span className="hero__cta-arrow">→</span>
        </a>
      </div>
    </section>
  );
}
