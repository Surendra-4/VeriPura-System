import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import VerifyPage from './pages/VerifyPage';
import './styles/global.css';
import styles from './App.module.css';

function App() {
  return (
    <Router>
      <div className={styles.app}>
        <nav className={styles.nav}>
          <div className="container">
            <div className={styles.navContent}>
              <Link to="/" className={styles.logo}>
                🔒 VeriPura
              </Link>
              <div className={styles.navLinks}>
                <Link to="/" className={styles.navLink}>Upload</Link>
                <Link to="/verify" className={styles.navLink}>Verify</Link>
              </div>
            </div>
          </div>
        </nav>

        <main>
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/verify" element={<VerifyPage />} />
            <Route path="/verify/:batchId" element={<VerifyPage />} />
          </Routes>
        </main>

        <footer className={styles.footer}>
          <div className="container">
            <p>© 2026 VeriPura - Supply Chain Verification System</p>
          </div>
        </footer>
      </div>
    </Router>
  );
}

export default App;
