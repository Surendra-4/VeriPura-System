import React, { useState } from 'react';
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
        <header className={styles.header}>
          <h1>VeriPura Document Verification</h1>
          <p className={styles.subtitle}>
            Upload supply chain documents for AI-powered fraud detection and blockchain verification
          </p>
        </header>

        {!uploadResult ? (
          <Card>
            <FileUpload onFileSelect={handleFileSelect} disabled={uploading} />

            {selectedFile && (
              <div className={styles.fileInfo}>
                <div className={styles.fileName}>
                  <strong>Selected:</strong> {selectedFile.name}
                </div>
                <div className={styles.fileSize}>
                  {(selectedFile.size / 1024).toFixed(1)} KB
                </div>
              </div>
            )}

            {error && (
              <div className={styles.error}>
                ⚠️ {error}
              </div>
            )}

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
                <p>Processing document... This may take a few seconds.</p>
              </div>
            )}
          </Card>
        ) : (
          <>
            <UploadResult data={uploadResult} />
            <div className={styles.actions}>
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
