import type { Location } from '../types';

// Default location: Bhubaneswar, India
export const DEFAULT_LOCATION: Location = {
  lat: 20.2961,
  lng: 85.8245,
  name: 'Bhubaneswar, India'
};

// Map configuration
export const MAP_CONFIG = {
  defaultZoom: 13,
  minZoom: 3,
  maxZoom: 18,
  searchDebounceMs: 300,
  animationDuration: 1000
};

// OpenStreetMap tile URLs
export const TILE_LAYERS = {
  standard: 'https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png',
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  roads: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
};

// Nominatim API base URL for location search
export const NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org/search';
