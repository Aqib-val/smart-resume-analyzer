import { useInView, useAnimatedCounter } from '../hooks';
import './AnalysisPreview.css';

export default function AnalysisPreview() {
  const [sectionRef, inView] = useInView(0.25);

  const animatedScore = useAnimatedCounter(86, inView, 1200);
  const animatedAts = useAnimatedCounter(82, inView, 1200);

  const sampleCategories = [
    { name: 'Contact Info', score: 10, max: 10, pct: 100 },
    { name: 'Standard Sections', score: 15, max: 15, pct: 100 },
    { name: 'Work Experience Depth', score: 18, max: 20, pct: 90 },
    { name: 'Action Verbs & Impact', score: 14, max: 15, pct: 93 },
    { name: 'Quantifiable Metrics', score: 13, max: 15, pct: 86 },
    { name: 'Education & Certifications', score: 10, max: 10, pct: 100 },
  ];

  return (
    <section className="analysis-preview" id="analysis-preview" ref={sectionRef}>
      <div className="analysis-preview__inner">
        <div className="analysis-preview__header">
          <span className="analysis-preview__label">Interactive Sample</span>
          <h2 className="analysis-preview__title">Precision scoring breakdown</h2>
          <p className="analysis-preview__subtitle">
            Every submission produces a deterministic evaluation across contact hygiene,
            quantified outcomes, role alignment, and ATS keyword matching.
          </p>
        </div>

        {/* Preview Card Mockup */}
        <div className="analysis-preview__card">
          {/* Watermark / Sample Banner */}
          <div className="analysis-preview__banner">
            <span className="analysis-preview__banner-badge">SAMPLE REPORT</span>
            <span className="analysis-preview__banner-text">
              Demonstration data only · Upload your file below for your real score
            </span>
          </div>

          <div className="analysis-preview__card-body">
            {/* Top row: Role & Score summary */}
            <div className="analysis-preview__top-row">
              <div className="analysis-preview__meta">
                <span className="analysis-preview__role-badge">Target: Web Developer</span>
                <span className="analysis-preview__filename">sample_resume_alex_chen.pdf</span>
              </div>
              <div className="analysis-preview__scores">
                <div className="analysis-preview__score-box">
                  <div className="analysis-preview__score-num analysis-preview__score-num--accent">
                    {animatedScore}
                    <span className="analysis-preview__score-unit">/100</span>
                  </div>
                  <div className="analysis-preview__score-lbl">Resume Score</div>
                </div>

                <div className="analysis-preview__score-box">
                  <div className="analysis-preview__score-num">
                    {animatedAts}
                    <span className="analysis-preview__score-unit">%</span>
                  </div>
                  <div className="analysis-preview__score-lbl">ATS Match</div>
                </div>
              </div>
            </div>

            {/* Middle: Sample categories */}
            <div className="analysis-preview__section">
              <h4 className="analysis-preview__section-heading">Category Breakdown</h4>
              <div className="analysis-preview__grid">
                {sampleCategories.map((cat) => (
                  <div key={cat.name} className="analysis-preview__bar-item">
                    <div className="analysis-preview__bar-header">
                      <span className="analysis-preview__bar-name">{cat.name}</span>
                      <span className="analysis-preview__bar-score">{cat.score}/{cat.max}</span>
                    </div>
                    <div className="analysis-preview__track">
                      <div
                        className="analysis-preview__fill"
                        style={{ width: inView ? `${cat.pct}%` : '0%' }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Bottom: Sample skills & tip */}
            <div className="analysis-preview__bottom-row">
              <div className="analysis-preview__skills">
                <span className="analysis-preview__skills-title">Matched Keywords</span>
                <div className="analysis-preview__chips">
                  <span className="analysis-chip analysis-chip--matched">React</span>
                  <span className="analysis-chip analysis-chip--matched">JavaScript</span>
                  <span className="analysis-chip analysis-chip--matched">Node.js</span>
                  <span className="analysis-chip analysis-chip--matched">Git</span>
                  <span className="analysis-chip analysis-chip--missing">Docker (Missing)</span>
                </div>
              </div>

              <div className="analysis-preview__suggestion">
                <span className="analysis-preview__suggestion-title">Priority Recommendation</span>
                <p className="analysis-preview__suggestion-text">
                  Strengthen impact metrics in work history: include measurable percentage gains or volume handled.
                </p>
              </div>
            </div>
          </div>

          {/* Action prompt */}
          <div className="analysis-preview__footer">
            <span className="analysis-preview__footer-hint">Ready to benchmark your resume?</span>
            <button
              type="button"
              className="analysis-preview__footer-cta"
              onClick={() => {
                document.getElementById('upload-section')?.scrollIntoView({ behavior: 'smooth' });
              }}
            >
              Analyze Your Real Resume ↓
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
