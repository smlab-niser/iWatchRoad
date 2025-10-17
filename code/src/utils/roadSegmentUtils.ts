import type { RoadSegment } from '../types';

/**
 * Calculate the distance from a point to a line segment
 * @param point - [lat, lng] of the point
 * @param lineStart - [lat, lng] of line segment start
 * @param lineEnd - [lat, lng] of line segment end
 * @returns distance in meters (approximately)
 */
export const pointToLineDistance = (
    point: [number, number],
    lineStart: [number, number],
    lineEnd: [number, number]
): number => {
    const [px, py] = point;
    const [x1, y1] = lineStart;
    const [x2, y2] = lineEnd;

    // Calculate the squared length of the line segment
    const A = px - x1;
    const B = py - y1;
    const C = x2 - x1;
    const D = y2 - y1;

    const dot = A * C + B * D;
    const lenSq = C * C + D * D;

    let param = -1;
    if (lenSq !== 0) {
        param = dot / lenSq;
    }

    let xx, yy;

    if (param < 0) {
        xx = x1;
        yy = y1;
    } else if (param > 1) {
        xx = x2;
        yy = y2;
    } else {
        xx = x1 + param * C;
        yy = y1 + param * D;
    }

    const dx = px - xx;
    const dy = py - yy;

    // Convert to approximate meters (rough estimation)
    // 1 degree ≈ 111,000 meters at equator
    const latDistance = dx * 111000;
    const lngDistance = dy * 111000 * Math.cos(px * Math.PI / 180);

    return Math.sqrt(latDistance * latDistance + lngDistance * lngDistance);
};

/**
 * Find road segments that contain or are near a given point
 * @param point - [lat, lng] of the pothole
 * @param roadSegments - Array of road segments to check
 * @param tolerance - Maximum distance in meters to consider "on road" (default: 50m)
 * @returns Array of road segments that the point is near
 */
export const findRoadSegmentsNearPoint = (
    point: [number, number],
    roadSegments: RoadSegment[],
    tolerance: number = 50
): RoadSegment[] => {
    const nearbySegments: RoadSegment[] = [];

    for (const segment of roadSegments) {
        if (!segment.points || segment.points.length < 2) {
            continue; // Skip invalid segments
        }

        let isNearSegment = false;

        // Check distance to each line segment in the polyline
        for (let i = 0; i < segment.points.length - 1; i++) {
            const distance = pointToLineDistance(
                point,
                segment.points[i],
                segment.points[i + 1]
            );

            if (distance <= tolerance) {
                isNearSegment = true;
                break;
            }
        }

        if (isNearSegment) {
            nearbySegments.push(segment);
        }
    }

    return nearbySegments;
};

/**
 * Get the closest road segment to a point
 * @param point - [lat, lng] of the pothole
 * @param roadSegments - Array of road segments to check
 * @returns The closest road segment or null if none found
 */
export const getClosestRoadSegment = (
    point: [number, number],
    roadSegments: RoadSegment[]
): { segment: RoadSegment; distance: number } | null => {
    let closestSegment: RoadSegment | null = null;
    let minDistance = Infinity;

    for (const segment of roadSegments) {
        if (!segment.points || segment.points.length < 2) {
            continue;
        }

        // Find minimum distance to this segment
        let segmentMinDistance = Infinity;
        for (let i = 0; i < segment.points.length - 1; i++) {
            const distance = pointToLineDistance(
                point,
                segment.points[i],
                segment.points[i + 1]
            );
            segmentMinDistance = Math.min(segmentMinDistance, distance);
        }

        if (segmentMinDistance < minDistance) {
            minDistance = segmentMinDistance;
            closestSegment = segment;
        }
    }

    return closestSegment ? { segment: closestSegment, distance: minDistance } : null;
};

/**
 * Generate consistent colors for contractor names
 * @param contractorName - Name of the contractor
 * @returns HSL color string
 */
export const getContractorColor = (contractorName: string): string => {
    let hash = 0;
    for (let i = 0; i < contractorName.length; i++) {
        hash = contractorName.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = Math.abs(hash) % 360;
    return `hsl(${hue}, 70%, 50%)`;
};
