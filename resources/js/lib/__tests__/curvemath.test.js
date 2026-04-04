import { describe, it, expect } from 'vitest';
import {
    volumeAtBpm,
    speedAtBpm,
    volumeCurvePoints,
    volumeCurvePath,
    speedCurvePoints,
    bpmToPixel,
    pixelToBpm,
    clamp,
} from '../curvemath';

describe('volumeAtBpm', () => {
    const bpmLow = 120;
    const bpmHigh = 170;
    const fadeIn = 10;
    const fadeOut = 15;
    const volume = 0.8;

    it('returns 0 below the fade-in zone', () => {
        expect(volumeAtBpm(100, bpmLow, bpmHigh, fadeIn, fadeOut, volume)).toBe(0);
    });

    it('returns 0 above the fade-out zone', () => {
        expect(volumeAtBpm(200, bpmLow, bpmHigh, fadeIn, fadeOut, volume)).toBe(0);
    });

    it('returns full volume in the flat zone', () => {
        expect(volumeAtBpm(140, bpmLow, bpmHigh, fadeIn, fadeOut, volume)).toBe(volume);
    });

    it('returns full volume at bpmLow boundary', () => {
        expect(volumeAtBpm(120, bpmLow, bpmHigh, fadeIn, fadeOut, volume)).toBe(volume);
    });

    it('returns full volume at bpmHigh boundary', () => {
        expect(volumeAtBpm(170, bpmLow, bpmHigh, fadeIn, fadeOut, volume)).toBe(volume);
    });

    it('fades in linearly', () => {
        // Midpoint of fade-in: bpmLow - fadeIn/2 = 115
        const val = volumeAtBpm(115, bpmLow, bpmHigh, fadeIn, fadeOut, volume);
        expect(val).toBeCloseTo(0.4, 5); // 0.5 * 0.8
    });

    it('fades out linearly', () => {
        // Midpoint of fade-out: bpmHigh + fadeOut/2 = 177.5
        const val = volumeAtBpm(177.5, bpmLow, bpmHigh, fadeIn, fadeOut, volume);
        expect(val).toBeCloseTo(0.4, 5); // 0.5 * 0.8
    });

    it('returns 0 at exactly the fade-in start', () => {
        expect(volumeAtBpm(110, bpmLow, bpmHigh, fadeIn, fadeOut, volume)).toBe(0);
    });

    it('returns 0 at exactly the fade-out end', () => {
        // D = 170 + 15 = 185, at bpm=185 it should be 0 (bpm < d is false)
        expect(volumeAtBpm(185, bpmLow, bpmHigh, fadeIn, fadeOut, volume)).toBe(0);
    });

    it('returns 0 when muted', () => {
        expect(volumeAtBpm(140, bpmLow, bpmHigh, fadeIn, fadeOut, volume, true)).toBe(0);
    });

    it('handles zero fade-in', () => {
        // With fadeIn=0, A=B=bpmLow. Below bpmLow should be 0.
        expect(volumeAtBpm(119, bpmLow, bpmHigh, 0, fadeOut, volume)).toBe(0);
        expect(volumeAtBpm(120, bpmLow, bpmHigh, 0, fadeOut, volume)).toBe(volume);
    });

    it('handles zero fade-out', () => {
        expect(volumeAtBpm(170, bpmLow, bpmHigh, fadeIn, 0, volume)).toBe(volume);
        expect(volumeAtBpm(171, bpmLow, bpmHigh, fadeIn, 0, volume)).toBe(0);
    });

    it('handles bpmLow === bpmHigh (zero-width flat zone)', () => {
        const val = volumeAtBpm(150, 150, 150, 10, 10, 1.0);
        expect(val).toBe(1.0);
    });

    it('handles volume = 1.0', () => {
        expect(volumeAtBpm(140, bpmLow, bpmHigh, fadeIn, fadeOut, 1.0)).toBe(1.0);
    });

    it('handles volume = 0', () => {
        expect(volumeAtBpm(140, bpmLow, bpmHigh, fadeIn, fadeOut, 0)).toBe(0);
    });
});

