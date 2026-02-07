import React from 'react';
import styles from './LoadingSpinner.module.css';

const LoadingSpinner = ({ size = 'medium' }) => {
  return (
    <div className={`${styles.spinner} ${styles[size]}`}>
      <div className={styles.circle}></div>
    </div>
  );
};

export default LoadingSpinner;
