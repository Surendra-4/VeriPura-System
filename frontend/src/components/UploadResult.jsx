import React from 'react';
import Card from './Card';
import styles from './UploadResult.module.css';

const RiskBadge = ({ level }) => {
  const colors = {
    low: styles.low,
    medium: styles.medium,
    high: styles.high,
    critical: styles.critical,
  };

  return <span className={`${styles.badge} ${colors[level] || styles.low}`}>{level.toUpperCase()}</span>;
};

const UploadResult = ({ data }) => {
  const { upload, validation, verification } = data;

  return (
    <Card className={styles.card}>
      <div className={styles.result}>
        <div className={styles.header}>
          <div>
            <p className={styles.kicker}>Verification Complete</p>
            <h2>{upload.metadata.original_filename}</h2>
            <p className={styles.subtitle}>
              Batch <strong>{verification.batch_id}</strong> is recorded in the verification ledger.
            </p>
          </div>
          <RiskBadge level={validation.risk_level} />
        </div>

        <div className={styles.scoreBand}>
          <div className={styles.scoreTile}>
            <span className={styles.tileLabel}>Fraud Score</span>
            <span className={styles.tileValue}>{validation.fraud_score.toFixed(1)}</span>
          </div>
          <div className={styles.scoreTile}>
            <span className={styles.tileLabel}>Anomaly</span>
            <span className={styles.tileValue}>{validation.is_anomaly ? 'Yes' : 'No'}</span>
          </div>
          <div className={styles.scoreTile}>
            <span className={styles.tileLabel}>Rule Violations</span>
            <span className={styles.tileValue}>{validation.rule_violations.length}</span>
          </div>
        </div>

        <div className={styles.section}>
          <h3>Document Profile</h3>
          <div className={styles.grid}>
            <div className={styles.field}>
              <span className={styles.label}>Filename</span>
              <span className={styles.value}>{upload.metadata.original_filename}</span>
            </div>
            <div className={styles.field}>
              <span className={styles.label}>Type</span>
              <span className={styles.value}>{upload.metadata.document_type.toUpperCase()}</span>
            </div>
            <div className={styles.field}>
              <span className={styles.label}>Size</span>
              <span className={styles.value}>{(upload.metadata.file_size / 1024).toFixed(1)} KB</span>
            </div>
          </div>
        </div>

        <div className={styles.section}>
          <h3>Ledger Record</h3>
          <div className={styles.grid}>
            <div className={styles.field}>
              <span className={styles.label}>Batch ID</span>
              <span className={styles.value}>{verification.batch_id}</span>
            </div>
            <div className={styles.field}>
              <span className={styles.label}>Record Hash</span>
              <span className={styles.hash}>{verification.record_hash.substring(0, 24)}...</span>
            </div>
            <div className={styles.field}>
              <span className={styles.label}>Timestamp</span>
              <span className={styles.value}>{new Date(verification.recorded_at).toLocaleString()}</span>
            </div>
          </div>
        </div>

        {validation.text_excerpt && (
          <div className={styles.section}>
            <h3>Extracted Text Preview</h3>
            <div className={styles.excerpt}>{validation.text_excerpt}</div>
          </div>
        )}

        <div className={styles.section}>
          <h3>QR Traceability</h3>
          <div className={styles.qrSection}>
            <img src={verification.qr_code_url} alt="Verification QR Code" className={styles.qrCode} />
            <p className={styles.qrHint}>Attach this QR to packaging for one-scan verification.</p>
            <a
              href={verification.qr_code_url}
              download={`${verification.batch_id}.png`}
              className={styles.downloadButton}
            >
              Download QR Code
            </a>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default UploadResult;
