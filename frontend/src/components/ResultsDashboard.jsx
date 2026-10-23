import { useState, useEffect } from 'react';
import { useAnimatedCounter } from '../hooks';
import './ResultsDashboard.css';

/**
 * Renders the full analysis returned by the backend.
 *
 * Expected `data` shape (from POST /api/analyze):
 *   resume_score      – number (0-100)
 *   ats_score         – number (0-100)
 *   role              – string
 *   category_scores   – { [section]: { score, max, explanation } }
 *   matched_skills    – string[]
 *   missing_skills    – string[]
 *   keyword_match_pct – number
 *   suggestions       – string[]
 */
export default function ResultsDashboard({ data, onReset }) {
  const {
    resume_score = 0,
    ats_score = 0,
    role = '',
    category_scores = {},
    matched_skills = [],
    missing_skills = [],
    keyword_match_pct,
    suggestions = [],
  } = data;

  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setMounted(true), 50);
    return () => clearTimeout(timer);
  }, []);

  const animatedScore = useAnimatedCounter(resume_score, mounted, 1200);
  const animatedAts = useAnimatedCounter(ats_score, mounted, 1200);

  function getBenchmarkLabel(score) {
    if (score >= 80) return 'Exceeds Typical Benchmarks';
    if (score >= 65) return 'Competitive Profile';
    if (score >= 50) return 'Moderate Alignment';
    return 'Actionable Gaps Identified';
  }

  return (
    <div className="results" id="results-dashboard">
      {/* ── Report Header ── */}
      <header className="results__header">
        <div className="results__header-top">
          <span className="results__badge">Verified Analysis</span>
          {role && <span className="results__role-tag">Role: {role}</span>}
        </div>
        <h1 className="results__title">Resume Performance Intelligence</h1>
        <p className="results__desc">
          Evaluated against 7 structural and qualitative categories plus role-specific ATS keywords.
        </p>
      </header>

      {/* ── Primary Scores Grid ── */}
      <div className="results__scores">
        <div className="score-card score-card--primary">
          <div className="score-card__top">
            <span className="score-card__label">Comprehensive Score</span>
            <span className="score-card__status">{getBenchmarkLabel(resume_score)}</span>
          </div>
          <div className="score-card__value-wrap">
            <span className="score-card__value score-card__value--accent">{animatedScore}</span>
            <span className="score-card__max">/100</span>
          </div>
          <div className="score-card__meter">
            <div
              className="score-card__meter-fill"
              style={{ width: mounted ? `${resume_score}%` : '0%' }}
            />
          </div>
          <p className="score-card__hint">
            Calculated across structure, quantifiable achievements, and language precision.
          </p>
        </div>

        <div className="score-card">
          <div className="score-card__top">
            <span className="score-card__label">ATS Role Keyword Match</span>
            <span className="score-card__status">
              {matched_skills.length} of {matched_skills.length + missing_skills.length} Core Skills
            </span>
          </div>
          <div className="score-card__value-wrap">
            <span className="score-card__value">{animatedAts}</span>
            <span className="score-card__max">%</span>
          </div>
          <div className="score-card__meter">
            <div
              className="score-card__meter-fill score-card__meter-fill--ats"
              style={{ width: mounted ? `${ats_score}%` : '0%' }}
            />
          </div>
          <p className="score-card__hint">
            Direct correlation to applicant tracking system role filtering thresholds.
          </p>
        </div>
      </div>

      {/* ── Category Breakdown ── */}
      {Object.keys(category_scores).length > 0 && (
        <section className="results__section" id="category-section">
          <div className="results__section-header">
            <div className="results__section-title-wrap">
              <span className="results__section-tag">Vectors</span>
              <h2 className="results__section-title">Category Breakdown</h2>
            </div>
            <span className="results__section-meta">
              {Object.keys(category_scores).length} Evaluated Dimensions
            </span>
          </div>

          <div className="results__categories-grid">
            {Object.entries(category_scores).map(([key, cat]) => (
              <CategoryBar
                key={key}
                name={key}
                score={cat.score}
                max={cat.max}
                explanation={cat.explanation}
                mounted={mounted}
              />
            ))}
          </div>
        </section>
      )}

      {/* ── Skills Analysis ── */}
      {(matched_skills.length > 0 || missing_skills.length > 0) && (
        <section className="results__section" id="skills-section">
          <div className="results__section-header">
            <div className="results__section-title-wrap">
              <span className="results__section-tag">Keywords</span>
              <h2 className="results__section-title">Role Skills Analysis</h2>
            </div>
            {keyword_match_pct != null && (
              <span className="results__match-badge">
                {keyword_match_pct}% Match Rate
              </span>
            )}
          </div>

          <div className="results__skills-layout">
            {matched_skills.length > 0 && (
              <SkillsGroup
                label="Matched Keywords"
                skills={matched_skills}
                variant="matched"
                subtext="Detected in your resume text"
              />
            )}
            {missing_skills.length > 0 && (
              <SkillsGroup
                label="Missing Keywords"
                skills={missing_skills}
                variant="missing"
                subtext="Recommended for this role"
              />
            )}
          </div>
        </section>
      )}

      {/* ── Prioritized Suggestions ── */}
      {suggestions.length > 0 && (
        <section className="results__section" id="suggestions-section">
          <div className="results__section-header">
            <div className="results__section-title-wrap">
              <span className="results__section-tag">Optimization</span>
              <h2 className="results__section-title">Actionable Recommendations</h2>
            </div>
            <span className="results__section-meta">
              {suggestions.length} Improvement Steps
            </span>
          </div>

          <div className="results__suggestions-list">
            {suggestions.map((tip, i) => (
              <div className="suggestion" key={i}>
                <span className="suggestion__index" aria-hidden="true">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <p className="suggestion__text">{tip}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Action Bar ── */}
      <div className="results__actions">
        <button
          type="button"
          className="results__reset-btn"
          onClick={onReset}
          id="reset-btn"
        >
          ← Analyze Another Resume
        </button>
      </div>
    </div>
  );
}

/* ── Sub-components ── */

function CategoryBar({ name, score, max, explanation, mounted }) {
  const pct = max > 0 ? Math.round((score / max) * 100) : 0;
  const isPerfect = score === max;

  return (
    <div className="category">
      <div className="category__header">
        <span className="category__name">{name}</span>
        <div className="category__score-wrap">
          <span className="category__score">{score}</span>
          <span className="category__score-max">/{max}</span>
        </div>
      </div>
      <div className="category__bar">
        <div
          className={`category__bar-fill${isPerfect ? ' category__bar-fill--perfect' : ''}`}
          style={{ width: mounted ? `${pct}%` : '0%' }}
        />
      </div>
      {explanation && (
        <p className="category__explanation">{explanation}</p>
      )}
    </div>
  );
}

function SkillsGroup({ label, skills, variant, subtext }) {
  return (
    <div className={`skills-group skills-group--${variant}`}>
      <div className="skills-group__header">
        <div className="skills-group__info">
          <span className="skills-group__label">{label}</span>
          <span className="skills-group__subtext">{subtext}</span>
        </div>
        <span className="skills-group__count">{skills.length}</span>
      </div>
      <div className="skills-group__chips">
        {skills.map((skill) => (
          <span key={skill} className={`chip chip--${variant}`}>
            {variant === 'matched' ? '✓ ' : '+ '}
            {skill}
          </span>
        ))}
      </div>
    </div>
  );
}
