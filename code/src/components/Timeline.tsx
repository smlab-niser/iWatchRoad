import { useState, useEffect } from 'react';
import type { Pothole } from '../types';

interface TimelineProps {
    potholes: Pothole[];
    onDateRangeChange: (startDate: Date, endDate: Date) => void;
}

export const Timeline: React.FC<TimelineProps> = ({ potholes, onDateRangeChange }) => {
    const [selectedDate, setSelectedDate] = useState<Date>(new Date());
    const [timeRange, setTimeRange] = useState<number>(30); // days

    // Get date range for timeline
    const dates = potholes.map(p => new Date(p.timestamp)).sort((a, b) => a.getTime() - b.getTime());
    const minDate = dates[0] || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    const maxDate = dates[dates.length - 1] || new Date();

    useEffect(() => {
        // Only apply date filtering if user has explicitly selected something
        // For now, we'll disable automatic date filtering to show all potholes
        // const endDate = selectedDate;
        // const startDate = new Date(endDate.getTime() - timeRange * 24 * 60 * 60 * 1000);
        // onDateRangeChange(startDate, endDate);
    }, [selectedDate, timeRange, onDateRangeChange]);

    const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = parseInt(e.target.value);
        const totalRange = maxDate.getTime() - minDate.getTime();
        const newDate = new Date(minDate.getTime() + (totalRange * value / 100));
        setSelectedDate(newDate);
    };

    const getSliderPosition = () => {
        const totalRange = maxDate.getTime() - minDate.getTime();
        const currentPosition = selectedDate.getTime() - minDate.getTime();
        return totalRange > 0 ? (currentPosition / totalRange) * 100 : 0;
    };

    return (
        <div className="timeline">
            <div className="timeline-header">
                <h3>📅 Timeline</h3>
                <div className="timeline-controls">
                    <label>
                        Range:
                        <select
                            value={timeRange}
                            onChange={(e) => setTimeRange(parseInt(e.target.value))}
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
                </div>
            </div>
        </div>
    );
};
