export interface Location {
  lat: number;
  lng: number;
  name: string;
}

export interface SearchResult {
  place_id: string;
  display_name: string;
  lat: string;
  lon: string;
  boundingbox: string[];
}

export interface MapViewProps {
  location: Location;
  onLocationChange: (location: Location) => void;
  showSatellite: boolean;
  showMajorRoadsOnly: boolean;
}

// Pothole-related types for backend integration
export interface Pothole {
  id: number;
  latitude: string;
  longitude: string;
  location_string: string;
  num_potholes: number;
  status: PotholeStatus;
  severity: PotholeSeverity;
  image: string | null;
  frame_image_base64?: string | null;
  frame_number?: number | null;
  timestamp: string;
  created_at: string;
  updated_at: string;
  description?: string;
  road_c_date?: string | null;
  contractor?: string | null;
}

export interface PotholeCreate {
  latitude: number;
  longitude: number;
  num_potholes: number;
  status: PotholeStatus;
  severity: PotholeSeverity;
  description?: string;
  image?: File | null;
}

export interface PotholeUpdate {
  num_potholes?: number;
  status?: PotholeStatus;
  severity?: PotholeSeverity;
  description?: string;
  image?: File | null;
}

export type PotholeStatus = 'reported' | 'verified' | 'in_progress' | 'fixed' | 'closed';
export type PotholeSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface PotholeStats {
  total_reports: number;
  total_potholes: number;
  by_status: Record<PotholeStatus, number>;
  by_severity: Record<PotholeSeverity, number>;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface PotholeFilters {
  status?: PotholeStatus;
  severity?: PotholeSeverity;
  lat_min?: number;
  lat_max?: number;
  lng_min?: number;
  lng_max?: number;
  search?: string;
  ordering?: string;
}

export interface PotholeInAreaParams {
  lat_center: number;
  lng_center: number;
  radius?: number;
}