describe('speedAtBpm', () => {
    it('returns baseSpeed when no speed points', () => {
        expect(speedAtBpm(150, null, 1.0)).toBe(1.0);
        expect(speedAtBpm(150, [], 1.0)).toBe(1.0);
    });

    it('returns baseSpeed with custom value', () => {
        expect(speedAtBpm(150, null, 1.5)).toBe(1.5);
    });

    it('clamps to first point below range', () => {
        const points = [[100, 0.8], [200, 1.2]];
        expect(speedAtBpm(50, points, 1.0)).toBe(0.8);
    });

    it('clamps to last point above range', () => {
        const points = [[100, 0.8], [200, 1.2]];
        expect(speedAtBpm(250, points, 1.0)).toBe(1.2);
    });

    it('interpolates linearly between points', () => {
        const points = [[100, 0.8], [200, 1.2]];
        expect(speedAtBpm(150, points, 1.0)).toBeCloseTo(1.0, 5);
    });

    it('multiplies by baseSpeed', () => {
        const points = [[100, 0.8], [200, 1.2]];
        expect(speedAtBpm(150, points, 2.0)).toBeCloseTo(2.0, 5);
    });

    it('handles single point', () => {
        const points = [[150, 1.5]];
        expect(speedAtBpm(100, points, 1.0)).toBe(1.5);
        expect(speedAtBpm(150, points, 1.0)).toBe(1.5);
        expect(speedAtBpm(200, points, 1.0)).toBe(1.5);
    });

    it('handles three points', () => {
        const points = [[100, 0.5], [150, 1.0], [200, 1.5]];
        expect(speedAtBpm(125, points, 1.0)).toBeCloseTo(0.75, 5);
        expect(speedAtBpm(175, points, 1.0)).toBeCloseTo(1.25, 5);
    });

    it('returns exact value at a defined point', () => {
        const points = [[100, 0.8], [150, 1.0], [200, 1.2]];
        expect(speedAtBpm(150, points, 1.0)).toBe(1.0);
    });
});

describe('volumeCurvePoints', () => {
    it('returns 4 points forming the trapezoid', () => {
        const pts = volumeCurvePoints(120, 170, 10, 15, 0.8);
        expect(pts).toHaveLength(4);
        expect(pts[0]).toEqual({ bpm: 110, vol: 0 });
        expect(pts[1]).toEqual({ bpm: 120, vol: 0.8 });
        expect(pts[2]).toEqual({ bpm: 170, vol: 0.8 });
        expect(pts[3]).toEqual({ bpm: 185, vol: 0 });
    });

    it('handles zero fades', () => {
        const pts = volumeCurvePoints(120, 170, 0, 0, 1.0);
        expect(pts[0].bpm).toBe(120);
        expect(pts[3].bpm).toBe(170);
    });
});

describe('bpmToPixel / pixelToBpm round-trip', () => {
    const width = 1000;

    it('converts BPM to pixel correctly', () => {
        expect(bpmToPixel(60, width)).toBe(0);
        expect(bpmToPixel(240, width)).toBe(1000);
        expect(bpmToPixel(150, width)).toBe(500);
    });

    it('converts pixel to BPM correctly', () => {
        expect(pixelToBpm(0, width)).toBe(60);
        expect(pixelToBpm(1000, width)).toBe(240);
        expect(pixelToBpm(500, width)).toBe(150);
    });

    it('round-trips accurately', () => {
        for (const bpm of [60, 90, 120, 150, 180, 210, 240]) {
            const px = bpmToPixel(bpm, width);
            const result = pixelToBpm(px, width);
            expect(result).toBeCloseTo(bpm, 10);
        }
    });
});

describe('volumeCurvePath', () => {
    it('returns a valid SVG path string', () => {
        const path = volumeCurvePath(120, 170, 10, 15, 0.8, 0, 0, 1000, 80);
        expect(path).toContain('M');
        expect(path).toContain('L');
        expect(path).toContain('Z');
    });
});

describe('speedCurvePoints', () => {
    it('generates correct number of samples', () => {
        const points = speedCurvePoints([[100, 0.8], [200, 1.2]], 1.0, 60, 240, 50);
        expect(points).toHaveLength(50);
    });

    it('returns flat line with no speed points', () => {
        const points = speedCurvePoints([], 1.5, 60, 240, 10);
        for (const p of points) {
            expect(p.speed).toBe(1.5);
        }
    });
});

describe('clamp', () => {
    it('clamps below min', () => expect(clamp(-5, 0, 10)).toBe(0));
    it('clamps above max', () => expect(clamp(15, 0, 10)).toBe(10));
    it('passes through in range', () => expect(clamp(5, 0, 10)).toBe(5));
    it('handles min === max', () => expect(clamp(5, 3, 3)).toBe(3));
});
