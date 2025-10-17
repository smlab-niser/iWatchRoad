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

// Government Authorization Types
export interface GovUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  department?: string;
  created_at: string;
}

export interface GovAuthCredentials {
  username: string;
  password: string;
}

export interface GovSignupData {
  username: string;
  email: string;
  password: string;
  full_name: string;
  department?: string;
}

export interface RoadSegment {
  id?: number;
  points: [number, number][]; // Array of [lat, lng] coordinates
  contractor_id: string;
  contractor_name: string;
  contractor_email: string;
  contractor_phone: string;
  road_creation_date: string;
  warranty_period: number; // in months
  money_sanctioned: number;
  created_by?: {
    id: number;
    username: string;
    email: string;
    full_name: string;
    department?: string;
    created_at: string;
  };
  created_at?: string;
  updated_at?: string;
}

export interface RoadSegmentForm {
  contractor_id: string;
  contractor_name: string;
  contractor_email: string;
  contractor_phone: string;
  road_creation_date: string;
  warranty_period: number;
  money_sanctioned: number;
}

// Road Health Types
export type RoadHealthStatus = 'critical' | 'warning' | 'caution' | 'good';

export interface RoadHealthData {
  segment_id?: number;
  pothole_count: number;
  is_under_warranty: boolean;
  health_status: RoadHealthStatus;
  contractor_info?: {
    contractor_id: string;
    contractor_name: string;
    contractor_email: string;
    contractor_phone: string;
  };
  points: [number, number][];
}

export interface ContractorMessage {
  id?: number;
  segment_id: number;
  contractor_email: string;
  contractor_phone: string;
  message: string;
  message_type: 'auto' | 'manual';
  sent_at?: string;
  status?: 'sent' | 'failed' | 'pending';
  notification_results?: {
    email: {
      success: boolean;
      error?: string;
    };
    sms: {
      success: boolean;
      error?: string;
    };
  };
}
