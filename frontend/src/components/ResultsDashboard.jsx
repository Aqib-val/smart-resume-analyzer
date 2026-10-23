import './ResultsDashboard.css';

/**
 * Renders the full analysis returned by the backend.
 *
 * Expected `data` shape (from POST /api/analyze):
 *   resume_score     – number (0-100)
 *   ats_score        – number (0-100)
 *   role             – string
 *   category_scores  – { [section]: { score, max, explanation } }
 *   matched_skills   – string[]
 *   missing_skills   – string[]
 *   keyword_match_pct – number
 *   suggestions      – string[]
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

  return (
    <div className="results" id="results-dashboard">
      {/* ── Header ── */}
      <div className="results__header">
        <h2>Your Resume Analysis</h2>
        {role && <span className="results__role-tag">{role}</span>}
      </div>

      {/* ── Score cards ── */}
      <div className="results__scores">
        <ScoreCard
          value={resume_score}
          label="Resume Score"
          variant="resume"
        />
        <ScoreCard
          value={ats_score}
          label="ATS Keyword Match"
          variant="ats"
        />
      </div>

      {/* ── Category breakdown ── */}
      {Object.keys(category_scores).length > 0 && (
        <section className="results__section" id="category-section">
          <h3 className="results__section-title">
            <span className="results__section-title-icon">📊</span>
            Category Breakdown
          </h3>
          {Object.entries(category_scores).map(([key, cat]) => (
            <CategoryBar
              key={key}
              name={key}
              score={cat.score}
              max={cat.max}
              explanation={cat.explanation}
            />
          ))}
        </section>
      )}

      {/* ── Skills ── */}
      {(matched_skills.length > 0 || missing_skills.length > 0) && (
        <section className="results__section" id="skills-section">
          <h3 className="results__section-title">
            <span className="results__section-title-icon">🎯</span>
            Skills Analysis
            {keyword_match_pct != null && (
              <span className="results__role-tag" style={{ marginLeft: 'auto', fontSize: '0.7rem' }}>
                {keyword_match_pct}% match
              </span>
            )}
          </h3>

          {matched_skills.length > 0 && (
            <SkillsGroup label="Matched Skills" skills={matched_skills} variant="matched" />
          )}
          {missing_skills.length > 0 && (
            <SkillsGroup label="Missing Skills" skills={missing_skills} variant="missing" />
          )}
        </section>
      )}

      {/* ── Suggestions ── */}
      {suggestions.length > 0 && (
        <section className="results__section" id="suggestions-section">
          <h3 className="results__section-title">
            <span className="results__section-title-icon">💡</span>
            Suggestions
          </h3>
          {suggestions.map((tip, i) => (
            <div className="suggestion" key={i}>
              <span className="suggestion__icon">{i + 1}</span>
              <p className="suggestion__text">{tip}</p>
            </div>
          ))}
        </section>
      )}

      {/* ── Reset ── */}
      <button
        className="results__reset"
        onClick={onReset}
        id="reset-btn"
      >
        ↻ Analyze Another Resume
      </button>
    </div>
  );
}


/* ── Sub-components ── */

function ScoreCard({ value, label, variant }) {
  return (
    <div className="score-card">
      <div className={`score-card__value score-card__value--${variant}`}>
        {value}
        <span style={{ fontSize: '1.25rem', fontWeight: 600 }}>
          {variant === 'ats' ? '%' : '/100'}
        </span>
      </div>
      <div className="score-card__label">{label}</div>
    </div>
  );
}


function CategoryBar({ name, score, max, explanation }) {
  const pct = max > 0 ? (score / max) * 100 : 0;
  const tier = pct >= 70 ? 'high' : pct >= 40 ? 'mid' : 'low';

  return (
    <div className="category">
      <div className="category__header">
        <span className="category__name">{name}</span>
        <span className="category__score">{score}/{max}</span>
      </div>
      <div className="category__bar">
        <div
          className={`category__bar-fill category__bar-fill--${tier}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {explanation && (
        <p className="category__explanation">{explanation}</p>
      )}
    </div>
  );
}


function SkillsGroup({ label, skills, variant }) {
  return (
    <div className="skills-group">
      <div className="skills-group__label">
        {label}
        <span className="skills-group__count">{skills.length}</span>
      </div>
      <div className="skills-group__chips">
        {skills.map((skill) => (
          <span key={skill} className={`chip chip--${variant}`}>
            {skill}
          </span>
        ))}
      </div>
    </div>
  );
}
