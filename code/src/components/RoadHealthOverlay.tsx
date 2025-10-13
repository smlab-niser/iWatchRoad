import React, { useState, useEffect } from 'react';
import { Polyline, Popup } from 'react-leaflet';
import type { RoadHealthData, ContractorMessage } from '../types';
import { roadHealthService } from '../services/roadHealthService';
import { LoadingSpinner } from './LoadingSpinner';
import { ErrorDisplay } from './ErrorDisplay';

interface RoadHealthOverlayProps {
    enabled: boolean;
    onMessageSent?: () => void;
}

export const RoadHealthOverlay: React.FC<RoadHealthOverlayProps> = ({
    enabled,
    onMessageSent
}) => {
    const [roadHealthData, setRoadHealthData] = useState<RoadHealthData[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedSegment, setSelectedSegment] = useState<RoadHealthData | null>(null);
    const [customMessage, setCustomMessage] = useState('');
    const [sendingMessage, setSendingMessage] = useState(false);
    const [messageHistory, setMessageHistory] = useState<ContractorMessage[]>([]);
    const [refreshing, setRefreshing] = useState(false);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    useEffect(() => {
        if (enabled) {
            loadRoadHealthData();
        }
    }, [enabled]);

    // Clear success message after 3 seconds
    useEffect(() => {
        if (successMessage) {
            const timer = setTimeout(() => {
                setSuccessMessage(null);
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [successMessage]);

    const loadRoadHealthData = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await roadHealthService.getRoadHealthData();
            setRoadHealthData(data);

            // If no data found, suggest refreshing from segments
            if (data.length === 0) {
                setError('No road health data found. Click "Refresh from Road Segments" to generate data from existing road segments.');
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load road health data');
        } finally {
            setLoading(false);
        }
    };

    const refreshFromSegments = async () => {
        setRefreshing(true);
        setError(null);
        try {
            const result = await roadHealthService.refreshFromSegments();
            console.log('Road health refreshed:', result);
            setSuccessMessage(`✅ ${result.message}`);
            await loadRoadHealthData(); // Reload the data
            onMessageSent?.(); // Notify parent component
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to refresh road health data');
        } finally {
            setRefreshing(false);
        }
    };

    const loadMessageHistory = async (segmentId: number) => {
        try {
            const messages = await roadHealthService.getContractorMessages(segmentId);
            setMessageHistory(messages);
        } catch (err) {
            console.error('Failed to load message history:', err);
        }
    };

    const sendCustomMessage = async () => {
        if (!selectedSegment || !customMessage.trim()) return;

        setSendingMessage(true);
        setError(null);

        try {
            const response = await roadHealthService.sendContractorMessage({
                segment_id: selectedSegment.segment_id!,
                message: customMessage,
                message_type: 'manual'
            });

            setCustomMessage('');
            await loadMessageHistory(selectedSegment.segment_id!);

            // Show detailed success message based on notification results
            if (response.notification_results) {
                const results = response.notification_results;
                let successParts = [];
                if (results.email?.success) successParts.push('email');
                if (results.sms?.success) successParts.push('SMS');

                if (successParts.length > 0) {
                    setSuccessMessage(`Message sent successfully via ${successParts.join(' and ')}!`);
                } else {
                    setError('Message saved but failed to send via email and SMS. Check contractor contact details.');
                }
            } else {
                setSuccessMessage('Message sent successfully!');
            }

            onMessageSent?.();
        } catch (err) {
            console.error('Failed to send message:', err);
            setError('Failed to send message. Please try again.');
        } finally {
            setSendingMessage(false);
        }
    };

    const getHealthStatusText = (status: RoadHealthData['health_status']): string => {
        const statusMap = {
            critical: 'Critical - Immediate attention required',
            warning: 'Warning - Repair needed',
            caution: 'Caution - Under warranty monitoring',
            good: 'Good - Well maintained'
        };
        return statusMap[status];
    };

    const getHealthIcon = (status: RoadHealthData['health_status']): string => {
        const iconMap = {
            critical: '🚨',
            warning: '⚠️',
            caution: '⚡',
            good: '✅'
        };
        return iconMap[status];
    };

    if (!enabled) return null;

    if (loading) {
        return (
            <div style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 1000 }}>
                <LoadingSpinner />
            </div>
        );
    }

    if (error) {
        return (
            <div style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 1000 }}>
                <ErrorDisplay error={error} onRetry={loadRoadHealthData} />
            </div>
        );
    }

    return (
        <>
            {/* Success Message */}
            {successMessage && (
                <div style={{
                    position: 'absolute',
                    top: '20px',
                    right: '20px',
                    background: '#16a34a',
                    color: 'white',
                    padding: '12px 16px',
                    borderRadius: '6px',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                    zIndex: 1001,
                    fontSize: '14px',
                    fontWeight: '500'
                }}>
                    {successMessage}
                </div>
            )}

            {/* Road Health Legend */}
            <div className="road-health-legend" style={{
                position: 'absolute',
                bottom: '100px',
                right: '20px',
                background: 'white',
                padding: '16px',
                borderRadius: '8px',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                zIndex: 1000,
                minWidth: '250px'
            }}>
                <h4 style={{ margin: '0 0 12px 0', fontWeight: '600' }}>🏥 Road Health Status</h4>

                {/* Refresh Button */}
                <button
                    onClick={refreshFromSegments}
                    disabled={refreshing || loading}
                    style={{
                        width: '100%',
                        padding: '8px 12px',
                        backgroundColor: '#16a34a',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: '600',
                        cursor: 'pointer',
                        marginBottom: '12px',
                        opacity: (refreshing || loading) ? 0.6 : 1
                    }}
                >
                    {refreshing ? 'Refreshing...' : '🔄 Refresh from Road Segments'}
                </button>

                <div style={{ fontSize: '12px', lineHeight: '1.6' }}>
                    <div style={{ display: 'flex', alignItems: 'center', margin: '4px 0' }}>
                        <div style={{ width: '16px', height: '4px', backgroundColor: '#dc2626', marginRight: '8px' }}></div>
                        <span>Critical ({'>'}200 potholes, warranty active)</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', margin: '4px 0' }}>
                        <div style={{ width: '16px', height: '4px', backgroundColor: '#ea580c', marginRight: '8px' }}></div>
                        <span>Warning ({'>'}200 potholes, no warranty)</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', margin: '4px 0' }}>
                        <div style={{ width: '16px', height: '4px', backgroundColor: '#eab308', marginRight: '8px' }}></div>
                        <span>Caution ({'<'}200 potholes, warranty active)</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', margin: '4px 0' }}>
                        <div style={{ width: '16px', height: '4px', backgroundColor: '#16a34a', marginRight: '8px' }}></div>
                        <span>Good ({'<'}200 potholes, no warranty)</span>
                    </div>

                    {roadHealthData.length > 0 && (
                        <div style={{
                            marginTop: '12px',
                            paddingTop: '8px',
                            borderTop: '1px solid #e5e7eb',
                            fontSize: '11px',
                            color: '#6b7280'
                        }}>
                            Total segments: {roadHealthData.length}
                        </div>
                    )}
                </div>
            </div>

            {/* Road Health Segments */}
            {roadHealthData.map((segment, index) => (
                <Polyline
                    key={`road-health-${index}`}
                    positions={segment.points}
                    color={roadHealthService.getRoadHealthColor(segment.health_status)}
                    weight={6}
                    opacity={0.8}
                    eventHandlers={{
                        click: () => {
                            setSelectedSegment(segment);
                            if (segment.segment_id) {
                                loadMessageHistory(segment.segment_id);
                            }
                        }
                    }}
                >
                    <Popup>
                        <div style={{ minWidth: '300px', fontFamily: 'inherit' }}>
                            <h3 style={{
                                color: '#1e293b',
                                fontSize: '16px',
                                fontWeight: '600',
                                marginBottom: '12px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                            }}>
                                {getHealthIcon(segment.health_status)} Road Health Report
                            </h3>

                            <div style={{ fontSize: '14px', lineHeight: '1.6', marginBottom: '16px' }}>
                                <div style={{ marginBottom: '8px' }}>
                                    <strong>Status:</strong> {getHealthStatusText(segment.health_status)}
                                </div>
                                <div style={{ marginBottom: '8px' }}>
                                    <strong>Pothole Count:</strong> {segment.pothole_count}
                                </div>
                                <div style={{ marginBottom: '8px' }}>
                                    <strong>Warranty Status:</strong> {segment.is_under_warranty ? 'Active' : 'Expired'}
                                </div>

                                {segment.contractor_info && (
                                    <>
                                        <div style={{ marginBottom: '8px' }}>
                                            <strong>Contractor:</strong> {segment.contractor_info.contractor_name}
                                        </div>
                                        <div style={{ marginBottom: '8px' }}>
                                            <strong>Contact:</strong> {segment.contractor_info.contractor_email}
                                        </div>
                                        <div style={{ marginBottom: '8px' }}>
                                            <strong>Phone:</strong> {segment.contractor_info.contractor_phone}
                                        </div>
                                    </>
                                )}
                            </div>

                            {/* Auto-message indicator */}
                            {roadHealthService.shouldTriggerAutoMessage(segment.health_status) && (
                                <div style={{
                                    backgroundColor: '#fef3c7',
                                    border: '1px solid #f59e0b',
                                    borderRadius: '6px',
                                    padding: '8px',
                                    marginBottom: '12px',
                                    fontSize: '12px'
                                }}>
                                    🤖 Auto-messages sent to contractor every 5 days
                                </div>
                            )}

                            {/* Custom message section */}
                            {segment.contractor_info && (
                                <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '12px' }}>
                                    <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Send Custom Message</h4>
                                    <textarea
                                        value={customMessage}
                                        onChange={(e) => setCustomMessage(e.target.value)}
                                        placeholder="Enter custom message..."
                                        style={{
                                            width: '100%',
                                            height: '60px',
                                            padding: '8px',
                                            border: '1px solid #d1d5db',
                                            borderRadius: '4px',
                                            fontSize: '12px',
                                            resize: 'vertical'
                                        }}
                                    />
                                    <button
                                        onClick={sendCustomMessage}
                                        disabled={!customMessage.trim() || sendingMessage}
                                        style={{
                                            marginTop: '8px',
                                            padding: '6px 12px',
                                            backgroundColor: '#3b82f6',
                                            color: 'white',
                                            border: 'none',
                                            borderRadius: '4px',
                                            fontSize: '12px',
                                            cursor: 'pointer',
                                            opacity: (!customMessage.trim() || sendingMessage) ? 0.5 : 1
                                        }}
                                    >
                                        {sendingMessage ? 'Sending...' : 'Send Message'}
                                    </button>
                                </div>
                            )}

                            {/* Message history */}
                            {messageHistory.length > 0 && (
                                <div style={{ marginTop: '12px', borderTop: '1px solid #e5e7eb', paddingTop: '12px' }}>
                                    <h4 style={{ fontSize: '14px', marginBottom: '8px' }}>Recent Messages</h4>
                                    <div style={{ maxHeight: '100px', overflowY: 'auto' }}>
                                        {messageHistory.slice(0, 3).map((msg, idx) => (
                                            <div key={idx} style={{
                                                fontSize: '11px',
                                                marginBottom: '6px',
                                                padding: '4px 8px',
                                                backgroundColor: msg.message_type === 'auto' ? '#f3f4f6' : '#eff6ff',
                                                borderRadius: '4px'
                                            }}>
                                                <div style={{ fontWeight: '500' }}>
                                                    {msg.message_type === 'auto' ? '🤖 Auto' : '👤 Manual'}
                                                </div>
                                                <div>{msg.message}</div>
                                                {msg.sent_at && (
                                                    <div style={{ color: '#6b7280', marginTop: '2px' }}>
                                                        {new Date(msg.sent_at).toLocaleDateString()}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </Popup>
                </Polyline>
            ))}
        </>
    );
};
