/**
 * Curve Math — Pure functions for BPM-reactive volume and speed calculations.
 *
 * Volume: Trapezoidal curve with linear fade zones.
 * Speed: Piecewise-linear interpolation with endpoint clamping.
 */

/**
 * Compute volume at a single BPM value using the trapezoidal curve.
 *
 *   1.0  |        ___________
 *        |       /           \
 *   0.0  |_____/               \________
 *            A  B           C  D
 *
 *   A = bpmLow - fadeIn
 *   B = bpmLow
 *   C = bpmHigh
 *   D = bpmHigh + fadeOut
 */
export function volumeAtBpm(bpm, bpmLow, bpmHigh, fadeIn, fadeOut, volume, muted = false) {
    if (muted) return 0;

    const a = bpmLow - fadeIn;
    const b = bpmLow;
    const c = bpmHigh;
    const d = bpmHigh + fadeOut;

    let curve;

    if (bpm < a) {
        curve = 0;
    } else if (bpm < b) {
        curve = fadeIn === 0 ? 0 : (bpm - a) / (b - a);
    } else if (bpm <= c) {
        curve = 1;
    } else if (bpm < d) {
        curve = fadeOut === 0 ? 0 : 1 - (bpm - c) / (d - c);
    } else {
        curve = 0;
    }

    return curve * volume;
}

/**
 * Compute speed multiplier at a single BPM value using piecewise-linear interpolation.
 * Clamps to first/last point outside the defined range.
 *
 * @param {number} bpm
 * @param {[number, number][] | null} speedPoints - Array of [bpm, multiplier] pairs, sorted by BPM
 * @param {number} baseSpeed - Global speed multiplier
 * @returns {number} Effective speed
 */
export function speedAtBpm(bpm, speedPoints, baseSpeed = 1.0) {
    if (!speedPoints || speedPoints.length === 0) {
        return baseSpeed;
    }

    let curveVal;

    if (bpm <= speedPoints[0][0]) {
        curveVal = speedPoints[0][1];
    } else if (bpm >= speedPoints[speedPoints.length - 1][0]) {
        curveVal = speedPoints[speedPoints.length - 1][1];
    } else {
        for (let i = 0; i < speedPoints.length - 1; i++) {
            if (bpm >= speedPoints[i][0] && bpm <= speedPoints[i + 1][0]) {
                const t = (bpm - speedPoints[i][0]) / (speedPoints[i + 1][0] - speedPoints[i][0]);
                curveVal = speedPoints[i][1] + t * (speedPoints[i + 1][1] - speedPoints[i][1]);
                break;
            }
        }
    }

    return curveVal * baseSpeed;
}

/**
 * Generate path coordinates for rendering the trapezoidal volume shape as SVG.
 * Returns an array of {bpm, vol} points describing the trapezoid outline.
 */
export function volumeCurvePoints(bpmLow, bpmHigh, fadeIn, fadeOut, volume) {
    const a = bpmLow - fadeIn;
    const b = bpmLow;
    const c = bpmHigh;
    const d = bpmHigh + fadeOut;

    return [
        { bpm: a, vol: 0 },
        { bpm: b, vol: volume },
        { bpm: c, vol: volume },
        { bpm: d, vol: 0 },
    ];
}

/**
 * Generate an SVG path `d` string from volume curve points.
 * Maps BPM to x and volume to y within the given dimensions.
 *
 * @param {number} bpmLow
 * @param {number} bpmHigh
 * @param {number} fadeIn
 * @param {number} fadeOut
 * @param {number} volume - 0 to 1
 * @param {number} xOffset - Pixel offset for the lane's x start
 * @param {number} yOffset - Pixel offset for the lane's y start
 * @param {number} width - Available pixel width for BPM range 60-240
 * @param {number} laneHeight - Pixel height of the lane
 * @param {number} bpmMin - Default 60
 * @param {number} bpmMax - Default 240
 * @returns {string} SVG path d attribute
 */
export function volumeCurvePath(bpmLow, bpmHigh, fadeIn, fadeOut, volume, xOffset, yOffset, width, laneHeight, bpmMin = 60, bpmMax = 240) {
    const points = volumeCurvePoints(bpmLow, bpmHigh, fadeIn, fadeOut, volume);
    const bpmRange = bpmMax - bpmMin;

    function bpmToX(bpm) {
        return xOffset + ((bpm - bpmMin) / bpmRange) * width;
    }

    function volToY(vol) {
        return yOffset + laneHeight - (vol * laneHeight);
    }

    const baseline = yOffset + laneHeight;

    const d = [
        `M ${bpmToX(points[0].bpm)} ${baseline}`,
        `L ${bpmToX(points[0].bpm)} ${volToY(points[0].vol)}`,
        `L ${bpmToX(points[1].bpm)} ${volToY(points[1].vol)}`,
        `L ${bpmToX(points[2].bpm)} ${volToY(points[2].vol)}`,
        `L ${bpmToX(points[3].bpm)} ${volToY(points[3].vol)}`,
        `L ${bpmToX(points[3].bpm)} ${baseline}`,
        'Z',
    ].join(' ');

    return d;
}

/**
 * Generate polyline coordinates for a speed curve.
 *
 * @param {[number, number][]} speedPoints
 * @param {number} baseSpeed
 * @param {number} bpmMin
 * @param {number} bpmMax
 * @param {number} numSamples
 * @returns {{bpm: number, speed: number}[]}
 */
export function speedCurvePoints(speedPoints, baseSpeed = 1.0, bpmMin = 60, bpmMax = 240, numSamples = 100) {
    const points = [];
    const step = (bpmMax - bpmMin) / (numSamples - 1);

    for (let i = 0; i < numSamples; i++) {
        const bpm = bpmMin + i * step;
        points.push({ bpm, speed: speedAtBpm(bpm, speedPoints, baseSpeed) });
    }

    return points;
}

/**
 * Utility: convert BPM to pixel x-coordinate.
 */
export function bpmToPixel(bpm, width, bpmMin = 60, bpmMax = 240) {
    return ((bpm - bpmMin) / (bpmMax - bpmMin)) * width;
}

/**
 * Utility: convert pixel x-coordinate to BPM.
 */
export function pixelToBpm(x, width, bpmMin = 60, bpmMax = 240) {
    return bpmMin + (x / width) * (bpmMax - bpmMin);
}

/**
 * Clamp a value between min and max.
 */
export function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}
