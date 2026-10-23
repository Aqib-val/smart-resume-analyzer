import './Hero.css';

export default function Hero() {
  return (
    <section className="hero">
      <div className="hero__badge">
        <span className="hero__badge-dot" />
        Free &amp; Instant Analysis
      </div>
      <h1 className="hero__title">
        Analyze Your Resume,{' '}
        <span className="hero__title-accent">Land More Interviews</span>
      </h1>
      <p className="hero__subtitle">
        Upload your resume, choose a target role, and get a transparent score
        breakdown with actionable suggestions to beat ATS filters.
      </p>
    </section>
  );
}
