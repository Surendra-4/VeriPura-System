import React, { useState, useRef } from 'react';
import styles from './FileUpload.module.css';

const FileUpload = ({ onFileSelect, disabled = false }) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const handleFileInput = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div
      className={`${styles.uploadArea} ${isDragging ? styles.dragging : ''} ${disabled ? styles.disabled : ''}`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      onClick={handleClick}
    >
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleFileInput}
        accept=".pdf,.png,.jpg,.jpeg,.csv"
        disabled={disabled}
        style={{ display: 'none' }}
      />

      <div className={styles.uploadIcon}>VP</div>
      <p className={styles.uploadText}>
        <strong>Drop a file here</strong> or click to browse
      </p>
      <p className={styles.uploadHint}>PDF, PNG, JPG, JPEG, CSV up to 10 MB</p>

      <div className={styles.tagRow}>
        <span className={styles.tag}>OCR Ready</span>
        <span className={styles.tag}>AI Fraud Scan</span>
        <span className={styles.tag}>Ledger Proof</span>
      </div>
    </div>
  );
};

export default FileUpload;
