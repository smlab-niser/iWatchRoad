import { useEffect, useState } from 'react';
import { potholeApiService } from '../services/potholeApiService';
import type { PotholeStats } from '../types';

export const PotholeStatsPanel: React.FC = () => {
    const [stats, setStats] = useState<PotholeStats | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadStats = async () => {
            setLoading(true);
            setError(null);

            try {
                console.log('Loading pothole stats...');
                const statsData = await potholeApiService.getPotholeStats();
                console.log('Loaded stats:', statsData);
                setStats(statsData);
            } catch (err) {
                console.error('Failed to load stats:', err);
                setError('Failed to load statistics');
            } finally {
                setLoading(false);
            }
        };

        loadStats();
    }, []);

    if (loading) {
        return <div className="stats-loading">Loading statistics...</div>;
    }

    if (error) {
        return <div className="stats-error">Error: {error}</div>;
    }

    if (!stats) {
        return <div className="stats-empty">No statistics available</div>;
    }

    return (
        <div className="pothole-stats">
            <h3>Pothole Statistics</h3>
            <div className="stats-grid">
                <div className="stat-item">
                    <span className="stat-label">Total Reports:</span>
                    <span className="stat-value">{stats.total_reports}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Total Potholes:</span>
                    <span className="stat-value">{stats.total_potholes}</span>
                </div>

                <div className="stat-section">
                    <h4>By Status:</h4>
                    {Object.entries(stats.by_status).map(([status, count]) => (
                        <div key={status} className="stat-item">
                            <span className="stat-label">{status.replace('_', ' ')}:</span>
                            <span className="stat-value">{count}</span>
                        </div>
                    ))}
                </div>

                <div className="stat-section">
                    <h4>By Severity:</h4>
                    {Object.entries(stats.by_severity).map(([severity, count]) => (
                        <div key={severity} className="stat-item">
                            <span className="stat-label">{severity}:</span>
                            <span className="stat-value">{count}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};
