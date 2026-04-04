import { bpmToPixel, BPM_MIN, BPM_MAX } from './constants';

const MAJOR_TICK_INTERVAL = 20;
const MINOR_TICK_INTERVAL = 10;

export default function BpmAxis({ width, height = 40 }) {
    const ticks = [];

    for (let bpm = BPM_MIN; bpm <= BPM_MAX; bpm += MINOR_TICK_INTERVAL) {
        const x = bpmToPixel(bpm, width);
        const isMajor = bpm % MAJOR_TICK_INTERVAL === 0;

        ticks.push(
            <g key={bpm}>
                <line
                    x1={x}
                    y1={isMajor ? 20 : 28}
                    x2={x}
                    y2={height}
                    stroke="var(--color-border-default)"
                    strokeWidth={isMajor ? 1 : 0.5}
                    opacity={isMajor ? 0.6 : 0.3}
                />
                {isMajor && (
                    <text
                        x={x}
                        y={16}
                        textAnchor="middle"
                        fill="var(--color-text-muted)"
                        fontSize={11}
                        fontFamily="var(--font-body)"
                    >
                        {bpm}
                    </text>
                )}
            </g>
        );
    }

    return <g className="bpm-axis">{ticks}</g>;
}
