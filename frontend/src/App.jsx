import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, Link } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import VerifyPage from './pages/VerifyPage';
import './styles/global.css';
import styles from './App.module.css';

function App() {
  const navClass = ({ isActive }) => `${styles.navLink} ${isActive ? styles.navLinkActive : ''}`;

  return (
    <Router>
      <div className={styles.app}>
        <div className={styles.atmosphere} aria-hidden="true">
          <span className={styles.orbA}></span>
          <span className={styles.orbB}></span>
        </div>

        <nav className={styles.nav}>
          <div className="container">
            <div className={styles.navContent}>
              <Link to="/" className={styles.brand}>
                <span className={styles.brandMark} aria-hidden="true">
                  <span className={styles.brandCore}></span>
                </span>
                <span className={styles.brandText}>
                  <span className={styles.brandName}>VeriPura</span>
                  <span className={styles.brandTag}>Food Trust Infrastructure</span>
                </span>
              </Link>

              <div className={styles.navLinks}>
                <NavLink to="/" className={navClass} end>
                  Upload
                </NavLink>
                <NavLink to="/verify" className={navClass}>
                  Verify
                </NavLink>
                <a
                  href="https://veripura.com"
                  target="_blank"
                  rel="noreferrer"
                  className={styles.navCta}
                >
                  Learn More
                </a>
              </div>
            </div>
          </div>
        </nav>

        <main className={styles.main}>
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/verify" element={<VerifyPage />} />
            <Route path="/verify/:batchId" element={<VerifyPage />} />
          </Routes>
        </main>

        <footer className={styles.footer}>
          <div className="container">
            <div className={styles.footerContent}>
              <p className={styles.footerTitle}>Trust is the most important import.</p>
              <p className={styles.footerCopy}>
                VeriPura combines AI validation and immutable verification records to protect food supply chains.
              </p>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
