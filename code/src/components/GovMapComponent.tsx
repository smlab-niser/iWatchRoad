import React, { useState, useCallback, useRef, useEffect } from 'react';
import { MapContainer, TileLayer, useMapEvents, Polyline, Marker, Popup } from 'react-leaflet';
import type { RoadSegmentForm, RoadSegment } from '../types';
import { DEFAULT_LOCATION } from '../constants';
import { govApiService } from '../services/govApiService';
import 'leaflet/dist/leaflet.css';

interface GovMapComponentProps {
    onSubmitSegment: (points: [number, number][], formData: RoadSegmentForm) => Promise<void>;
    onExit: () => void;
}

interface MapClickHandlerProps {
    onAddPoint: (lat: number, lng: number) => void;
}

const MapClickHandler: React.FC<MapClickHandlerProps> = ({ onAddPoint }) => {
    useMapEvents({
        click: (e) => {
            onAddPoint(e.latlng.lat, e.latlng.lng);
        },
    });
    return null;
};

// Function to get route between two points using a simple routing service
const getRoute = async (start: [number, number], end: [number, number]): Promise<[number, number][]> => {
    try {
        // Using a simpler approach with OSRM (Open Source Routing Machine)
        const response = await fetch(
            `https://router.project-osrm.org/route/v1/driving/${start[1]},${start[0]};${end[1]},${end[0]}?overview=full&geometries=geojson`
        );

        if (response.ok) {
            const data = await response.json();
            if (data.routes && data.routes[0] && data.routes[0].geometry) {
                // Convert coordinates from [lon, lat] to [lat, lon]
                return data.routes[0].geometry.coordinates.map((coord: [number, number]) => [coord[1], coord[0]]);
            }
        }
    } catch (error) {
        console.error('Routing service error:', error);
    }

    // Fallback to straight line if routing fails
    console.log('Using fallback straight line route');
    return [start, end];
};

// Function to generate consistent colors for contractor names
const getContractorColor = (contractorName: string): string => {
    // Create a simple hash of the contractor name to generate consistent colors
    let hash = 0;
    for (let i = 0; i < contractorName.length; i++) {
        hash = contractorName.charCodeAt(i) + ((hash << 5) - hash);
    }

    // Convert hash to HSL color for better variety and visibility
    const hue = Math.abs(hash) % 360;
    return `hsl(${hue}, 70%, 50%)`;
};

