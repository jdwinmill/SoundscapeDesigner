import { useMemo, useState } from 'react';
import { bpmToPixel, LANE_HEIGHT, LANE_PADDING } from './constants';
import { getFillWithOpacity, getStroke, getColor } from '../../lib/stemColors';
import StemBandHandles from './StemBandHandles';

/**
 * Renders a single stem lane as a trapezoidal SVG shape with interactive handles.
 */
export default function StemBand({
    lane,
    yOffset,
    canvasWidth,
    isSelected,
    onSelect,
    onUpdate,
    dispatch,
}) {
    const { bpmRange, fadeIn, fadeOut, volume, colorIndex, muted, stemName } = lane;
    const [bpmLow, bpmHigh] = bpmRange;
    const [hovered, setHovered] = useState(false);

    const path = useMemo(() => {
        const a = bpmToPixel(bpmLow - fadeIn, canvasWidth);
        const b = bpmToPixel(bpmLow, canvasWidth);
        const c = bpmToPixel(bpmHigh, canvasWidth);
        const d = bpmToPixel(bpmHigh + fadeOut, canvasWidth);

        const top = yOffset + LANE_PADDING + (1 - volume) * (LANE_HEIGHT - LANE_PADDING * 2);
        const bottom = yOffset + LANE_HEIGHT - LANE_PADDING;

        return [
            `M ${a} ${bottom}`,
            `L ${b} ${top}`,
            `L ${c} ${top}`,
            `L ${d} ${bottom}`,
            'Z',
        ].join(' ');
    }, [bpmLow, bpmHigh, fadeIn, fadeOut, volume, yOffset, canvasWidth]);

    const fillOpacity = muted ? 0.1 : 0.3;
    const strokeOpacity = muted ? 0.2 : isSelected ? 0.9 : hovered ? 0.7 : 0.5;
    const color = getColor(colorIndex);

    // Label position: center of the flat top
    const labelX = bpmToPixel((bpmLow + bpmHigh) / 2, canvasWidth);
    const labelY = yOffset + LANE_PADDING + (1 - volume) * (LANE_HEIGHT - LANE_PADDING * 2) - 14;

    return (
        <g
            className="stem-band"
            onPointerEnter={() => setHovered(true)}
            onPointerLeave={() => setHovered(false)}
        >
            {/* Lane background (click to select) */}
            <rect
                x={0}
                y={yOffset}
                width={canvasWidth}
                height={LANE_HEIGHT}
                fill="transparent"
                style={{ cursor: 'pointer' }}
                onClick={(e) => { e.stopPropagation(); onSelect(lane.id); }}
            />

            {/* Selection highlight glow */}
            {isSelected && (
                <path
                    d={path}
                    fill="none"
                    stroke={color.fill}
                    strokeWidth={3}
                    opacity={0.3}
                    filter="url(#glow)"
                    pointerEvents="none"
                />
            )}

            {/* Trapezoid fill */}
            <path
                d={path}
                fill={getFillWithOpacity(colorIndex, fillOpacity)}
                stroke={getStroke(colorIndex)}
                strokeWidth={isSelected ? 2 : 1}
                opacity={strokeOpacity}
                style={{ cursor: 'pointer' }}
                onClick={(e) => { e.stopPropagation(); onSelect(lane.id); }}
            />

            {/* Stem name label */}
            <text
                x={labelX}
                y={labelY}
                textAnchor="middle"
                fill={color.fill}
                fontSize={11}
                fontFamily="var(--font-heading)"
                fontWeight={600}
                opacity={muted ? 0.3 : 0.8}
                pointerEvents="none"
            >
                {stemName}
            </text>

            {/* Drag handles (visible on hover or selection) */}
            <StemBandHandles
                lane={lane}
                yOffset={yOffset}
                canvasWidth={canvasWidth}
                isSelected={isSelected}
                isHovered={hovered}
                dispatch={dispatch}
            />
        </g>
    );
}
