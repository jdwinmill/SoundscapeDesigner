import { useRef, useState, useEffect } from 'react';
import BpmAxis from './BpmAxis';
import StemBand from './StemBand';
import { AXIS_HEIGHT, LANE_HEIGHT, LANE_GAP, bpmToPixel, pixelToBpm, BPM_MIN, BPM_MAX } from './constants';

/**
 * The main SVG canvas for the Soundscape Designer.
 */
export default function DesignerCanvas({
    lanes,
    selectedLaneId,
    scrubBpm,
    onSelectLane,
    onUpdateLane,
    onScrubBpmChange,
    dispatch,
    onWidthChange,
}) {
    const containerRef = useRef(null);
    const svgRef = useRef(null);
    const [canvasWidth, setCanvasWidth] = useState(800);
    const scrubDragRef = useRef(false);

    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        const observer = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const w = entry.contentRect.width;
                setCanvasWidth(w);
                onWidthChange?.(w);
            }
        });
        observer.observe(el);
        return () => observer.disconnect();
    }, []);

    const totalHeight = AXIS_HEIGHT + Math.max(lanes.length, 1) * (LANE_HEIGHT + LANE_GAP) + LANE_GAP;
    const minHeight = Math.max(totalHeight, 200);

    const scrubX = bpmToPixel(scrubBpm, canvasWidth);

    function getSvgX(e) {
        const svg = svgRef.current;
        if (!svg) return 0;
        const rect = svg.getBoundingClientRect();
        return e.clientX - rect.left;
    }

    function clampScrubBpm(x) {
        const bpm = pixelToBpm(x, canvasWidth);
        return Math.round(Math.max(BPM_MIN, Math.min(BPM_MAX, bpm)));
    }

    function handleScrubPointerDown(e) {
        e.stopPropagation();
        e.currentTarget.setPointerCapture(e.pointerId);
        scrubDragRef.current = true;
        onScrubBpmChange(clampScrubBpm(getSvgX(e)));
    }

    function handleScrubPointerMove(e) {
        if (!scrubDragRef.current) return;
        onScrubBpmChange(clampScrubBpm(getSvgX(e)));
    }

    function handleScrubPointerUp() {
        scrubDragRef.current = false;
    }

    // Deselect is handled by the background rect's onClick directly

    return (
        <div
            ref={containerRef}
            className="w-full bg-bg-secondary rounded-2xl border border-border-subtle"
        >
            <svg
                ref={svgRef}
                width={canvasWidth}
                height={minHeight}
                className="block select-none"
                style={{ minHeight: '200px' }}
            >
                <defs>
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="4" result="blur" />
                        <feMerge>
                            <feMergeNode in="blur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>

                {/* Canvas background — click to deselect */}
                <rect
                    x={0}
                    y={0}
                    width={canvasWidth}
                    height={minHeight}
                    fill="transparent"
                    onClick={() => onSelectLane(null)}
                />

                {/* Background grid lines */}
                {Array.from({ length: 10 }, (_, i) => {
                    const bpm = 60 + i * 20;
                    const x = bpmToPixel(bpm, canvasWidth);
                    return (
                        <line
                            key={`grid-${bpm}`}
                            x1={x}
                            y1={AXIS_HEIGHT}
                            x2={x}
                            y2={minHeight}
                            stroke="var(--color-border-subtle)"
                            strokeWidth={0.5}
                            opacity={0.3}
                            pointerEvents="none"
                        />
                    );
                })}

                {/* BPM Axis */}
                <BpmAxis width={canvasWidth} height={AXIS_HEIGHT} />

                {/* Stem bands */}
                {lanes.map((lane, index) => {
                    const yOffset = AXIS_HEIGHT + LANE_GAP + index * (LANE_HEIGHT + LANE_GAP);
                    return (
                        <StemBand
                            key={lane.id}
                            lane={lane}
                            yOffset={yOffset}
                            canvasWidth={canvasWidth}
                            isSelected={lane.id === selectedLaneId}
                            onSelect={onSelectLane}
                            onUpdate={onUpdateLane}
                            dispatch={dispatch}
                        />
                    );
                })}

                {/* BPM Scrubber line (visual only, no pointer events) */}
                <line
                    x1={scrubX}
                    y1={0}
                    x2={scrubX}
                    y2={minHeight}
                    stroke="var(--color-highlight-amber)"
                    strokeWidth={2}
                    opacity={0.7}
                    pointerEvents="none"
                />

                {/* Scrubber drag handle — only the triangle + small hit area, not full height */}
                <g
                    style={{ cursor: 'ew-resize' }}
                    onPointerDown={handleScrubPointerDown}
                    onPointerMove={handleScrubPointerMove}
                    onPointerUp={handleScrubPointerUp}
                >
                    {/* Hit area: just the handle zone at the top */}
                    <rect
                        x={scrubX - 16}
                        y={0}
                        width={32}
                        height={AXIS_HEIGHT + 10}
                        fill="transparent"
                    />
                    {/* Visible triangle handle */}
                    <polygon
                        points={`${scrubX - 7},${AXIS_HEIGHT - 4} ${scrubX + 7},${AXIS_HEIGHT - 4} ${scrubX},${AXIS_HEIGHT + 6}`}
                        fill="var(--color-highlight-amber)"
                    />
                    {/* BPM label */}
                    <text
                        x={scrubX}
                        y={AXIS_HEIGHT - 10}
                        textAnchor="middle"
                        fill="var(--color-highlight-amber)"
                        fontSize={10}
                        fontFamily="var(--font-body)"
                        fontWeight={600}
                        pointerEvents="none"
                    >
                        {Math.round(scrubBpm)}
                    </text>
                </g>

                {/* Empty state */}
                {lanes.length === 0 && (
                    <text
                        x={canvasWidth / 2}
                        y={minHeight / 2 + 10}
                        textAnchor="middle"
                        fill="var(--color-text-muted)"
                        fontSize={14}
                        fontFamily="var(--font-body)"
                        pointerEvents="none"
                    >
                        Add stems to start designing your soundscape
                    </text>
                )}
            </svg>
        </div>
    );
}
