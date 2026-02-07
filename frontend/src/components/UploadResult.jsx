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

  return (
    <span className={`${styles.badge} ${colors[level] || styles.low}`}>
      {level.toUpperCase()}
    </span>
  );
};

const UploadResult = ({ data }) => {
  const { upload, validation, verification } = data;

  return (
    <Card>
      <div className={styles.result}>
        <div className={styles.header}>
          <h2>✓ Verification Complete</h2>
        </div>

        {/* Document Info */}
        <div className={styles.section}>
          <h3>Document Information</h3>
          <div className={styles.grid}>
            <div className={styles.field}>
              <span className={styles.label}>Filename:</span>
              <span className={styles.value}>{upload.metadata.original_filename}</span>
            </div>
            <div className={styles.field}>
              <span className={styles.label}>Type:</span>
              <span className={styles.value}>{upload.metadata.document_type.toUpperCase()}</span>
            </div>
            <div className={styles.field}>
              <span className={styles.label}>Size:</span>
              <span className={styles.value}>{(upload.metadata.file_size / 1024).toFixed(1)} KB</span>
            </div>
          </div>
        </div>

        {/* Validation Results */}
        <div className={styles.section}>
          <h3>Validation Results</h3>
          <div className={styles.scoreSection}>
            <div className={styles.scoreCircle}>
              <div className={styles.scoreValue}>
                {validation.fraud_score.toFixed(1)}
              </div>
              <div className={styles.scoreLabel}>Fraud Score</div>
            </div>
            <div className={styles.riskInfo}>
              <div className={styles.field}>
                <span className={styles.label}>Risk Level:</span>
                <RiskBadge level={validation.risk_level} />
              </div>
              <div className={styles.field}>
                <span className={styles.label}>Anomaly Detected:</span>
                <span className={styles.value}>{validation.is_anomaly ? 'Yes ⚠️' : 'No ✓'}</span>
              </div>
              <div className={styles.field}>
                <span className={styles.label}>Rule Violations:</span>
                <span className={styles.value}>{validation.rule_violations.length}</span>
              </div>
            </div>
          </div>

          {validation.text_excerpt && (
            <div className={styles.excerpt}>
              <strong>Extracted Text Preview:</strong>
              <p>{validation.text_excerpt}</p>
            </div>
          )}
        </div>

        {/* Verification Record */}
        <div className={styles.section}>
          <h3>Blockchain Record</h3>
          <div className={styles.field}>
            <span className={styles.label}>Batch ID:</span>
            <span className={styles.batchId}>{verification.batch_id}</span>
          </div>
          <div className={styles.field}>
            <span className={styles.label}>Record Hash:</span>
            <span className={styles.hash}>{verification.record_hash.substring(0, 16)}...</span>
          </div>
          <div className={styles.field}>
            <span className={styles.label}>Timestamp:</span>
            <span className={styles.value}>{new Date(verification.recorded_at).toLocaleString()}</span>
          </div>
        </div>

        {/* QR Code */}
        <div className={styles.section}>
          <h3>QR Code for Traceability</h3>
          <div className={styles.qrSection}>
            <img 
              src={verification.qr_code_url} 
              alt="Verification QR Code" 
              className={styles.qrCode}
            />
            <p className={styles.qrHint}>
              Print this QR code on packaging for instant verification
            </p>
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
