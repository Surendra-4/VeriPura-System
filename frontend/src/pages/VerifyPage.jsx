import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Card from '../components/Card';
import LoadingSpinner from '../components/LoadingSpinner';
import { getVerificationRecord } from '../api/services';
import styles from './VerifyPage.module.css';

const VerifyPage = () => {
  const { batchId } = useParams();
  const navigate = useNavigate();
  const [searchId, setSearchId] = useState(batchId || '');
  const [record, setRecord] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (batchId) {
      fetchRecord(batchId);
    }
  }, [batchId]);

  const fetchRecord = async (id) => {
    setLoading(true);
    setError(null);

    try {
      const data = await getVerificationRecord(id);
      setRecord(data);
    } catch (err) {
      setError(err.response?.data?.detail?.error || 'Batch ID not found');
      setRecord(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchId.trim()) {
      navigate(`/verify/${searchId.trim()}`);
    }
  };

  return (
    <div className={styles.page}>
      <div className="container">
        <header className={styles.header}>
          <h1>Verify Document</h1>
          <p className={styles.subtitle}>
            Enter a batch ID to view verification details
          </p>
        </header>

        <Card>
          <form onSubmit={handleSearch} className={styles.searchForm}>
            <input
              type="text"
              value={searchId}
              onChange={(e) => setSearchId(e.target.value)}
              placeholder="Enter Batch ID (e.g., BATCH-20260207-A3F5E8)"
              className={styles.searchInput}
              disabled={loading}
            />
            <button type="submit" className={styles.searchButton} disabled={loading || !searchId.trim()}>
              Verify
            </button>
          </form>
        </Card>

        {loading && (
          <div className={styles.loading}>
            <LoadingSpinner size="large" />
            <p>Loading verification record...</p>
          </div>
        )}

        {error && (
          <Card>
            <div className={styles.error}>
              <h3>❌ Not Found</h3>
              <p>{error}</p>
            </div>
          </Card>
        )}

        {record && !loading && (
          <Card>
            <div className={styles.record}>
              <div className={styles.recordHeader}>
                <h2>✓ Verified</h2>
                <span className={styles.batchId}>{record.batch_id}</span>
              </div>

              <div className={styles.section}>
                <h3>Document Information</h3>
                <div className={styles.grid}>
                  <div className={styles.field}>
                    <span className={styles.label}>Filename:</span>
                    <span className={styles.value}>{record.document_metadata.original_filename}</span>
                  </div>
                  <div className={styles.field}>
                    <span className={styles.label}>Type:</span>
                    <span className={styles.value}>{record.document_metadata.document_type.toUpperCase()}</span>
                  </div>
                  <div className={styles.field}>
                    <span className={styles.label}>Size:</span>
                    <span className={styles.value}>{(record.document_metadata.file_size / 1024).toFixed(1)} KB</span>
                  </div>
                </div>
              </div>

              <div className={styles.section}>
                <h3>Validation Results</h3>
                <div className={styles.grid}>
                  <div className={styles.field}>
                    <span className={styles.label}>Fraud Score:</span>
                    <span className={styles.value}>{record.validation_result.fraud_score.toFixed(1)}</span>
                  </div>
                  <div className={styles.field}>
                    <span className={styles.label}>Risk Level:</span>
                    <span className={`${styles.badge} ${styles[record.validation_result.risk_level]}`}>
                      {record.validation_result.risk_level.toUpperCase()}
                    </span>
                  </div>
                  <div className={styles.field}>
                    <span className={styles.label}>Anomaly:</span>
                    <span className={styles.value}>{record.validation_result.is_anomaly ? 'Yes ⚠️' : 'No ✓'}</span>
                  </div>
                </div>
              </div>

              <div className={styles.section}>
                <h3>Blockchain Record</h3>
                <div className={styles.field}>
                  <span className={styles.label}>Record Hash:</span>
                  <span className={styles.hash}>{record.record_hash}</span>
                </div>
                <div className={styles.field}>
                  <span className={styles.label}>Previous Hash:</span>
                  <span className={styles.hash}>{record.previous_hash || 'Genesis Block'}</span>
                </div>
                <div className={styles.field}>
                  <span className={styles.label}>Timestamp:</span>
                  <span className={styles.value}>{new Date(record.timestamp).toLocaleString()}</span>
                </div>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default VerifyPage;
