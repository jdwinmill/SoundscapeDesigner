import { useState, useRef, useCallback } from 'react';
import { bpmToPixel, pixelToBpm, BPM_MIN, BPM_MAX } from './constants';
import { getColor } from '../../lib/stemColors';

const SPEED_MIN = 0.25;
const SPEED_MAX = 2.5;
const POINT_RADIUS = 7;
const EDITOR_HEIGHT = 160;
const PADDING_TOP = 24;
const PADDING_BOTTOM = 24;

function speedToY(speed, height) {
    const inner = height - PADDING_TOP - PADDING_BOTTOM;
    return PADDING_TOP + (1 - (speed - SPEED_MIN) / (SPEED_MAX - SPEED_MIN)) * inner;
}

function yToSpeed(y, height) {
    const inner = height - PADDING_TOP - PADDING_BOTTOM;
    const raw = SPEED_MIN + (1 - (y - PADDING_TOP) / inner) * (SPEED_MAX - SPEED_MIN);
    return Math.round(Math.max(SPEED_MIN, Math.min(SPEED_MAX, raw)) * 100) / 100;
}

/**
 * Inline piecewise-linear speed curve editor.
 * Renders as an SVG overlay with draggable control points.
 *
 * - Click on the line to add a new point
 * - Drag points to move them
 * - Double-click a point to remove it
 * - "Reset" clears back to flat
 */
