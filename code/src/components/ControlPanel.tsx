import React from 'react';
import type { Location } from '../types';

interface ControlPanelProps {
  showSatellite: boolean;
  showMajorRoadsOnly: boolean;
  onToggleSatellite: () => void;
  onToggleRoads: () => void;
  onResetLocation: () => void;
  onNavigateToUpload?: () => void;
  onNavigateToGovAuth?: () => void;
  onNavigateToRoadHealth?: () => void;
  currentLocation: Location;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  showSatellite,
  showMajorRoadsOnly,
  onToggleSatellite,
  onToggleRoads,
  onResetLocation,
  onNavigateToUpload,
  onNavigateToGovAuth,
  onNavigateToRoadHealth,
  currentLocation
}) => {
  return (
    <div className="control-panel">
      <div className="control-group">
        <h3>Map Controls</h3>

        <div className="control-item">
          <button
            className={`toggle-button ${showSatellite ? 'active' : ''}`}
            onClick={onToggleSatellite}
            title="Toggle satellite view"
          >
            {showSatellite ? '🛰️ Satellite' : '🗺️ Road Map'}
          </button>
        </div>

        <div className="control-item">
          <button
            className={`toggle-button ${showMajorRoadsOnly ? 'active' : ''}`}
            onClick={onToggleRoads}
            title="Toggle road display"
            disabled={showSatellite}
          >
            {showMajorRoadsOnly ? '🛣️ Major Roads' : '🛤️ All Roads'}
          </button>
        </div>

        <div className="control-item">
          <button
            className="action-button"
            onClick={onResetLocation}
            title="Reset to Bhubaneswar"
          >
            🏠 Reset to Default
          </button>
        </div>

        {onNavigateToUpload && (
          <div className="control-item">
            <button
              className="upload-button"
              onClick={onNavigateToUpload}
              title="Upload dashcam videos for processing"
            >
              📹 Upload Videos
            </button>
          </div>
        )}

        {onNavigateToGovAuth && (
          <div className="control-item">
            <button
              className="gov-segment-btn"
              onClick={onNavigateToGovAuth}
              title="Segment road and allocate contractor (Government users only)"
              style={{
                padding: '10px 16px',
                fontWeight: 'bold',
                background: '#1976d2',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                width: '100%'
              }}
            >
              🏛️ Government Authorization
            </button>
          </div>
        )}

        {onNavigateToRoadHealth && (
          <div className="control-item">
            <button
              className="road-health-btn"
              onClick={onNavigateToRoadHealth}
              title="View road health status based on pothole density and warranty"
              style={{
                padding: '10px 16px',
                fontWeight: 'bold',
                background: '#16a34a',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                width: '100%'
              }}
            >
              🏥 Road Health
            </button>
          </div>
        )}
      </div>

      <div className="location-info">
        <h4>Current Location</h4>
        <div className="location-details">
          <div className="location-name">{currentLocation.name}</div>
          <div className="coordinates">
            Lat: {currentLocation.lat.toFixed(4)},
            Lng: {currentLocation.lng.toFixed(4)}
          </div>
        </div>
      </div>
    </div>
  );
};
