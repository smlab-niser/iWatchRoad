import type { PotholeStatus, PotholeSeverity } from '../types';

interface FilterPanelProps {
    onStatusFilter: (status: PotholeStatus | 'all') => void;
    onSeverityFilter: (severity: PotholeSeverity | 'all') => void;
    selectedStatus: PotholeStatus | 'all';
    selectedSeverity: PotholeSeverity | 'all';
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
    onStatusFilter,
    onSeverityFilter,
    selectedStatus,
    selectedSeverity
}) => {
    const statusOptions: Array<PotholeStatus | 'all'> = ['all', 'reported', 'verified', 'in_progress', 'fixed', 'closed'];
    const severityOptions: Array<PotholeSeverity | 'all'> = ['all', 'low', 'medium', 'high', 'critical'];

    const formatLabel = (value: string) => {
        if (value === 'all') return 'All';
        return value.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    return (
        <div className="filter-panel">
            <h3>🔍 Filters</h3>

            <div className="filter-group">
                <label>Status:</label>
                <select
                    value={selectedStatus}
                    onChange={(e) => onStatusFilter(e.target.value as PotholeStatus | 'all')}
                    className="filter-select"
                >
                    {statusOptions.map(status => (
                        <option key={status} value={status}>
                            {formatLabel(status)}
                        </option>
                    ))}
                </select>
            </div>

            <div className="filter-group">
                <label>Severity:</label>
                <select
                    value={selectedSeverity}
                    onChange={(e) => onSeverityFilter(e.target.value as PotholeSeverity | 'all')}
                    className="filter-select"
                >
                    {severityOptions.map(severity => (
                        <option key={severity} value={severity}>
                            {formatLabel(severity)}
                        </option>
                    ))}
                </select>
            </div>
        </div>
    );
};
