import React, { useRef, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Map as LeafletMap } from 'leaflet';
import type { LatLngTuple } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Location, PotholeStatus, PotholeSeverity } from '../types';
import { MAP_CONFIG, TILE_LAYERS } from '../constants';
import { PotholeMarkers } from './PotholeMarkers';

// Fix for default markers in React-Leaflet
import L from 'leaflet';
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapComponentProps {
  location: Location;
  showSatellite: boolean;
  showMajorRoadsOnly: boolean;
  statusFilter?: PotholeStatus | 'all';
  severityFilter?: PotholeSeverity | 'all';
  dateRange?: { start: Date; end: Date };
  refreshTrigger?: number;
}

// Component to handle map updates
const MapController: React.FC<{ location: Location }> = ({ location }) => {
  const map = useMap();

  useEffect(() => {
    map.flyTo([location.lat, location.lng], MAP_CONFIG.defaultZoom, {
      duration: MAP_CONFIG.animationDuration / 1000
    });
  }, [map, location]);

  return null;
};

export const MapComponent: React.FC<MapComponentProps> = ({
  location,
  showSatellite,
  showMajorRoadsOnly,
  statusFilter = 'all',
  severityFilter = 'all',
  dateRange,
  refreshTrigger = 0
}) => {
  const mapRef = useRef<LeafletMap>(null);

  // Determine which tile layer to use
  const getTileUrl = () => {
    if (showSatellite) {
      return TILE_LAYERS.satellite;
    }
    return TILE_LAYERS.standard;
  };

  const getTileAttribution = () => {
    if (showSatellite) {
      return '&copy; <a href="https://www.esri.com/">Esri</a>';
    }
    return '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>';
  };

  const center: LatLngTuple = [location.lat, location.lng];

  useEffect(() => {
    // Add scale control when map is ready
    const map = mapRef.current;
    if (map) {
      L.control.scale({
        position: 'bottomleft',
        metric: true,
        imperial: false
      }).addTo(map);
    }
  }, []);

  return (
    <div className="map-container">
      <MapContainer
        center={center}
        zoom={MAP_CONFIG.defaultZoom}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
        zoomControl={true}
        scrollWheelZoom={true}
      >
        <TileLayer
          url={getTileUrl()}
          attribution={getTileAttribution()}
          maxZoom={MAP_CONFIG.maxZoom}
          minZoom={MAP_CONFIG.minZoom}
        />

        {/* Road overlay for major roads only */}
        {showMajorRoadsOnly && !showSatellite && (
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            opacity={0.7}
          />
        )}

        <Marker position={center}>
          <Popup>
            <div>
              <strong>{location.name}</strong>
              <br />
              Coordinates: {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
            </div>
          </Popup>
        </Marker>

        {/* Pothole markers */}
        <PotholeMarkers
          refresh={refreshTrigger}
          statusFilter={statusFilter}
          severityFilter={severityFilter}
          dateRange={dateRange}
        />

        <MapController location={location} />
      </MapContainer>
    </div>
  );
};
