import { useInView } from '../hooks';
import './HowItWorks.css';

const STEPS = [
  {
    num: '01',
    title: 'Upload Resume',
    desc: 'Select your target role and drop your PDF or DOCX resume. Validation is instant and your file never leaves your session.',
    badge: 'Format & File',
  },
  {
    num: '02',
    title: 'Multi-Engine Analysis',
    desc: 'The backend evaluates 7 scoring categories—from action verbs and quantifiable results to role-specific ATS keyword matching.',
    badge: '7 Scoring Vectors',
  },
  {
    num: '03',
    title: 'Actionable Feedback',
    desc: 'Receive transparent category breakdowns, identified skill gaps, and concrete suggestions to optimize for recruiter screenings.',
    badge: 'Instant Results',
  },
];

export default function HowItWorks() {
  const [sectionRef, inView] = useInView(0.2);

  return (
    <section className="how-it-works" id="how-it-works" ref={sectionRef}>
      <div className="how-it-works__inner">
        <div className="how-it-works__header">
          <span className="how-it-works__label">Process</span>
          <h2 className="how-it-works__title">Engineered for total transparency</h2>
          <p className="how-it-works__subtitle">
            No black-box scores. Every point is tied to verified resume sections,
            quantifiable metrics, and role-matched keyword benchmarks.
          </p>
        </div>

        <div className="how-it-works__timeline">
          <div className="how-it-works__line" aria-hidden="true" />
          <div className="how-it-works__steps">
            {STEPS.map((step, idx) => (
              <div
                key={step.num}
                className={`how-it-works__step${inView ? ' how-it-works__step--active' : ''}`}
                style={{ transitionDelay: `${idx * 0.15}s` }}
              >
                <div className="how-it-works__step-top">
                  <span className="how-it-works__step-num">{step.num}</span>
                  <span className="how-it-works__step-badge">{step.badge}</span>
                </div>
                <h3 className="how-it-works__step-title">{step.title}</h3>
                <p className="how-it-works__step-desc">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
