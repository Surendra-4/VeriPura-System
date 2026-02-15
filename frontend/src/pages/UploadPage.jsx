import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import FileUpload from '../components/FileUpload';
import UploadResult from '../components/UploadResult';
import LoadingSpinner from '../components/LoadingSpinner';
import Card from '../components/Card';
import { uploadDocument } from '../api/services';
import styles from './UploadPage.module.css';

const UploadPage = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setError(null);
    setUploadResult(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError(null);

    try {
      const result = await uploadDocument(selectedFile);
      setUploadResult(result);
      setSelectedFile(null);
    } catch (err) {
      const apiError = err.response?.data?.detail?.error;

      if (apiError) {
        setError(apiError);
      } else if (err.response?.status) {
        setError(`Upload failed (${err.response.status}). Please try again.`);
      } else if (err.request) {
        setError('Upload request was blocked or no response was received. Please refresh and try again.');
      } else {
        setError('Upload failed. Please try again.');
      }

      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setUploadResult(null);
    setError(null);
  };

  return (
    <div className={styles.page}>
      <div className="container">
        <header className={styles.hero}>
          <p className={styles.kicker}>AI Validation + Immutable Ledger</p>
          <h1>Build Supply Chain Confidence In Minutes</h1>
          <p className={styles.subtitle}>
            VeriPura verifies food documents with machine intelligence and tamper-evident traceability,
            helping teams detect fraud before it reaches buyers.
          </p>

          <div className={styles.metricRow}>
            <div className={styles.metricCard}>
              <span className={styles.metricValue}>6M+</span>
              <span className={styles.metricLabel}>Food-borne illnesses annually</span>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricValue}>$7B</span>
              <span className={styles.metricLabel}>U.S. food waste impact</span>
            </div>
            <div className={styles.metricCard}>
              <span className={styles.metricValue}>24/7</span>
              <span className={styles.metricLabel}>Verification readiness</span>
            </div>
          </div>

          <div className={styles.heroActions}>
            <Link to="/verify" className={styles.secondaryLink}>
              Verify Existing Batch
            </Link>
          </div>
        </header>

        {!uploadResult ? (
          <div className={styles.workspace}>
            <Card className={styles.uploadPanel}>
              <div className={styles.panelHeader}>
                <h2>Upload Document</h2>
                <p>Submit invoices, food safety certificates, scans, or CSV shipment logs.</p>
              </div>

              <FileUpload onFileSelect={handleFileSelect} disabled={uploading} />

              {selectedFile && (
                <div className={styles.fileInfo}>
                  <div>
                    <p className={styles.fileLabel}>Selected file</p>
                    <p className={styles.fileName}>{selectedFile.name}</p>
                  </div>
                  <p className={styles.fileSize}>{(selectedFile.size / 1024).toFixed(1)} KB</p>
                </div>
              )}

              {error && <div className={styles.error}>Warning: {error}</div>}

              {selectedFile && !uploading && (
                <div className={styles.actions}>
                  <button onClick={handleUpload} className={styles.uploadButton}>
                    Upload & Verify
                  </button>
                  <button onClick={handleReset} className={styles.cancelButton}>
                    Cancel
                  </button>
                </div>
              )}

              {uploading && (
                <div className={styles.uploading}>
                  <LoadingSpinner size="large" />
                  <p>Running OCR, anomaly checks, and ledger recording. This can take 20-40 seconds.</p>
                </div>
              )}
            </Card>

            <Card className={styles.infoPanel}>
              <h3>Why teams choose VeriPura</h3>
              <ul className={styles.benefitList}>
                <li>Detect suspicious patterns before approvals happen.</li>
                <li>Create cryptographic records for every verified batch.</li>
                <li>Generate traceability QR codes for downstream partners.</li>
              </ul>

              <div className={styles.timeline}>
                <h4>Verification flow</h4>
                <ol>
                  <li>Upload food supply-chain document</li>
                  <li>AI extracts text and computes fraud features</li>
                  <li>Result is chained into immutable verification ledger</li>
                </ol>
              </div>
            </Card>
          </div>
        ) : (
          <>
            <UploadResult data={uploadResult} />
            <div className={styles.actionsBottom}>
              <button onClick={handleReset} className={styles.uploadButton}>
                Upload Another Document
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default UploadPage;
