/**
 * Stem Color Palette — Assigns distinct colors to stem lanes.
 *
 * Colors are chosen to be visually distinct on a dark background,
 * harmonize with the teal-to-violet accent system, and remain
 * readable at varying opacity levels.
 */

const PALETTE = [
    { fill: '#00d4aa', stroke: '#00b894', label: 'Teal' },
    { fill: '#7c3aed', stroke: '#6d28d9', label: 'Violet' },
    { fill: '#f59e0b', stroke: '#d97706', label: 'Amber' },
    { fill: '#3b82f6', stroke: '#2563eb', label: 'Blue' },
    { fill: '#ef4444', stroke: '#dc2626', label: 'Red' },
    { fill: '#10b981', stroke: '#059669', label: 'Emerald' },
    { fill: '#ec4899', stroke: '#db2777', label: 'Pink' },
    { fill: '#8b5cf6', stroke: '#7c3aed', label: 'Purple' },
    { fill: '#06b6d4', stroke: '#0891b2', label: 'Cyan' },
    { fill: '#f97316', stroke: '#ea580c', label: 'Orange' },
    { fill: '#84cc16', stroke: '#65a30d', label: 'Lime' },
    { fill: '#e879f9', stroke: '#d946ef', label: 'Fuchsia' },
];

/**
 * Get a color from the palette by index, cycling if needed.
 * @param {number} index
 * @returns {{ fill: string, stroke: string, label: string }}
 */
export function getColor(index) {
    return PALETTE[index % PALETTE.length];
}

/**
 * Get the fill color with a specific opacity (for SVG fill).
 * @param {number} index
 * @param {number} opacity - 0 to 1
 * @returns {string} rgba color string
 */
export function getFillWithOpacity(index, opacity = 0.3) {
    const color = PALETTE[index % PALETTE.length];
    return hexToRgba(color.fill, opacity);
}

/**
 * Get the stroke color for a lane.
 * @param {number} index
 * @returns {string} hex color
 */
export function getStroke(index) {
    return PALETTE[index % PALETTE.length].stroke;
}

function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

export { PALETTE };
