import { useEffect, useState } from 'react';
import { Marker, Popup, Polyline } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet';
import type { Pothole, PotholeSeverity, PotholeStatus, RoadSegment } from '../types';
import { potholeApiService } from '../services/potholeApiService';
import { govApiService } from '../services/govApiService';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorDisplay } from './ErrorDisplay';
import { getClosestRoadSegment, getContractorColor } from '../utils/roadSegmentUtils';

interface PotholeMarkersProps {
    refresh?: number; // Used to trigger refresh
    statusFilter?: PotholeStatus | 'all';
    severityFilter?: PotholeSeverity | 'all';
    dateRange?: { start: Date; end: Date };
}

// Custom icons for different pothole severities
const createPotholeIcon = (severity: PotholeSeverity, status: PotholeStatus) => {
    const colors = {
        low: '#28a745',
        medium: '#ffc107',
        high: '#fd7e14',
        critical: '#dc3545'
    };

    const statusOpacity = status === 'fixed' || status === 'closed' ? 0.5 : 1;

    return L.divIcon({
        html: `
      <div style="
        background-color: ${colors[severity]};
        opacity: ${statusOpacity};
        width: 20px;
        height: 20px;
        border: 2px solid white;
        border-radius: 50%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        font-weight: bold;
        color: white;
      ">
        ${severity === 'critical' ? '!' : severity === 'high' ? '●' : '○'}
      </div>
    `,
        className: 'pothole-marker',
        iconSize: [20, 20],
        iconAnchor: [10, 10],
    });
};

// Custom cluster icon with dramatic scaling based on zoom level
const createCustomClusterIcon = (cluster: any) => {
    const count = cluster.getChildCount();
    const map = cluster._group._map;
    const zoom = map ? map.getZoom() : 10;

    // Dramatic scaling: invisible when zoomed out
    let scale = 1.5;
    if (zoom > 8) {
        if (zoom <= 10) {
            scale = 1.5;
        } else if (zoom <= 12) {
            scale = 1.1;
        } else if (zoom <= 14) {
            scale = 0.9;
        } else {
            scale = 0.8;
        }
    }

    return L.divIcon({
        html: `
            <div style="
                background-color: #ff0037ff;
                color: white;
                border: 2px solid white;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                font-weight: bold;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                transform: scale(${scale});
                transition: transform 0.3s ease;
                opacity: ${scale === 0 ? 0 : 1};
            ">
                ${count}
            </div>
        `,
        className: 'custom-cluster-icon',
        iconSize: [40, 40],
        iconAnchor: [20, 20],
    });
};

