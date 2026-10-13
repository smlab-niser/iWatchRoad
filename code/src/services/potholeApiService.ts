import type {
    Pothole,
    PotholeCreate,
    PotholeUpdate,
    PotholeStats,
    PotholeFilters,
    PotholeInAreaParams
} from '../types';
import { API_CONFIG, API_ENDPOINTS } from '../constants/api';

type StandardizedEnvelope<T> = {
    success?: boolean;
    message?: string;
    data?: T;
    errors?: unknown;
};
const EMPTY_POTHOLE_STATS: PotholeStats = {
    total_reports: 0,
    total_potholes: 0,
    by_status: {
        reported: 0,
        verified: 0,
        in_progress: 0,
        fixed: 0,
        closed: 0,
    },
    by_severity: {
        low: 0,
        medium: 0,
        high: 0,
        critical: 0,
    },
};

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

    private isRecord(value: unknown): value is Record<string, unknown> {
        return typeof value === 'object' && value !== null && !Array.isArray(value);
    }

    private isEnvelope<T>(value: unknown): value is StandardizedEnvelope<T> {
        return this.isRecord(value) && ('success' in value || 'data' in value || 'errors' in value);
    }

    private unwrapEnvelope<T>(responseData: unknown, endpoint: string): T {
        if (this.isEnvelope<T>(responseData)) {
            if (responseData.success === false) {
                const message = typeof responseData.message === 'string' && responseData.message.trim()
                    ? responseData.message
                    : `Request failed for ${endpoint}`;
                throw new Error(message);
            }

            if (!('data' in responseData)) {
                throw new Error(`Malformed response from ${endpoint}: missing data field`);
            }

            return responseData.data as T;
        }

        return responseData as T;
    }

    private extractList<T>(payload: unknown, endpoint: string): T[] {
        if (Array.isArray(payload)) {
            return payload as T[];
        }

        if (this.isRecord(payload) && Array.isArray(payload.results)) {
            return payload.results as T[];
        }

        console.warn(`Unexpected list payload from ${endpoint}; falling back to empty list.`, payload);
        return [];
    }

    private extractObject<T>(payload: unknown, endpoint: string): T {
        if (this.isRecord(payload)) {
            return payload as T;
        }

        throw new Error(`Malformed response from ${endpoint}: expected an object`);
    }

    private async request(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<unknown> {
        const url = `${this.baseURL}${endpoint}`;
        const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;

        const headers: Record<string, string> = {
            ...API_CONFIG.headers,
            ...(options.headers as Record<string, string> | undefined),
        };

        if (isFormData) {
            delete headers['Content-Type'];
        }

        const config: RequestInit = {
            ...options,
            headers,
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

            if (response.status === 204) {
                console.log(`API request successful for ${endpoint}: no content`);
                return null;
            }

            const responseText = await response.text();
            if (!responseText.trim()) {
                console.log(`API request successful for ${endpoint}: empty response body`);
                return null;
            }

            try {
                const data = JSON.parse(responseText) as unknown;
                console.log(`API request successful for ${endpoint}:`, data);
                return data;
            } catch (parseError) {
                console.warn(`API request returned non-JSON payload for ${endpoint}:`, responseText);
                return responseText;
            }
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
        const response = await this.request(endpoint);
        const payload = this.unwrapEnvelope<unknown>(response, endpoint);
        return this.extractList<Pothole>(payload, endpoint);
    }

    // Get all potholes (same as getPotholes now)
    async getAllPotholes(filters: PotholeFilters = {}): Promise<Pothole[]> {
        return this.getPotholes(filters);
    }

    // Get a specific pothole by ID
    async getPothole(id: number): Promise<Pothole> {
        const endpoint = API_ENDPOINTS.potholeDetail(id);
        const response = await this.request(endpoint);
        const payload = this.unwrapEnvelope<unknown>(response, endpoint);
        return this.extractObject<Pothole>(payload, endpoint);
    }

    // Get frame image for a specific pothole
    async getPotholeFrameImage(id: number): Promise<{ id: number, frame_number?: number, frame_image_base64?: string, frame_image_url?: string }> {
        const endpoint = API_ENDPOINTS.potholeFrameImage(id);
        const response = await this.request(endpoint);
        const payload = this.unwrapEnvelope<unknown>(response, endpoint);
        return this.extractObject<{ id: number, frame_number?: number, frame_image_base64?: string, frame_image_url?: string }>(payload, endpoint);
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

        const endpoint = API_ENDPOINTS.potholes;
        const response = await this.request(endpoint, {
            method: 'POST',
            body: formData,
        });
        const payload = this.unwrapEnvelope<unknown>(response, endpoint);
        return this.extractObject<Pothole>(payload, endpoint);
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

        const endpoint = API_ENDPOINTS.potholeDetail(id);
        const response = await this.request(endpoint, {
            method: 'PATCH',
            body: formData,
        });
        const payload = this.unwrapEnvelope<unknown>(response, endpoint);
        return this.extractObject<Pothole>(payload, endpoint);
    }

    // Delete a pothole
    async deletePothole(id: number): Promise<void> {
        const endpoint = API_ENDPOINTS.potholeDetail(id);
        const response = await this.request(endpoint, {
            method: 'DELETE',
        });
        this.unwrapEnvelope<unknown>(response, endpoint);
    }

    // Get potholes within a specific area
    async getPotholesInArea(params: PotholeInAreaParams): Promise<Pothole[]> {
        const searchParams = new URLSearchParams({
            lat_center: params.lat_center.toString(),
            lng_center: params.lng_center.toString(),
            radius: (params.radius || 5).toString(),
        });

        const endpoint = `${API_ENDPOINTS.potholesInArea}?${searchParams}`;
        const response = await this.request(endpoint);
        const payload = this.unwrapEnvelope<unknown>(response, endpoint);
        return this.extractList<Pothole>(payload, endpoint);
    }

    // Get pothole statistics
    async getPotholeStats(): Promise<PotholeStats> {
        const endpoint = API_ENDPOINTS.potholesStats;
        const response = await this.request(endpoint);
        const payload = this.unwrapEnvelope<unknown>(response, endpoint);

        if (!this.isRecord(payload)) {
            console.warn(`Unexpected stats payload from ${endpoint}; falling back to zero values.`, payload);
            return EMPTY_POTHOLE_STATS;
        }

        const totalReports = typeof payload.total_reports === 'number' ? payload.total_reports : EMPTY_POTHOLE_STATS.total_reports;
        const totalPotholes = typeof payload.total_potholes === 'number' ? payload.total_potholes : EMPTY_POTHOLE_STATS.total_potholes;
        const byStatus = this.isRecord(payload.by_status) ? payload.by_status as PotholeStats['by_status'] : EMPTY_POTHOLE_STATS.by_status;
        const bySeverity = this.isRecord(payload.by_severity) ? payload.by_severity as PotholeStats['by_severity'] : EMPTY_POTHOLE_STATS.by_severity;

        return {
            total_reports: totalReports,
            total_potholes: totalPotholes,
            by_status: {
                reported: Number(byStatus.reported ?? 0),
                verified: Number(byStatus.verified ?? 0),
                in_progress: Number(byStatus.in_progress ?? 0),
                fixed: Number(byStatus.fixed ?? 0),
                closed: Number(byStatus.closed ?? 0),
            },
            by_severity: {
                low: Number(bySeverity.low ?? 0),
                medium: Number(bySeverity.medium ?? 0),
                high: Number(bySeverity.high ?? 0),
                critical: Number(bySeverity.critical ?? 0),
            },
        };
    }

    // Update only the status of a pothole
    async updatePotholeStatus(id: number, status: string): Promise<Pothole> {
        const endpoint = API_ENDPOINTS.updateStatus(id);
        const response = await this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify({ status }),
        });
        const payload = this.unwrapEnvelope<unknown>(response, endpoint);
        return this.extractObject<Pothole>(payload, endpoint);
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
