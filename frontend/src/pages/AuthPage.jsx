import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getGoogleLoginUrl, loginUser, registerUser } from '../api/services';
import { isAuthenticated, setAccessToken } from '../auth/token';
import styles from './AuthPage.module.css';

const initialState = {
  email: '',
  password: '',
  confirmPassword: '',
};

const AuthPage = () => {
  const navigate = useNavigate();
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState(initialState);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  useEffect(() => {
    if (isAuthenticated()) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  const updateField = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const extractError = (err) =>
    err.response?.data?.detail?.error || err.response?.data?.detail || 'Authentication failed.';

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setInfo('');

    if (mode === 'signup' && form.password !== form.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'signup') {
        await registerUser({ email: form.email, password: form.password });
        setInfo('Account created. Please sign in.');
        setMode('login');
        setForm({ email: form.email, password: '', confirmPassword: '' });
      } else {
        const result = await loginUser({ email: form.email, password: form.password });
        setAccessToken(result.access_token);
        navigate('/dashboard', { replace: true });
      }
    } catch (err) {
      setError(extractError(err));
    } finally {
      setLoading(false);
    }
  };

  const continueWithGoogle = async () => {
    setError('');
    setInfo('');
    setGoogleLoading(true);

    try {
      const { authorization_url: authorizationUrl } = await getGoogleLoginUrl();
      window.location.assign(authorizationUrl);
    } catch (err) {
      setError(extractError(err));
      setGoogleLoading(false);
    }
  };

  return (
    <section className={styles.page}>
      <div className="container">
        <div className={styles.shell}>
          <div className={styles.pitch}>
            <p className={styles.kicker}>Access VeriPura</p>
            <h1>Secure your supply-chain intelligence workspace</h1>
            <p>
              Sign in to manage verification workflows, inspect document fraud signals, and track shipment
              consistency in one secure control panel.
            </p>
          </div>

          <div className={styles.panel}>
            <div className={styles.tabRow}>
              <button
                className={`${styles.tab} ${mode === 'login' ? styles.activeTab : ''}`}
                onClick={() => {
                  setMode('login');
                  setError('');
                  setInfo('');
                }}
                type="button"
              >
                Login
              </button>
              <button
                className={`${styles.tab} ${mode === 'signup' ? styles.activeTab : ''}`}
                onClick={() => {
                  setMode('signup');
                  setError('');
                  setInfo('');
                }}
                type="button"
              >
                Signup
              </button>
            </div>

            <form className={styles.form} onSubmit={submit}>
              <label className={styles.label} htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                className={styles.input}
                value={form.email}
                onChange={(e) => updateField('email', e.target.value)}
                required
                autoComplete="email"
                placeholder="you@company.com"
              />

              <label className={styles.label} htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                className={styles.input}
                value={form.password}
                onChange={(e) => updateField('password', e.target.value)}
                minLength={8}
                required
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                placeholder="At least 8 characters"
              />

              {mode === 'signup' && (
                <>
                  <label className={styles.label} htmlFor="confirmPassword">
                    Confirm password
                  </label>
                  <input
                    id="confirmPassword"
                    type="password"
                    className={styles.input}
                    value={form.confirmPassword}
                    onChange={(e) => updateField('confirmPassword', e.target.value)}
                    minLength={8}
                    required
                    autoComplete="new-password"
                    placeholder="Repeat password"
                  />
                </>
              )}

              {error && <div className={styles.error}>{error}</div>}
              {info && <div className={styles.info}>{info}</div>}

              <button type="submit" className={styles.submitButton} disabled={loading || googleLoading}>
                {loading ? 'Please wait...' : mode === 'signup' ? 'Create account' : 'Sign in'}
              </button>
            </form>

            <div className={styles.divider}>or</div>

            <button
              type="button"
              className={styles.googleButton}
              disabled={loading || googleLoading}
              onClick={continueWithGoogle}
            >
              {googleLoading ? 'Redirecting...' : 'Continue with Google'}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AuthPage;
