import React from 'react';
import type { Location } from '../types';

interface ControlPanelProps {
  showSatellite: boolean;
  showMajorRoadsOnly: boolean;
  onToggleSatellite: () => void;
  onToggleRoads: () => void;
  onResetLocation: () => void;
  onNavigateToUpload?: () => void;
  currentLocation: Location;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({
  showSatellite,
  showMajorRoadsOnly,
  onToggleSatellite,
  onToggleRoads,
  onResetLocation,
  onNavigateToUpload,
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
