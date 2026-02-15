import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { googleCallbackLogin } from '../api/services';
import { setAccessToken } from '../auth/token';
import styles from './GoogleCallbackPage.module.css';

const GoogleCallbackPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState('');

  useEffect(() => {
    const run = async () => {
      const oauthError = searchParams.get('error');
      const code = searchParams.get('code');
      const state = searchParams.get('state');

      if (oauthError) {
        setError('Google authentication was cancelled or denied.');
        return;
      }

      if (!code) {
        setError('Missing Google authorization code.');
        return;
      }

      try {
        const result = await googleCallbackLogin(code, state);
        setAccessToken(result.access_token);
        navigate('/dashboard', { replace: true });
      } catch (err) {
        setError(err.response?.data?.detail?.error || 'Google authentication failed.');
      }
    };

    run();
  }, [navigate, searchParams]);

  return (
    <section className={styles.page}>
      <div className="container">
        <div className={styles.card}>
          {!error ? (
            <>
              <h1>Signing you in...</h1>
              <p>Completing secure authentication with Google.</p>
            </>
          ) : (
            <>
              <h1>Google Login Failed</h1>
              <p>{error}</p>
              <button className={styles.button} type="button" onClick={() => navigate('/auth')}>
                Back to Login
              </button>
            </>
          )}
        </div>
      </div>
    </section>
  );
};

export default GoogleCallbackPage;
