import type {
    GovUser,
    GovAuthCredentials,
    GovSignupData,
    RoadSegment,
    RoadSegmentForm
} from '../types';

// Government API configuration - using separate database
const GOV_API_CONFIG = {
    baseURL: '/project/iwatchroad/gov-api', // Separate API for government features
    headers: {
        'Content-Type': 'application/json',
    },
};

class GovApiService {
    private static instance: GovApiService;
    private baseURL: string;
    private authToken: string | null = null;

    constructor() {
        this.baseURL = GOV_API_CONFIG.baseURL;
    }

    static getInstance(): GovApiService {
        if (!GovApiService.instance) {
            GovApiService.instance = new GovApiService();
        }
        return GovApiService.instance;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseURL}${endpoint}`;

        const config: RequestInit = {
            ...options,
            headers: {
                ...GOV_API_CONFIG.headers,
                ...(this.authToken && { Authorization: `Bearer ${this.authToken}` }),
                ...options.headers,
            },
        };

        console.log(`Making Government API request to: ${url}`);

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                const errorText = await response.text();
                console.error(`Government API request failed for ${endpoint}:`, {
                    status: response.status,
                    statusText: response.statusText,
                    error: errorText
                });
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }

            const data = await response.json();
            console.log(`Government API request successful for ${endpoint}:`, data);
            return data;
        } catch (error) {
            console.error(`Government API request failed for ${endpoint}:`, error);

            // Provide more helpful error messages
            if (error instanceof TypeError && error.message.includes('fetch')) {
                throw new Error(`Network error: Unable to connect to government backend. Please check if the service is running.`);
            }

            throw error;
        }
    }

    // Authentication methods
    async login(credentials: GovAuthCredentials): Promise<{ user: GovUser; token: string }> {
        const response = await this.request<{ user: GovUser; token: string }>('/auth/login/', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });

        this.authToken = response.token;
        localStorage.setItem('gov_auth_token', response.token);
        localStorage.setItem('gov_user', JSON.stringify(response.user));

        return response;
    }

    async signup(data: GovSignupData): Promise<{ user: GovUser; message: string }> {
        return this.request<{ user: GovUser; message: string }>('/auth/signup/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async logout(): Promise<void> {
        try {
            await this.request('/auth/logout/', {
                method: 'POST',
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            this.authToken = null;
            localStorage.removeItem('gov_auth_token');
            localStorage.removeItem('gov_user');
        }
    }

    // Check if user is authenticated
    isAuthenticated(): boolean {
        const token = localStorage.getItem('gov_auth_token');
        if (token) {
            this.authToken = token;
            return true;
        }
        return false;
    }

    // Get current user from localStorage
    getCurrentUser(): GovUser | null {
        const userStr = localStorage.getItem('gov_user');
        return userStr ? JSON.parse(userStr) : null;
    }

    // Road segment methods
    async createRoadSegment(points: [number, number][], formData: RoadSegmentForm): Promise<RoadSegment> {
        const roadSegmentData = {
            points: points,
            contractor_id: formData.contractor_id,
            contractor_name: formData.contractor_name,
            contractor_email: formData.contractor_email,
            contractor_phone: formData.contractor_phone,
            road_creation_date: formData.road_creation_date,
            warranty_period: formData.warranty_period,
            money_sanctioned: formData.money_sanctioned,
        };

        return this.request<RoadSegment>('/road-segments/', {
            method: 'POST',
            body: JSON.stringify(roadSegmentData),
        });
    }

    async getRoadSegments(): Promise<RoadSegment[]> {
        return this.request<RoadSegment[]>('/road-segments/');
    }

    async updateRoadSegment(id: number, data: Partial<RoadSegment>): Promise<RoadSegment> {
        return this.request<RoadSegment>(`/road-segments/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async deleteRoadSegment(id: number): Promise<void> {
        return this.request<void>(`/road-segments/${id}/`, {
            method: 'DELETE',
        });
    }

    // Verify token validity
    async verifyToken(): Promise<boolean> {
        if (!this.authToken) return false;

        try {
            await this.request('/auth/verify/', {
                method: 'POST',
            });
            return true;
        } catch (error) {
            this.logout();
            return false;
        }
    }
}

export const govApiService = GovApiService.getInstance();
