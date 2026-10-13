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

// Basemap tile URLs (all key-free; CARTO basemaps now require an API key)
export const TILE_LAYERS = {
  standard: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
  roads: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
};

// Highest zoom each basemap actually serves tiles for; Leaflet upscales beyond it
export const TILE_MAX_NATIVE_ZOOM = {
  standard: 16,
  satellite: 18,
  roads: 19
};

// Nominatim API base URL for location search
export const NOMINATIM_BASE_URL = 'https://nominatim.openstreetmap.org/search';
