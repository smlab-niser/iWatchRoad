import { useState, useEffect } from 'react';
import type { Pothole } from '../types';

interface TimelineProps {
    potholes: Pothole[];
    onDateRangeChange: (startDate: Date | null, endDate: Date | null) => void;
}

export const Timeline: React.FC<TimelineProps> = ({ potholes, onDateRangeChange }) => {
    const [selectedDate, setSelectedDate] = useState<Date>(new Date());
    const [timeRange, setTimeRange] = useState<number>(30); // days
    const [isActive, setIsActive] = useState<boolean>(false); // Track if timeline filtering is active

    // Get date range for timeline
    const dates = potholes.map(p => new Date(p.timestamp)).sort((a, b) => a.getTime() - b.getTime());
    const minDate = dates[0] || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    const maxDate = dates[dates.length - 1] || new Date();

    // Initialize selectedDate to the most recent date when potholes load
    useEffect(() => {
        if (potholes.length > 0 && maxDate) {
            setSelectedDate(maxDate);
        }
    }, [potholes.length, maxDate.getTime()]);

    useEffect(() => {
        // Apply date filtering only when timeline is active
        if (isActive) {
            const endDate = selectedDate;
            const startDate = new Date(endDate.getTime() - timeRange * 24 * 60 * 60 * 1000);
            console.log('Timeline: Applying date filter', { startDate, endDate, range: timeRange });
            onDateRangeChange(startDate, endDate);
        } else {
            // Show all potholes when timeline is not active
            console.log('Timeline: Showing all potholes');
            onDateRangeChange(null, null);
        }
    }, [selectedDate, timeRange, isActive, onDateRangeChange]);

    const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(e.target.value);
        const totalRange = maxDate.getTime() - minDate.getTime();
        const newDate = new Date(minDate.getTime() + (totalRange * value / 100));
        setSelectedDate(newDate);
        if (!isActive) {
            setIsActive(true); // Activate timeline when user interacts with slider
        }
    };

    const handleRangeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        setTimeRange(parseInt(e.target.value));
        if (!isActive) {
            setIsActive(true); // Activate timeline when user changes range
        }
    };

    const handleShowAll = () => {
        setIsActive(false); // Deactivate timeline to show all potholes
    };

    const getSliderPosition = () => {
        const totalRange = maxDate.getTime() - minDate.getTime();
        const currentPosition = selectedDate.getTime() - minDate.getTime();
        return totalRange > 0 ? (currentPosition / totalRange) * 100 : 0;
    };

    return (
        <div className="timeline">
            <div className="timeline-header">
                <h3>📅 Timeline {isActive && '(Active)'}</h3>
                <div className="timeline-info">
                    {potholes.length > 0 && (
                        <span className="timeline-count">
                            {potholes.length} potholes ({minDate.toLocaleDateString()} - {maxDate.toLocaleDateString()})
                        </span>
                    )}
                </div>
                <div className="timeline-controls">
                    <button
                        onClick={handleShowAll}
                        className={`timeline-button ${!isActive ? 'active' : ''}`}
                        title="Show all potholes"
                    >
                        Show All
                    </button>
                    <label>
                        Range:
                        <select
                            value={timeRange}
                            onChange={handleRangeChange}
                            className="timeline-select"
                        >
                            <option value={7}>7 days</option>
                            <option value={30}>30 days</option>
                            <option value={90}>90 days</option>
                            <option value={365}>1 year</option>
                        </select>
                    </label>
                </div>
            </div>

            <div className="timeline-slider">
                <div className="timeline-dates">
                    <span>{minDate.toLocaleDateString()}</span>
                    <span>{maxDate.toLocaleDateString()}</span>
                </div>
                <input
                    type="range"
                    min="0"
                    max="100"
                    value={getSliderPosition()}
                    onChange={handleSliderChange}
                    className="timeline-range"
                />
                <div className="timeline-current">
                    Current: {selectedDate.toLocaleDateString()}
                    {isActive && (
                        <span className="timeline-status">
                            {' '}(Showing {timeRange} days from this date)
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
};
