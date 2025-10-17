// API configuration and base URL
export const API_CONFIG = {
    baseURL: '/project/iwatchroad/api', // Use full path with PRE_URL
    timeout: 10000,
    headers: {
        'Content-Type': 'application/json',
    },
    useDemoMode: false, // Always use real backend data
};

// API endpoints
export const API_ENDPOINTS = {
    potholes: '/potholes/',
    potholeDetail: (id: number) => `/potholes/${id}/`,
    potholeFrameImage: (id: number) => `/potholes/${id}/frame_image/`,
    potholesInArea: '/potholes/in_area/',
    potholesStats: '/potholes/stats/',
    updateStatus: (id: number) => `/potholes/${id}/update_status/`,
    roadHealth: '/road-health/',
    contractorMessages: '/contractor-messages/',
    updateRoadHealth: '/road-health/update/',
} as const;