export default function SpeedCurveEditor({ lane, canvasWidth, dispatch }) {
    const svgRef = useRef(null);
    const [draggingIdx, setDraggingIdx] = useState(null);
    const color = getColor(lane.colorIndex);

    const points = lane.speedCurve || [];
    const baseSpeed = lane.speed;

    function getSvgCoords(e) {
        const svg = svgRef.current;
        if (!svg) return { x: 0, y: 0 };
        const rect = svg.getBoundingClientRect();
        return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    }

    function updatePoints(newPoints) {
        const sorted = [...newPoints].sort((a, b) => a[0] - b[0]);
        dispatch({
            type: 'UPDATE_SPEED_CURVE',
            payload: { id: lane.id, speedCurve: sorted.length > 0 ? sorted : null },
        });
    }

    // Add point on click on the line area
    function handleBackgroundClick(e) {
        if (draggingIdx !== null) return;
        const { x, y } = getSvgCoords(e);
        const bpm = Math.round(pixelToBpm(x, canvasWidth));
        const speed = yToSpeed(y, EDITOR_HEIGHT);

        if (bpm < BPM_MIN || bpm > BPM_MAX) return;

        const newPoints = [...points, [bpm, speed]];
        updatePoints(newPoints);
    }

    // Drag a point
    function handlePointPointerDown(e, idx) {
        e.stopPropagation();
        const target = e.currentTarget;
        target.setPointerCapture(e.pointerId);

        dispatch({ type: 'DRAG_START' });
        setDraggingIdx(idx);

        function onMove(moveEvt) {
            const { x, y } = getSvgCoords(moveEvt);
            const bpm = Math.round(Math.max(BPM_MIN, Math.min(BPM_MAX, pixelToBpm(x, canvasWidth))));
            const speed = yToSpeed(y, EDITOR_HEIGHT);

            const newPoints = [...points];
            newPoints[idx] = [bpm, speed];
            const sorted = [...newPoints].sort((a, b) => a[0] - b[0]);
            dispatch({
                type: 'DRAG_UPDATE_LANE',
                payload: {
                    id: lane.id,
                    changes: { speedCurve: sorted },
                },
            });
        }

        function onUp() {
            setDraggingIdx(null);
            target.removeEventListener('pointermove', onMove);
            target.removeEventListener('pointerup', onUp);
        }

        target.addEventListener('pointermove', onMove);
        target.addEventListener('pointerup', onUp);
    }

    // Double-click to remove a point
    function handlePointDoubleClick(e, idx) {
        e.stopPropagation();
        const newPoints = points.filter((_, i) => i !== idx);
        updatePoints(newPoints);
    }

    function handleReset() {
        updatePoints([]);
    }

    // Build the polyline path
    const polylinePoints = points.length > 0
        ? points.map(([bpm, speed]) => `${bpmToPixel(bpm, canvasWidth)},${speedToY(speed, EDITOR_HEIGHT)}`).join(' ')
        : null;

    // Flat baseline (baseSpeed)
    const baselineY = speedToY(baseSpeed, EDITOR_HEIGHT);

    // Y-axis labels
    const speedLabels = [0.5, 1.0, 1.5, 2.0];

    return (
        <div className="mt-3 bg-bg-tertiary rounded-xl border border-border-subtle overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 border-b border-border-subtle">
                <span className="text-xs font-medium text-text-secondary">
                    Speed Curve
                    <span className="text-text-muted ml-2">Click to add points · Drag to move · Double-click to remove</span>
                </span>
                <button
                    onClick={handleReset}
                    className="text-xs text-text-muted hover:text-error transition-colors"
                >
                    Reset
                </button>
            </div>
            <svg
                ref={svgRef}
                width={canvasWidth}
                height={EDITOR_HEIGHT}
                className="block cursor-crosshair"
                onClick={handleBackgroundClick}
            >
                {/* Y-axis labels and grid */}
                {speedLabels.map((speed) => {
                    const y = speedToY(speed, EDITOR_HEIGHT);
                    return (
                        <g key={speed}>
                            <line
                                x1={0}
                                y1={y}
                                x2={canvasWidth}
                                y2={y}
                                stroke="var(--color-border-subtle)"
                                strokeWidth={0.5}
                                opacity={speed === 1.0 ? 0.6 : 0.3}
                                strokeDasharray={speed === 1.0 ? 'none' : '4 4'}
                            />
                            <text
                                x={8}
                                y={y - 4}
                                fill="var(--color-text-muted)"
                                fontSize={9}
                                fontFamily="var(--font-body)"
                            >
                                {speed}x
                            </text>
                        </g>
                    );
                })}

                {/* Baseline (flat speed when no points) */}
                <line
                    x1={0}
                    y1={baselineY}
                    x2={canvasWidth}
                    y2={baselineY}
                    stroke={color.fill}
                    strokeWidth={1}
                    opacity={0.2}
                    strokeDasharray="6 4"
                />

                {/* Speed curve polyline */}
                {polylinePoints && (
                    <polyline
                        points={polylinePoints}
                        fill="none"
                        stroke={color.fill}
                        strokeWidth={2}
                        opacity={0.8}
                    />
                )}

                {/* Control points */}
                {points.map(([bpm, speed], idx) => {
                    const cx = bpmToPixel(bpm, canvasWidth);
                    const cy = speedToY(speed, EDITOR_HEIGHT);
                    return (
                        <g key={idx}>
                            {/* Larger invisible hit area */}
                            <circle
                                cx={cx}
                                cy={cy}
                                r={POINT_RADIUS + 4}
                                fill="transparent"
                                style={{ cursor: 'grab' }}
                                onPointerDown={(e) => handlePointPointerDown(e, idx)}
                                onDoubleClick={(e) => handlePointDoubleClick(e, idx)}
                            />
                            {/* Visible point */}
                            <circle
                                cx={cx}
                                cy={cy}
                                r={POINT_RADIUS}
                                fill={color.fill}
                                stroke="var(--color-bg-primary)"
                                strokeWidth={2}
                                opacity={0.9}
                                pointerEvents="none"
                            />
                            {/* Value label */}
                            <text
                                x={cx}
                                y={cy - 12}
                                textAnchor="middle"
                                fill={color.fill}
                                fontSize={9}
                                fontFamily="var(--font-body)"
                                fontWeight={600}
                                pointerEvents="none"
                            >
                                {speed}x
                            </text>
                        </g>
                    );
                })}
            </svg>
        </div>
    );
}