export const PotholeMarkers: React.FC<PotholeMarkersProps> = ({
    refresh = 0,
    statusFilter = 'all',
    severityFilter = 'all',
    dateRange
}) => {
    const [potholes, setPotholes] = useState<Pothole[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [frameImages, setFrameImages] = useState<Record<number, { frame_number?: number, frame_image_base64: string }>>({});
    const [loadingFrames, setLoadingFrames] = useState<Set<number>>(new Set());

    // Road segment related state
    const [roadSegments, setRoadSegments] = useState<RoadSegment[]>([]);
    const [selectedRoadSegment, setSelectedRoadSegment] = useState<RoadSegment | null>(null);
    const [highlightedPotholeId, setHighlightedPotholeId] = useState<number | null>(null);

    useEffect(() => {
        // Load all potholes data (without frame images for performance)
        const loadPotholes = async () => {
            setLoading(true);
            setError(null);

            try {
                // Use simplified getPotholes method to get all data
                const response = await potholeApiService.getPotholes({});
                setPotholes(response);
                console.log(`Loaded ${response.length} potholes for map display`);
            } catch (err) {
                console.error('Failed to load potholes:', err);
                setError('Failed to load pothole data');
            } finally {
                setLoading(false);
            }
        };

        loadPotholes();
    }, [refresh]);

    // Load road segments when component mounts
    useEffect(() => {
        const loadRoadSegments = async () => {
            try {
                const segments = await govApiService.getRoadSegments();
                setRoadSegments(segments);
                console.log(`Loaded ${segments.length} road segments for pothole analysis`);
            } catch (err) {
                console.error('Failed to load road segments:', err);
                // Don't set error state here as road segments are optional
            }
        };

        loadRoadSegments();
    }, []);

    // Function to handle pothole marker click and find associated road segment
    const handlePotholeClick = (pothole: Pothole) => {
        setHighlightedPotholeId(pothole.id);

        const potholePoint: [number, number] = [parseFloat(pothole.latitude), parseFloat(pothole.longitude)];

        // Find the closest road segment to this pothole
        const closestResult = getClosestRoadSegment(potholePoint, roadSegments);

        if (closestResult && closestResult.distance <= 100) { // Within 100 meters
            setSelectedRoadSegment(closestResult.segment);
            console.log(`Found road segment for pothole ${pothole.id}:`, closestResult.segment.contractor_name, `(${closestResult.distance.toFixed(1)}m away)`);
        } else {
            setSelectedRoadSegment(null);
            console.log(`No road segment found near pothole ${pothole.id}`);
        }
    };

    // Function to load frame image on demand
    const loadFrameImage = async (potholeId: number, event?: React.MouseEvent) => {
        // Prevent event bubbling to avoid popup closure
        if (event) {
            event.preventDefault();
            event.stopPropagation();
        }

        if (frameImages[potholeId] || loadingFrames.has(potholeId)) {
            return; // Already loaded or loading
        }

        setLoadingFrames(prev => new Set(prev).add(potholeId));

        try {
            const frameData = await potholeApiService.getPotholeFrameImage(potholeId);
            setFrameImages(prev => ({
                ...prev,
                [potholeId]: {
                    frame_number: frameData.frame_number,
                    frame_image_base64: frameData.frame_image_base64
                }
            }));
        } catch (err) {
            console.error(`Failed to load frame image for pothole ${potholeId}:`, err);
            // Don't show error to user for frame images, just log it
        } finally {
            setLoadingFrames(prev => {
                const newSet = new Set(prev);
                newSet.delete(potholeId);
                return newSet;
            });
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getSeverityColor = (severity: PotholeSeverity) => {
        const colors = {
            low: '#28a745',
            medium: '#ffc107',
            high: '#fd7e14',
            critical: '#dc3545'
        };
        return colors[severity];
    };

    const getStatusColor = (status: PotholeStatus) => {
        const colors = {
            reported: '#6c757d',
            verified: '#17a2b8',
            in_progress: '#ffc107',
            fixed: '#28a745',
            closed: '#6f42c1'
        };
        return colors[status];
    };

    const getSeverityLabel = (severity: PotholeSeverity) => {
        return severity.charAt(0).toUpperCase() + severity.slice(1);
    };

    const getStatusLabel = (status: PotholeStatus) => {
        return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    // Component to render road segment details
    const RoadSegmentDetails: React.FC<{ segment: RoadSegment }> = ({ segment }) => (
        <div style={{
            marginTop: '16px',
            padding: '12px',
            backgroundColor: '#f1f5f9',
            borderRadius: '8px',
            border: `2px solid ${getContractorColor(segment.contractor_name)}`,
        }}>
            <div style={{
                display: 'flex',
                alignItems: 'center',
                marginBottom: '8px',
                gap: '8px'
            }}>
                <div style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    backgroundColor: getContractorColor(segment.contractor_name)
                }}></div>
                <strong style={{ color: '#1f2937', fontSize: '14px' }}>🛣️ Road Segment Details</strong>
            </div>

            <div style={{ fontSize: '12px', color: '#374151', lineHeight: '1.4' }}>
                <div style={{ marginBottom: '4px' }}>
                    <strong>👷 Contractor:</strong> {segment.contractor_name}
                </div>
                <div style={{ marginBottom: '4px' }}>
                    <strong>🆔 Contractor ID:</strong> {segment.contractor_id}
                </div>
                <div style={{ marginBottom: '4px' }}>
                    <strong>📧 Email:</strong> {segment.contractor_email}
                </div>
                <div style={{ marginBottom: '4px' }}>
                    <strong>📞 Phone:</strong> {segment.contractor_phone}
                </div>
                <div style={{ marginBottom: '4px' }}>
                    <strong>📅 Road Created:</strong> {new Date(segment.road_creation_date).toLocaleDateString('en-US', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric'
                    })}
                </div>
                <div style={{ marginBottom: '4px' }}>
                    <strong>🛡️ Warranty:</strong> {segment.warranty_period} months
                </div>
                <div style={{ marginBottom: '4px' }}>
                    <strong>💰 Money Sanctioned:</strong> ₹{segment.money_sanctioned?.toLocaleString('en-IN') || 'N/A'}
                </div>
                {segment.created_by && (
                    <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #d1d5db' }}>
                        <div style={{ fontSize: '11px', color: '#6b7280' }}>
                            <strong>Created by:</strong> {segment.created_by.full_name} ({segment.created_by.department || 'No Department'})
                        </div>
                    </div>
                )}
            </div>
        </div>
    );

    // Filter potholes based on current filters
    const filteredPotholes = potholes.filter(pothole => {
        // Status filter
        if (statusFilter !== 'all' && pothole.status !== statusFilter) {
            return false;
        }

        // Severity filter
        if (severityFilter !== 'all' && pothole.severity !== severityFilter) {
            return false;
        }

        // Date range filter - only apply if explicitly set
        if (dateRange && dateRange.start && dateRange.end) {
            const potholeDate = new Date(pothole.timestamp);
            if (potholeDate < dateRange.start || potholeDate > dateRange.end) {
                return false;
            }
        }

        return true;
    });

    if (error) {
        return <ErrorDisplay error={error} onRetry={() => window.location.reload()} />;
    }

    return (
        <>
            <MarkerClusterGroup
                chunkedLoading
                spiderfyOnMaxZoom={true}
                showCoverageOnHover={false}
                zoomToBoundsOnClick={true}
                maxClusterRadius={50}
                iconCreateFunction={createCustomClusterIcon}
            >
                {filteredPotholes.map((pothole) => (
                    <Marker
                        key={pothole.id}
                        position={[parseFloat(pothole.latitude), parseFloat(pothole.longitude)]}
                        icon={createPotholeIcon(pothole.severity, pothole.status)}
                        eventHandlers={{
                            click: () => handlePotholeClick(pothole),
                        }}
                    >
                        <Popup maxWidth={400} minWidth={300} className="pothole-popup">
                            <div className="pothole-popup-content">
                                <div className="pothole-header">
                                    <h4>🕳️ Pothole Report #{pothole.id}</h4>
                                    <div className="pothole-badges">
                                        <span
                                            className="severity-badge"
                                            style={{ backgroundColor: getSeverityColor(pothole.severity) }}
                                        >
                                            {getSeverityLabel(pothole.severity)} Severity
                                        </span>
                                        <span
                                            className="status-badge"
                                            style={{ backgroundColor: getStatusColor(pothole.status) }}
                                        >
                                            {getStatusLabel(pothole.status)}
                                        </span>
                                    </div>
                                </div>

                                <div className="pothole-details">
                                    <div className="detail-row">
                                        <strong>📍 Location:</strong>
                                        <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                                            {pothole.location_string}
                                        </div>
                                    </div>
                                    <div className="detail-row">
                                        <strong>🕳️ Count:</strong>
                                        <span style={{
                                            background: '#fee2e2',
                                            color: '#991b1b',
                                            padding: '2px 6px',
                                            borderRadius: '4px',
                                            marginLeft: '8px',
                                            fontSize: '12px',
                                            fontWeight: 'bold'
                                        }}>
                                            {pothole.num_potholes} pothole{pothole.num_potholes > 1 ? 's' : ''}
                                        </span>
                                    </div>
                                    <div className="detail-row">
                                        <strong>📅 Reported:</strong>
                                        <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                                            {formatDate(pothole.timestamp)}
                                        </div>
                                    </div>
                                    {pothole.description && (
                                        <div className="detail-row">
                                            <strong>📝 Description:</strong>
                                            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px', fontStyle: 'italic' }}>
                                                {pothole.description}
                                            </div>
                                        </div>
                                    )}
                                    {pothole.road_c_date && (
                                        <div className="detail-row">
                                            <strong>🛣️ Road Creation Date:</strong>
                                            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                                                {new Date(pothole.road_c_date).toLocaleDateString('en-US', {
                                                    year: 'numeric',
                                                    month: 'long',
                                                    day: 'numeric'
                                                })}
                                            </div>
                                        </div>
                                    )}
                                    {pothole.contractor && (
                                        <div className="detail-row">
                                            <strong>👷 Contractor:</strong>
                                            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px', fontWeight: '500' }}>
                                                {pothole.contractor}
                                            </div>
                                        </div>
                                    )}
                                    {pothole.image && (
                                        <div className="detail-row">
                                            <strong>📸 Uploaded Image:</strong>
                                            <img
                                                src={pothole.image}
                                                alt="Pothole"
                                                style={{
                                                    maxWidth: '100%',
                                                    marginTop: '8px',
                                                    borderRadius: '8px',
                                                    border: '1px solid #e5e7eb',
                                                    cursor: 'pointer'
                                                }}
                                                onClick={() => pothole.image && window.open(pothole.image, '_blank')}
                                                title="Click to view full size"
                                            />
                                        </div>
                                    )}

                                    {/* Frame Image Section - Load on demand for potholes with frame data */}
                                    {pothole.frame_number && (
                                        <div className="detail-row">
                                            <strong>🎥 Frame Image:</strong>
                                            <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px', marginBottom: '8px' }}>
                                                {pothole.frame_number ? `Frame #${pothole.frame_number}` : 'Frame Image Available'}
                                            </div>

                                            {frameImages[pothole.id] ? (
                                                <img
                                                    src={`data:image/jpeg;base64,${frameImages[pothole.id].frame_image_base64}`}
                                                    alt={`Pothole Frame ${pothole.frame_number}`}
                                                    style={{
                                                        width: '100%',
                                                        height: 'auto',
                                                        maxHeight: 'none', // Remove height constraint
                                                        objectFit: 'contain',
                                                        marginTop: '8px',
                                                        borderRadius: '8px',
                                                        border: '2px solid #3b82f6',
                                                        cursor: 'pointer',
                                                        boxShadow: '0 2px 8px rgba(59, 130, 246, 0.2)',
                                                        display: 'block'
                                                    }}
                                                    onClick={() => {
                                                        const imgWindow = window.open('', '_blank');
                                                        if (imgWindow) {
                                                            imgWindow.document.write(`
                                                                <html>
                                                                    <head><title>Pothole Frame ${pothole.frame_number}</title></head>
                                                                    <body style="margin:0;background:#000;display:flex;justify-content:center;align-items:center;min-height:100vh;">
                                                                        <img src="data:image/jpeg;base64,${frameImages[pothole.id].frame_image_base64}" style="max-width:100%;max-height:100%;object-fit:contain;" alt="Pothole Frame" />
                                                                    </body>
                                                                </html>
                                                            `);
                                                        }
                                                    }}
                                                    title="Click to view full size frame image"
                                                />
                                            ) : loadingFrames.has(pothole.id) ? (
                                                <div style={{
                                                    padding: '20px',
                                                    textAlign: 'center',
                                                    backgroundColor: '#f8fafc',
                                                    borderRadius: '8px',
                                                    border: '1px solid #e2e8f0',
                                                    marginTop: '8px'
                                                }}>
                                                    Loading frame image...
                                                </div>
                                            ) : (
                                                <button
                                                    style={{
                                                        width: '100%',
                                                        padding: '12px',
                                                        backgroundColor: '#3b82f6',
                                                        color: 'white',
                                                        border: 'none',
                                                        borderRadius: '8px',
                                                        cursor: 'pointer',
                                                        fontSize: '14px',
                                                        fontWeight: '500',
                                                        marginTop: '8px'
                                                    }}
                                                    onClick={(e) => loadFrameImage(pothole.id, e)}
                                                >
                                                    📷 Load Frame Image
                                                </button>
                                            )}
                                        </div>
                                    )}

                                    {/* Action buttons */}
                                    <div style={{
                                        marginTop: '12px',
                                        paddingTop: '12px',
                                        borderTop: '1px solid #e5e7eb',
                                        display: 'flex',
                                        gap: '8px',
                                        fontSize: '12px'
                                    }}>
                                        <button
                                            style={{
                                                background: '#3b82f6',
                                                color: 'white',
                                                border: 'none',
                                                padding: '6px 12px',
                                                borderRadius: '6px',
                                                cursor: 'pointer',
                                                fontSize: '11px'
                                            }}
                                            onClick={() => window.open(`https://www.google.com/maps?q=${pothole.latitude},${pothole.longitude}`, '_blank')}
                                        >
                                            📍 View in Google Maps
                                        </button>
                                        <button
                                            style={{
                                                background: '#6b7280',
                                                color: 'white',
                                                border: 'none',
                                                padding: '6px 12px',
                                                borderRadius: '6px',
                                                cursor: 'pointer',
                                                fontSize: '11px'
                                            }}
                                            onClick={() => navigator.clipboard?.writeText(`${pothole.latitude}, ${pothole.longitude}`)}
                                        >
                                            📋 Copy Coordinates
                                        </button>

                                        {/* Road Segment Button - Only show if a segment is found for this pothole */}
                                        {highlightedPotholeId === pothole.id && selectedRoadSegment && (
                                            <button
                                                style={{
                                                    background: getContractorColor(selectedRoadSegment.contractor_name),
                                                    color: 'white',
                                                    border: 'none',
                                                    padding: '6px 12px',
                                                    borderRadius: '6px',
                                                    cursor: 'pointer',
                                                    fontSize: '11px',
                                                    flex: '1'
                                                }}
                                                onClick={() => {
                                                    // Toggle showing road segment details in popup
                                                    const existingDetails = document.querySelector('.road-segment-details');
                                                    if (existingDetails) {
                                                        existingDetails.remove();
                                                    } else {
                                                        // This will be handled by the RoadSegmentDetails component below
                                                    }
                                                }}
                                            >
                                                🛣️ Road Details
                                            </button>
                                        )}
                                    </div>

                                    {/* Road Segment Details - Show when available and selected */}
                                    {highlightedPotholeId === pothole.id && selectedRoadSegment && (
                                        <RoadSegmentDetails segment={selectedRoadSegment} />
                                    )}
                                </div>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MarkerClusterGroup>

            {/* Highlight selected road segment */}
            {selectedRoadSegment && (
                <Polyline
                    positions={selectedRoadSegment.points}
                    color={getContractorColor(selectedRoadSegment.contractor_name)}
                    weight={6}
                    opacity={0.8}
                    dashArray="10, 5"
                />
            )}

            {loading && (
                <div className="pothole-loading-indicator">
                    <LoadingSpinner size="sm" />
                    <span>Loading potholes...</span>
                </div>
            )}
        </>
    );
};