export const GovMapComponent: React.FC<GovMapComponentProps> = ({
    onSubmitSegment,
    onExit
}) => {
    const [points, setPoints] = useState<[number, number][]>([]);
    const [routePoints, setRoutePoints] = useState<[number, number][]>([]);
    const [showForm, setShowForm] = useState(false);
    const [loading, setLoading] = useState(false);
    const [routeLoading, setRouteLoading] = useState(false);
    const [existingRoadSegments, setExistingRoadSegments] = useState<RoadSegment[]>([]);
    const [selectedSegment, setSelectedSegment] = useState<RoadSegment | null>(null);
    const [isEditMode, setIsEditMode] = useState(false);
    const [form, setForm] = useState<RoadSegmentForm>({
        contractor_id: '',
        contractor_name: '',
        contractor_email: '',
        contractor_phone: '',
        road_creation_date: '',
        warranty_period: 12,
        money_sanctioned: 0
    });

    const mapRef = useRef<any>(null);

    // Load existing road segments when component mounts
    useEffect(() => {
        const loadRoadSegments = async () => {
            try {
                const segments = await govApiService.getRoadSegments();
                setExistingRoadSegments(segments);
            } catch (error) {
                console.error('Failed to load road segments:', error);
            }
        };

        loadRoadSegments();
    }, []);

    // Handle editing a road segment
    const handleEditSegment = (segment: RoadSegment) => {
        setSelectedSegment(segment);
        setIsEditMode(true);

        // Set the points from the segment (use first and last points as start and end)
        const segmentPoints = segment.points;
        if (segmentPoints.length >= 2) {
            const startPoint = segmentPoints[0];
            const endPoint = segmentPoints[segmentPoints.length - 1];
            setPoints([startPoint, endPoint]);
            setRoutePoints(segmentPoints); // Set the full route
        }

        setForm({
            contractor_id: segment.contractor_id,
            contractor_name: segment.contractor_name,
            contractor_email: segment.contractor_email,
            contractor_phone: segment.contractor_phone,
            road_creation_date: segment.road_creation_date,
            warranty_period: segment.warranty_period,
            money_sanctioned: segment.money_sanctioned
        });
        setShowForm(true);
    };

    // Handle clicking on existing road segment
    const handleSegmentClick = (segment: RoadSegment) => {
        // Show segment details or edit option
        if (confirm(`Edit road segment by ${segment.contractor_name}?`)) {
            handleEditSegment(segment);
        }
    };

    const handleAddPoint = useCallback(async (lat: number, lng: number) => {
        const newPoint: [number, number] = [lat, lng];
        setPoints(prev => {
            // Restrict to maximum 2 points
            if (prev.length >= 2) {
                alert('Maximum 2 points allowed. Please clear existing points to add new ones.');
                return prev;
            }

            const updatedPoints = [...prev, newPoint];

            // If we have exactly 2 points, get the route between them
            if (updatedPoints.length === 2) {
                setRouteLoading(true);
                getRoute(updatedPoints[0], updatedPoints[1]).then(route => {
                    setRoutePoints(route);
                    setRouteLoading(false);
                }).catch(error => {
                    console.error('Route error:', error);
                    setRouteLoading(false);
                });
            }

            return updatedPoints;
        });
    }, []);

    const handleRemovePoint = useCallback((index: number) => {
        setPoints(prev => {
            const newPoints = prev.filter((_, i) => i !== index);

            // Clear route when we have less than 2 points
            if (newPoints.length < 2) {
                setRoutePoints([]);
            } else if (newPoints.length === 2) {
                // Recalculate route for the remaining 2 points
                setRouteLoading(true);
                getRoute(newPoints[0], newPoints[1]).then(route => {
                    setRoutePoints(route);
                    setRouteLoading(false);
                }).catch(error => {
                    console.error('Route error:', error);
                    setRouteLoading(false);
                });
            }

            return newPoints;
        });
    }, []);

    const handleClearAll = () => {
        setPoints([]);
        setRoutePoints([]);
        setShowForm(false);
        setIsEditMode(false);
        setSelectedSegment(null);
        setForm({
            contractor_id: '',
            contractor_name: '',
            contractor_email: '',
            contractor_phone: '',
            road_creation_date: '',
            warranty_period: 12,
            money_sanctioned: 0
        });
    };

    const handleOkay = () => {
        if (points.length !== 2) {
            alert('Please select exactly 2 points to create a road segment');
            return;
        }
        setIsEditMode(false);
        setSelectedSegment(null);
        setShowForm(true);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!form.contractor_id || !form.contractor_name || !form.contractor_email ||
            !form.contractor_phone || !form.road_creation_date || !form.money_sanctioned) {
            alert('Please fill all required fields');
            return;
        }

        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(form.contractor_email)) {
            alert('Please enter a valid email address');
            return;
        }

        // Basic phone validation
        const phoneRegex = /^[\+]?[1-9][\d]{9,14}$/;
        if (!phoneRegex.test(form.contractor_phone.replace(/[\s\-\(\)]/g, ''))) {
            alert('Please enter a valid phone number');
            return;
        }

        if (form.money_sanctioned <= 0) {
            alert('Money sanctioned must be greater than 0');
            return;
        }

        setLoading(true);
        try {
            if (isEditMode && selectedSegment) {
                // Update existing road segment
                const updateData = {
                    contractor_id: form.contractor_id,
                    contractor_name: form.contractor_name,
                    contractor_email: form.contractor_email,
                    contractor_phone: form.contractor_phone,
                    road_creation_date: form.road_creation_date,
                    warranty_period: form.warranty_period,
                    money_sanctioned: form.money_sanctioned
                };

                await govApiService.updateRoadSegment(selectedSegment.id!, updateData);

                // Reload road segments to update the display
                const segments = await govApiService.getRoadSegments();
                setExistingRoadSegments(segments);

                alert('Road segment updated successfully!');
            } else {
                // Use the route points if available, otherwise fall back to clicked points
                const pointsToSubmit = routePoints.length > 0 ? routePoints : points;
                await onSubmitSegment(pointsToSubmit, form);

                // Reload road segments to include the new one
                const segments = await govApiService.getRoadSegments();
                setExistingRoadSegments(segments);

                alert('Road segment submitted successfully!');
            }

            // Reset form and points after successful submission
            handleClearAll();
        } catch (error) {
            console.error('Submit error:', error);
            alert(isEditMode ? 'Failed to update road segment. Please try again.' : 'Failed to submit road segment. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const isFormValid = form.contractor_id && form.contractor_name && form.contractor_email &&
        form.contractor_phone && form.road_creation_date && form.warranty_period > 0 &&
        form.money_sanctioned > 0;

    return (
        <div className="gov-map-container">
            {/* Exit Button */}
            <button className="exit-button" onClick={onExit}>
                ✕ Exit
            </button>

            {/* Map */}
            <MapContainer
                center={[DEFAULT_LOCATION.lat, DEFAULT_LOCATION.lng]}
                zoom={13}
                style={{ height: '100vh', width: '100%' }}
                ref={mapRef}
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />

                <MapClickHandler onAddPoint={handleAddPoint} />

                {/* Render markers for each point */}
                {points.map((point, index) => (
                    <Marker
                        key={index}
                        position={point}
                        eventHandlers={{
                            click: () => handleRemovePoint(index)
                        }}
                    />
                ))}

                {/* Render polyline connecting the points along roads */}
                {routePoints.length > 1 && (
                    <Polyline
                        positions={routePoints}
                        color={isEditMode ? "orange" : "blue"}
                        weight={4}
                        opacity={isEditMode ? 0.9 : 0.7}
                        dashArray={isEditMode ? "10, 5" : undefined}
                    />
                )}

                {/* Render existing road segments with contractor-based colors */}
                {existingRoadSegments.map((segment) => {
                    // Don't render the segment being edited to avoid confusion
                    if (isEditMode && selectedSegment && segment.id === selectedSegment.id) {
                        return null;
                    }

                    return (
                        <Polyline
                            key={segment.id}
                            positions={segment.points}
                            color={getContractorColor(segment.contractor_name)}
                            weight={5}
                            opacity={isEditMode ? 0.3 : 0.8} // Reduce opacity of other segments when editing
                            eventHandlers={{
                                click: () => handleSegmentClick(segment)
                            }}
                        >
                            <Popup>
                                <div className="segment-popup">
                                    <h3>Road Segment Details</h3>
                                    <p><strong>Contractor:</strong> {segment.contractor_name}</p>
                                    <p><strong>Contractor ID:</strong> {segment.contractor_id}</p>
                                    <p><strong>Email:</strong> {segment.contractor_email}</p>
                                    <p><strong>Phone:</strong> {segment.contractor_phone}</p>
                                    <p><strong>Creation Date:</strong> {segment.road_creation_date}</p>
                                    <p><strong>Warranty:</strong> {segment.warranty_period} months</p>
                                    <p><strong>Money Sanctioned:</strong> ₹{segment.money_sanctioned}</p>
                                    <button
                                        onClick={() => handleEditSegment(segment)}
                                        className="edit-segment-button"
                                    >
                                        Edit Segment
                                    </button>
                                </div>
                            </Popup>
                        </Polyline>
                    );
                })}

                {/* Show loading indicator for route calculation */}
                {routeLoading && points.length >= 2 && (
                    <div className="route-loading">
                        Calculating road route...
                    </div>
                )}
            </MapContainer>

            {/* Road Segments Legend */}
            {existingRoadSegments.length > 0 && (
                <div className="road-segments-legend">
                    <div className="legend-title">Contractors</div>
                    {Array.from(new Set(existingRoadSegments.map(segment => segment.contractor_name))).map(contractorName => (
                        <div key={contractorName} className="legend-item">
                            <div
                                className="legend-color"
                                style={{ backgroundColor: getContractorColor(contractorName) }}
                            />
                            <div className="legend-contractor">{contractorName}</div>
                        </div>
                    ))}
                </div>
            )}

            {/* Control Panel */}
            <div className="gov-control-panel">
                <div className="control-info">
                    <h3>{isEditMode ? 'Edit Road Segment' : 'Road Segment Creator'}</h3>
                    <p>Click on the map to select exactly 2 points. Click on existing markers to remove them.</p>
                    <p>Click on colored road lines to view/edit existing segments.</p>
                    {isEditMode && (
                        <p style={{ color: '#10b981', fontWeight: 'bold' }}>📝 Editing mode: You can modify the points and route</p>
                    )}
                    <p>Points selected: {points.length}/2</p>
                    {points.length === 2 && routePoints.length > 0 && (
                        <p>Route calculated: {routePoints.length} coordinates along roads</p>
                    )}
                    {routeLoading && (
                        <p style={{ color: '#3b82f6', fontWeight: 'bold' }}>🔄 Calculating route...</p>
                    )}
                    {points.length < 2 && !isEditMode && (
                        <p style={{ color: '#f59e0b', fontWeight: 'bold' }}>⚠️ Please select 2 points to create a road segment</p>
                    )}
                    {points.length < 2 && isEditMode && (
                        <p style={{ color: '#f59e0b', fontWeight: 'bold' }}>⚠️ Please select 2 points to update the road segment</p>
                    )}
                </div>

                <div className="control-actions">
                    <button
                        className="clear-button"
                        onClick={handleClearAll}
                        disabled={points.length === 0}
                    >
                        {isEditMode ? 'Cancel Edit' : 'Clear All'}
                    </button>
                    <button
                        className="okay-button"
                        onClick={handleOkay}
                        disabled={points.length !== 2}
                    >
                        {isEditMode
                            ? (points.length === 2 ? 'Update Road Segment' : `Select 2 Points (${points.length}/2)`)
                            : (points.length === 2 ? 'Create Road Segment' : `Select 2 Points (${points.length}/2)`)
                        }
                    </button>
                </div>
            </div>

            {/* Road Segment Form Modal */}
            {showForm && (
                <div className="modal-overlay">
                    <div className="road-form-modal">
                        <div className="modal-header">
                            <h3>{isEditMode ? 'Edit Road Segment' : 'Road Segment Details'}</h3>
                            <button
                                className="close-button"
                                onClick={() => setShowForm(false)}
                            >
                                ×
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="road-form">
                            <div className="form-group">
                                <label htmlFor="contractor_id">
                                    Contractor ID: <span className="required">*</span>
                                </label>
                                <input
                                    type="text"
                                    id="contractor_id"
                                    value={form.contractor_id}
                                    onChange={(e) => setForm(prev => ({ ...prev, contractor_id: e.target.value }))}
                                    placeholder="e.g., CONT-2024-001"
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="contractor_name">
                                    Contractor Name: <span className="required">*</span>
                                </label>
                                <input
                                    type="text"
                                    id="contractor_name"
                                    value={form.contractor_name}
                                    onChange={(e) => setForm(prev => ({ ...prev, contractor_name: e.target.value }))}
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="contractor_email">
                                    Contractor Email: <span className="required">*</span>
                                </label>
                                <input
                                    type="email"
                                    id="contractor_email"
                                    value={form.contractor_email}
                                    onChange={(e) => setForm(prev => ({ ...prev, contractor_email: e.target.value }))}
                                    placeholder="contractor@example.com"
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="contractor_phone">
                                    Contractor Phone: <span className="required">*</span>
                                </label>
                                <input
                                    type="tel"
                                    id="contractor_phone"
                                    value={form.contractor_phone}
                                    onChange={(e) => setForm(prev => ({ ...prev, contractor_phone: e.target.value }))}
                                    placeholder="e.g., 9876543210"
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="road_creation_date">
                                    Road Creation Date: <span className="required">*</span>
                                </label>
                                <input
                                    type="date"
                                    id="road_creation_date"
                                    value={form.road_creation_date}
                                    onChange={(e) => setForm(prev => ({ ...prev, road_creation_date: e.target.value }))}
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="warranty_period">
                                    Warranty Period (months): <span className="required">*</span>
                                </label>
                                <input
                                    type="number"
                                    id="warranty_period"
                                    value={form.warranty_period}
                                    onChange={(e) => setForm(prev => ({ ...prev, warranty_period: parseInt(e.target.value) || 0 }))}
                                    min="1"
                                    max="120"
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="money_sanctioned">
                                    Money Sanctioned (₹): <span className="required">*</span>
                                </label>
                                <input
                                    type="number"
                                    id="money_sanctioned"
                                    value={form.money_sanctioned}
                                    onChange={(e) => setForm(prev => ({ ...prev, money_sanctioned: parseFloat(e.target.value) || 0 }))}
                                    min="0"
                                    step="0.01"
                                    placeholder="e.g., 500000.00"
                                    required
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-actions">
                                <button
                                    type="submit"
                                    className="submit-button"
                                    disabled={!isFormValid || loading}
                                >
                                    {loading ? (isEditMode ? 'Updating...' : 'Submitting...') : (isEditMode ? 'Update' : 'Submit')}
                                </button>
                                <button
                                    type="button"
                                    className="cancel-button"
                                    onClick={() => handleClearAll()}
                                    disabled={loading}
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};
