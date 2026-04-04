/**
 * Shared constants for the Designer canvas components.
 */

export const BPM_MIN = 60;
export const BPM_MAX = 240;
export const BPM_RANGE = BPM_MAX - BPM_MIN;

export const AXIS_HEIGHT = 40;
export const LANE_HEIGHT = 80;
export const LANE_GAP = 8;
export const LANE_PADDING = 4;

/**
 * Convert BPM to pixel x-coordinate within the canvas.
 */
export function bpmToPixel(bpm, canvasWidth) {
    return ((bpm - BPM_MIN) / BPM_RANGE) * canvasWidth;
}

/**
 * Convert pixel x-coordinate to BPM.
 */
export function pixelToBpm(x, canvasWidth) {
    return BPM_MIN + (x / canvasWidth) * BPM_RANGE;
}
