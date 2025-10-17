import type {
    Pothole,
    PotholeCreate,
    PotholeUpdate,
    PotholeStats,
    PotholeFilters,
    PotholeInAreaParams
} from '../types';
import { API_CONFIG, API_ENDPOINTS } from '../constants/api';

class PotholeApiService {
    private static instance: PotholeApiService;
    private baseURL: string;

    constructor() {
        this.baseURL = API_CONFIG.baseURL;
    }

    static getInstance(): PotholeApiService {
        if (!PotholeApiService.instance) {
            PotholeApiService.instance = new PotholeApiService();
        }
        return PotholeApiService.instance;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseURL}${endpoint}`;

        const config: RequestInit = {
            ...options,
            headers: {
                ...API_CONFIG.headers,
                ...options.headers,
            },
        };

        console.log(`Making API request to: ${url}`);

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`API request failed for ${endpoint}:`, {
                    status: response.status,
                    statusText: response.statusText,
                    error: errorText
                });
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            console.log(`API request successful for ${endpoint}:`, data);
            return data;
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);

            // Provide more helpful error messages
            if (error instanceof TypeError && error.message.includes('fetch')) {
                throw new Error(`Network error: Unable to connect to backend at ${this.baseURL}. Please check if the backend is running and CORS is configured.`);
            }

            throw error;
        }
    }

    // Get list of potholes with optional filters
    async getPotholes(filters: PotholeFilters = {}): Promise<Pothole[]> {
        const params = new URLSearchParams();

        Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null && key !== 'page' && key !== 'page_size') {
                params.append(key, value.toString());
            }
        });

        const endpoint = `${API_ENDPOINTS.potholes}${params.toString() ? `?${params}` : ''}`;
        const response = await this.request<Pothole[]>(endpoint);
        return response;
    }

    // Get all potholes (same as getPotholes now)
    async getAllPotholes(filters: PotholeFilters = {}): Promise<Pothole[]> {
        return this.getPotholes(filters);
    }

    // Get a specific pothole by ID
    async getPothole(id: number): Promise<Pothole> {
        return this.request<Pothole>(API_ENDPOINTS.potholeDetail(id));
    }

    // Get frame image for a specific pothole
    async getPotholeFrameImage(id: number): Promise<{ id: number, frame_number?: number, frame_image_base64: string }> {
        return this.request<{ id: number, frame_number?: number, frame_image_base64: string }>(API_ENDPOINTS.potholeFrameImage(id));
    }

    // Create a new pothole report
    async createPothole(data: PotholeCreate): Promise<Pothole> {
        const formData = new FormData();

        Object.entries(data).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                if (value instanceof File) {
                    formData.append(key, value);
                } else {
                    formData.append(key, value.toString());
                }
            }
        });

        return this.request<Pothole>(API_ENDPOINTS.potholes, {
            method: 'POST',
            body: formData,
            headers: {}, // Don't set Content-Type for FormData
        });
    }

    // Update an existing pothole
    async updatePothole(id: number, data: PotholeUpdate): Promise<Pothole> {
        const formData = new FormData();

        Object.entries(data).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                if (value instanceof File) {
                    formData.append(key, value);
                } else {
                    formData.append(key, value.toString());
                }
            }
        });

        return this.request<Pothole>(API_ENDPOINTS.potholeDetail(id), {
            method: 'PATCH',
            body: formData,
            headers: {}, // Don't set Content-Type for FormData
        });
    }

    // Delete a pothole
    async deletePothole(id: number): Promise<void> {
        await this.request<void>(API_ENDPOINTS.potholeDetail(id), {
            method: 'DELETE',
        });
    }

    // Get potholes within a specific area
    async getPotholesInArea(params: PotholeInAreaParams): Promise<Pothole[]> {
        const searchParams = new URLSearchParams({
            lat_center: params.lat_center.toString(),
            lng_center: params.lng_center.toString(),
            radius: (params.radius || 5).toString(),
        });

        const endpoint = `${API_ENDPOINTS.potholesInArea}?${searchParams}`;
        return this.request<Pothole[]>(endpoint);
    }

    // Get pothole statistics
    async getPotholeStats(): Promise<PotholeStats> {
        return this.request<PotholeStats>(API_ENDPOINTS.potholesStats);
    }

    // Update only the status of a pothole
    async updatePotholeStatus(id: number, status: string): Promise<Pothole> {
        return this.request<Pothole>(API_ENDPOINTS.updateStatus(id), {
            method: 'POST',
            body: JSON.stringify({ status }),
        });
    }

    // Get potholes within current map bounds
    async getPotholesInBounds(
        latMin: number,
        latMax: number,
        lngMin: number,
        lngMax: number
    ): Promise<Pothole[]> {
        const filters: PotholeFilters = {
            lat_min: latMin,
            lat_max: latMax,
            lng_min: lngMin,
            lng_max: lngMax,
        };

        return await this.getAllPotholes(filters);
    }
}

export const potholeApiService = PotholeApiService.getInstance();
