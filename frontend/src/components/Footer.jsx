import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer__inner">
        <div className="footer__brand">
          <span className="footer__logo-mark">◆</span>
          <span className="footer__logo-text">Smart Resume Analyzer</span>
        </div>
        <p className="footer__text">
          In-memory deterministic analysis · Uploads are never logged or persisted.
        </p>
        <span className="footer__note">Career Intelligence Architecture</span>
      </div>
    </footer>
  );
}
