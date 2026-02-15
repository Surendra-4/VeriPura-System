import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser } from '../api/services';
import { clearAccessToken } from '../auth/token';
import styles from './DashboardPage.module.css';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadMe = async () => {
      setLoading(true);
      setError('');

      try {
        const data = await getCurrentUser();
        setUser(data);
      } catch (err) {
        clearAccessToken();
        setError(err.response?.data?.detail?.error || 'Session expired. Please login again.');
      } finally {
        setLoading(false);
      }
    };

    loadMe();
  }, []);

  const logout = () => {
    clearAccessToken();
    navigate('/auth', { replace: true });
  };

  if (loading) {
    return (
      <section className={styles.page}>
        <div className="container">
          <div className={styles.card}>Loading dashboard...</div>
        </div>
      </section>
    );
  }

  if (error || !user) {
    return (
      <section className={styles.page}>
        <div className="container">
          <div className={styles.card}>
            <h1>Authentication Required</h1>
            <p>{error || 'Please sign in to continue.'}</p>
            <button className={styles.button} type="button" onClick={() => navigate('/auth')}>
              Go to Login
            </button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className={styles.page}>
      <div className="container">
        <div className={styles.card}>
          <h1>Dashboard</h1>
          <p>
            Logged in as: <strong>{user.email}</strong>
          </p>
          <p>
            Role: <strong>{user.role}</strong>
          </p>

          <button className={styles.button} type="button" onClick={logout}>
            Logout
          </button>
        </div>
      </div>
    </section>
  );
};

export default DashboardPage;
