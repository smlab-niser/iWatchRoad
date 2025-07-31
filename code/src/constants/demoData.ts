export const DEMO_POTHOLES: any[] = [
    {
        id: 1,
        latitude: 20.2961,
        longitude: 85.8245,
        num_potholes: 3,
        status: 'reported',
        severity: 'medium',
        description: 'Multiple potholes on main road near market',
        timestamp: '2024-01-15T10:30:00Z',
        created_at: '2024-01-15T10:30:00Z',
        updated_at: '2024-01-15T10:30:00Z',
        image: null
    },
    {
        id: 2,
        latitude: 20.3019,
        longitude: 85.8197,
        num_potholes: 1,
        status: 'verified',
        severity: 'high',
        description: 'Large pothole causing traffic issues',
        timestamp: '2024-01-16T14:15:00Z',
        created_at: '2024-01-16T14:15:00Z',
        updated_at: '2024-01-16T14:15:00Z',
        image: null
    },
    {
        id: 3,
        latitude: 20.2942,
        longitude: 85.8211,
        num_potholes: 2,
        status: 'in_progress',
        severity: 'low',
        description: 'Small potholes on residential street',
        timestamp: '2024-01-17T09:45:00Z',
        created_at: '2024-01-17T09:45:00Z',
        updated_at: '2024-01-17T09:45:00Z',
        image: null
    },
    {
        id: 4,
        latitude: 20.3091,
        longitude: 85.8314,
        num_potholes: 5,
        status: 'fixed',
        severity: 'critical',
        description: 'Major road damage - fixed',
        timestamp: '2024-01-10T16:20:00Z',
        created_at: '2024-01-10T16:20:00Z',
        updated_at: '2024-01-20T12:00:00Z',
        image: null
    },
    {
        id: 5,
        latitude: 20.2975,
        longitude: 85.8267,
        num_potholes: 1,
        status: 'reported',
        severity: 'medium',
        description: 'Pothole near bus stop',
        timestamp: '2024-01-18T11:30:00Z',
        created_at: '2024-01-18T11:30:00Z',
        updated_at: '2024-01-18T11:30:00Z',
        image: null
    }
];

export const DEMO_STATS = {
    total: 5,
    by_status: {
        reported: 2,
        verified: 1,
        in_progress: 1,
        fixed: 1,
        closed: 0
    },
    by_severity: {
        low: 1,
        medium: 2,
        high: 1,
        critical: 1
    }
};
