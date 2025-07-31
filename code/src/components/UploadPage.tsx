import React, { useState } from 'react';
import './UploadPage.css';

interface UploadPageProps {
  onNavigateToMap: () => void;
}

const UploadPage: React.FC<UploadPageProps> = ({ onNavigateToMap }) => {
  const [videoFiles, setVideoFiles] = useState<FileList | null>(null);
  const [gpsFiles, setGpsFiles] = useState<FileList | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStatus, setProcessingStatus] = useState<string>('');
  const [distanceThreshold, setDistanceThreshold] = useState<number>(2.5);

  const handleVideoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    setVideoFiles(event.target.files);
  };

  const handleGpsUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    setGpsFiles(event.target.files);
  };

  const uploadFiles = async (files: FileList, endpoint: string) => {
    const formData = new FormData();
    Array.from(files).forEach((file) => {
      formData.append('files', file);
    });

    const response = await fetch(endpoint, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    return await response.json();
  };

  const processVideo = async (videoPath: string, gpsDirectory: string) => {
    const response = await fetch('/api/process-video/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        video_path: videoPath,
        gps_directory: gpsDirectory,
        distance_threshold: distanceThreshold,
      }),
    });

    if (!response.ok) {
      throw new Error(`Processing failed: ${response.statusText}`);
    }

    return await response.json();
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!videoFiles || !gpsFiles) {
      alert('Please select both video and GPS files');
      return;
    }

    setIsProcessing(true);
    setProcessingStatus('Uploading files...');

    try {
      // Upload video files
      setProcessingStatus('Uploading video files...');
      const videoUploadResult = await uploadFiles(videoFiles, '/api/upload-videos/');

      // Upload GPS files
      setProcessingStatus('Uploading GPS files...');
      const gpsUploadResult = await uploadFiles(gpsFiles, '/api/upload-gps/');

      // Process each video with corresponding GPS data
      const videoResults = [];
      for (const videoPath of videoUploadResult.uploaded_files) {
        setProcessingStatus(`Processing video: ${videoPath}...`);
        const result = await processVideo(videoPath, gpsUploadResult.upload_directory);
        videoResults.push(result);
      }

      setProcessingStatus('Processing complete! Database updated successfully.');

      // Auto-navigate to map after 2 seconds
      setTimeout(() => {
        onNavigateToMap();
      }, 2000);

    } catch (error) {
      console.error('Error processing files:', error);
      setProcessingStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="upload-page">
      <div className="upload-container">
        <div className="upload-header">
          <h1>Upload Dashcam Data</h1>
          <p>Upload your dashcam videos and GPS files to detect and map potholes</p>
          <button
            className="nav-button"
            onClick={onNavigateToMap}
            disabled={isProcessing}
          >
            ← Back to Map
          </button>
        </div>

        <form onSubmit={handleSubmit} className="upload-form">
          <div className="file-input-section">
            <h3>📹 Video Files</h3>
            <p>Select one or more MP4 video files from your dashcam</p>
            <input
              type="file"
              accept=".mp4,.avi,.mov"
              multiple
              onChange={handleVideoUpload}
              className="file-input"
              disabled={isProcessing}
            />
            {videoFiles && (
              <div className="file-list">
                <p>Selected videos:</p>
                <ul>
                  {Array.from(videoFiles).map((file, index) => (
                    <li key={index}>{file.name} ({(file.size / 1024 / 1024).toFixed(1)} MB)</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="file-input-section">
            <h3>🗺️ GPS Files</h3>
            <p>Select corresponding GPS .git files</p>
            <input
              type="file"
              accept=".git"
              multiple
              onChange={handleGpsUpload}
              className="file-input"
              disabled={isProcessing}
            />
            {gpsFiles && (
              <div className="file-list">
                <p>Selected GPS files:</p>
                <ul>
                  {Array.from(gpsFiles).map((file, index) => (
                    <li key={index}>{file.name} ({(file.size / 1024).toFixed(1)} KB)</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="settings-section">
            <h3>⚙️ Processing Settings</h3>
            <div className="setting-item">
              <label htmlFor="distance-threshold">
                Distance Threshold (meters):
                <span className="setting-help">
                  Minimum distance between detected potholes to avoid duplicates
                </span>
              </label>
              <input
                id="distance-threshold"
                type="number"
                min="0.5"
                max="10"
                step="0.5"
                value={distanceThreshold}
                onChange={(e) => setDistanceThreshold(parseFloat(e.target.value))}
                disabled={isProcessing}
              />
            </div>
          </div>

          <div className="submit-section">
            <button
              type="submit"
              className="submit-button"
              disabled={isProcessing || !videoFiles || !gpsFiles}
            >
              {isProcessing ? '🔄 Processing...' : '🚀 Process Videos'}
            </button>
          </div>
        </form>

        {processingStatus && (
          <div className={`status-message ${isProcessing ? 'processing' : 'complete'}`}>
            <p>{processingStatus}</p>
            {isProcessing && (
              <div className="progress-bar">
                <div className="progress-bar-fill"></div>
              </div>
            )}
          </div>
        )}

        <div className="info-section">
          <h3>ℹ️ How it works</h3>
          <ol>
            <li>Upload your dashcam video files (MP4 format recommended)</li>
            <li>Upload corresponding GPS .git files from your dashcam</li>
            <li>The system will process videos using AI to detect potholes</li>
            <li>GPS coordinates will be matched with detected potholes</li>
            <li>Results will be automatically added to the pothole database</li>
            <li>You'll be redirected to the map to view the new data</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default UploadPage;
