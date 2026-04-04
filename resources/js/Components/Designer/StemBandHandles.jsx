import { bpmToPixel, LANE_HEIGHT, LANE_PADDING, BPM_MIN, BPM_MAX } from './constants';

const HANDLE_RADIUS = 6;
const MIN_BPM_GAP = 2;
const MIN_FADE = 0;
const MAX_FADE = 40;
const VOLUME_HIT_HEIGHT = 12; // Wider hit area for volume drag

/**
 * Renders interactive drag handles on a stem band.
 *
 * Uses DRAG_START on pointerDown (one undo entry) and
 * DRAG_UPDATE_LANE on pointerMove (no undo entries).
 */
export default function StemBandHandles({
    lane,
    yOffset,
    canvasWidth,
    isSelected,
    isHovered,
    dispatch,
}) {
    const { id, bpmRange, fadeIn, fadeOut, volume } = lane;
    const [bpmLow, bpmHigh] = bpmRange;

    const visible = isSelected || isHovered;
    if (!visible) return null;

    // Clamp fade tip positions to visible canvas range
    const rawA = bpmLow - fadeIn;
    const rawD = bpmHigh + fadeOut;
    const aPixel = Math.max(0, bpmToPixel(rawA, canvasWidth));
    const bPixel = bpmToPixel(bpmLow, canvasWidth);
    const cPixel = bpmToPixel(bpmHigh, canvasWidth);
    const dPixel = Math.min(canvasWidth, bpmToPixel(rawD, canvasWidth));

    const top = yOffset + LANE_PADDING + (1 - volume) * (LANE_HEIGHT - LANE_PADDING * 2);
    const bottom = yOffset + LANE_HEIGHT - LANE_PADDING;

    function clampBpm(bpm) {
        return Math.max(BPM_MIN, Math.min(BPM_MAX, Math.round(bpm)));
    }

    function clampVolume(vol) {
        return Math.max(0.05, Math.min(1.0, Math.round(vol * 100) / 100));
    }

    function startDrag(e, mode) {
        e.stopPropagation();
        const target = e.currentTarget;
        target.setPointerCapture(e.pointerId);

        // Push one undo entry at the start of the drag
        dispatch({ type: 'DRAG_START' });

        const startX = e.clientX;
        const startY = e.clientY;
        const startBpmLow = bpmLow;
        const startBpmHigh = bpmHigh;
        const startFadeIn = fadeIn;
        const startFadeOut = fadeOut;
        const startVolume = volume;

        function onMove(moveEvt) {
            const dx = moveEvt.clientX - startX;
            const dy = moveEvt.clientY - startY;
            const dBpm = (dx / canvasWidth) * (BPM_MAX - BPM_MIN);

            let changes = null;

            switch (mode) {
                case 'move': {
                    const shift = Math.round(dBpm);
                    const newLow = clampBpm(startBpmLow + shift);
                    const newHigh = newLow + (startBpmHigh - startBpmLow);
                    if (newHigh <= BPM_MAX && newLow >= BPM_MIN) {
                        changes = { bpmRange: [newLow, newHigh] };
                    }
                    break;
                }
                case 'left-edge': {
                    const newLow = clampBpm(startBpmLow + dBpm);
                    if (newLow < startBpmHigh - MIN_BPM_GAP) {
                        changes = { bpmRange: [newLow, startBpmHigh] };
                    }
                    break;
                }
                case 'right-edge': {
                    const newHigh = clampBpm(startBpmHigh + dBpm);
                    if (newHigh > startBpmLow + MIN_BPM_GAP) {
                        changes = { bpmRange: [startBpmLow, newHigh] };
                    }
                    break;
                }
                case 'fade-in': {
                    const newFade = Math.max(MIN_FADE, Math.min(MAX_FADE, Math.round(startFadeIn - dBpm)));
                    changes = { fadeIn: newFade };
                    break;
                }
                case 'fade-out': {
                    const newFade = Math.max(MIN_FADE, Math.min(MAX_FADE, Math.round(startFadeOut + dBpm)));
                    changes = { fadeOut: newFade };
                    break;
                }
                case 'volume': {
                    const laneInnerHeight = LANE_HEIGHT - LANE_PADDING * 2;
                    const dVol = -dy / laneInnerHeight;
                    changes = { volume: clampVolume(startVolume + dVol) };
                    break;
                }
            }

            if (changes) {
                dispatch({ type: 'DRAG_UPDATE_LANE', payload: { id, changes } });
            }
        }

        function onUp() {
            target.removeEventListener('pointermove', onMove);
            target.removeEventListener('pointerup', onUp);
        }

        target.addEventListener('pointermove', onMove);
        target.addEventListener('pointerup', onUp);
    }

    const handleFill = isSelected ? 'var(--color-accent-teal)' : 'var(--color-text-muted)';
    const handleFillFade = isSelected ? 'var(--color-highlight-amber)' : 'var(--color-text-muted)';

    return (
        <g className="stem-band-handles">
            {/* Center move zone (the flat top area) */}
            <rect
                x={bPixel}
                y={top}
                width={Math.max(cPixel - bPixel, 4)}
                height={Math.max(bottom - top, 4)}
                fill="transparent"
                style={{ cursor: 'grab' }}
                onPointerDown={(e) => startDrag(e, 'move')}
            />

            {/* Volume drag zone (wider invisible hit area on top edge) */}
            <rect
                x={bPixel + 4}
                y={top - VOLUME_HIT_HEIGHT / 2}
                width={Math.max(cPixel - bPixel - 8, 4)}
                height={VOLUME_HIT_HEIGHT}
                fill="transparent"
                style={{ cursor: 'ns-resize' }}
                onPointerDown={(e) => startDrag(e, 'volume')}
            />

            {/* Volume visual indicator (thin line) */}
            <line
                x1={bPixel + 4}
                y1={top}
                x2={cPixel - 4}
                y2={top}
                stroke={handleFill}
                strokeWidth={2}
                opacity={0.5}
                pointerEvents="none"
            />

            {/* Left edge handle (B) — resize bpmLow */}
            <circle
                cx={bPixel}
                cy={(top + bottom) / 2}
                r={HANDLE_RADIUS}
                fill={handleFill}
                opacity={0.8}
                style={{ cursor: 'ew-resize' }}
                onPointerDown={(e) => startDrag(e, 'left-edge')}
            />

            {/* Right edge handle (C) — resize bpmHigh */}
            <circle
                cx={cPixel}
                cy={(top + bottom) / 2}
                r={HANDLE_RADIUS}
                fill={handleFill}
                opacity={0.8}
                style={{ cursor: 'ew-resize' }}
                onPointerDown={(e) => startDrag(e, 'right-edge')}
            />

            {/* Fade-in tip handle (A) — clamped to canvas */}
            <polygon
                points={`${aPixel},${bottom} ${aPixel - 5},${bottom + 5} ${aPixel + 5},${bottom + 5}`}
                fill={handleFillFade}
                opacity={0.8}
                style={{ cursor: 'ew-resize' }}
                onPointerDown={(e) => startDrag(e, 'fade-in')}
            />

            {/* Fade-out tip handle (D) — clamped to canvas */}
            <polygon
                points={`${dPixel},${bottom} ${dPixel - 5},${bottom + 5} ${dPixel + 5},${bottom + 5}`}
                fill={handleFillFade}
                opacity={0.8}
                style={{ cursor: 'ew-resize' }}
                onPointerDown={(e) => startDrag(e, 'fade-out')}
            />

            {/* Volume tooltip */}
            <text
                x={(bPixel + cPixel) / 2}
                y={top - 6}
                textAnchor="middle"
                fill="var(--color-text-secondary)"
                fontSize={10}
                fontFamily="var(--font-body)"
                pointerEvents="none"
                opacity={0.7}
            >
                {(volume * 100).toFixed(0)}%
            </text>
        </g>
    );
}
