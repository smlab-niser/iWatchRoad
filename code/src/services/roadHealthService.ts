import type { RoadHealthData, ContractorMessage } from '../types';
import { API_CONFIG } from '../constants/api';

class RoadHealthService {
    private static instance: RoadHealthService;
    private baseURL: string;

    constructor() {
        this.baseURL = API_CONFIG.baseURL;
    }

    static getInstance(): RoadHealthService {
        if (!RoadHealthService.instance) {
            RoadHealthService.instance = new RoadHealthService();
        }
        return RoadHealthService.instance;
    }

    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = `${this.baseURL}${endpoint}`;

        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers,
                },
                credentials: 'include',
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`API Error: ${response.status} - ${errorText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Request failed: ${url}`, error);
            throw error;
        }
    }

    // Get road health data for all segments
    async getRoadHealthData(): Promise<RoadHealthData[]> {
        return this.request<RoadHealthData[]>('/road-health/');
    }

    // Send message to contractor
    async sendContractorMessage(data: {
        segment_id: number;
        message: string;
        message_type: 'auto' | 'manual';
    }): Promise<ContractorMessage> {
        return this.request<ContractorMessage>('/contractor-messages/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // Get contractor message history
    async getContractorMessages(segment_id?: number): Promise<ContractorMessage[]> {
        const endpoint = segment_id
            ? `/contractor-messages/?segment_id=${segment_id}`
            : '/contractor-messages/';
        return this.request<ContractorMessage[]>(endpoint);
    }

    // Update road health after data upload
    async updateRoadHealthAfterUpload(): Promise<void> {
        return this.request<void>('/road-health/update/', {
            method: 'POST',
        });
    }

    // Refresh road health from current road segments
    async refreshFromSegments(): Promise<{
        message: string;
        updated_count: number;
        analytics: any;
    }> {
        return this.request<{
            message: string;
            updated_count: number;
            analytics: any;
        }>('/road-health/refresh_from_segments/', {
            method: 'POST',
        });
    }

    // Update all road health data
    async updateAll(): Promise<{
        message: string;
        updated_count: number;
    }> {
        return this.request<{
            message: string;
            updated_count: number;
        }>('/road-health/update_all/', {
            method: 'POST',
        });
    }

    // Get road health color based on status
    getRoadHealthColor(status: RoadHealthData['health_status']): string {
        const colors = {
            critical: '#dc2626',    // Red: >200 potholes, under warranty
            warning: '#ea580c',     // Orange: >200 potholes, not under warranty  
            caution: '#eab308',     // Yellow: <200 potholes, under warranty
            good: '#16a34a'         // Green: <200 potholes, not under warranty
        };
        return colors[status];
    }

    // Determine road health status
    determineHealthStatus(potholeCount: number, isUnderWarranty: boolean): RoadHealthData['health_status'] {
        if (potholeCount >= 200) {
            return isUnderWarranty ? 'critical' : 'warning';
        } else {
            return isUnderWarranty ? 'caution' : 'good';
        }
    }

    // Check if automatic messaging should be triggered
    shouldTriggerAutoMessage(status: RoadHealthData['health_status']): boolean {
        return status === 'critical' || status === 'warning';
    }
}

export const roadHealthService = RoadHealthService.getInstance();
