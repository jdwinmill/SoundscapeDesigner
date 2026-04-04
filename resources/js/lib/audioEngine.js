/**
 * AudioEngine — Web Audio engine for real-time BPM-reactive soundscape preview.
 *
 * Manages an AudioContext with per-stem audio nodes. Each stem gets:
 *   AudioBufferSourceNode (loop) → GainNode → masterGain → analyser → destination
 *
 * The engine is driven by a single BPM value. When BPM changes, all gains
 * and playback rates are recalculated with smooth ramps to avoid clicks.
 *
 * This is a plain class, not React state. Access it via a ref.
 */

import { volumeAtBpm, speedAtBpm } from './curvemath';

const RAMP_TIME = 0.05; // 50ms ramp for smooth transitions

export default class AudioEngine {
    constructor() {
        this.ctx = null;
        this.masterGain = null;
        this.analyser = null;
        this.stemNodes = new Map(); // Map<laneId, { source, gain, buffer, startOffset, startTime }>
        this.bpm = 150;
        this.masterVolume = 0.8;
        this.isPlaying = false;
        this.lanes = []; // Current lane configs for gain/rate calculation
    }

    /**
     * Initialize the AudioContext. Must be called from a user gesture.
     */
    init() {
        if (this.ctx) return;
        this.ctx = new AudioContext();
        this.masterGain = this.ctx.createGain();
        this.masterGain.gain.value = this.masterVolume;
        this.analyser = this.ctx.createAnalyser();
        this.analyser.fftSize = 256;
        this.masterGain.connect(this.analyser);
        this.analyser.connect(this.ctx.destination);
    }

    /**
     * Ensure the AudioContext is running (resume if suspended).
     */
    async _ensureRunning() {
        if (this.ctx && this.ctx.state === 'suspended') {
            await this.ctx.resume();
        }
    }

    /**
     * Fetch and decode an audio file, returning an AudioBuffer.
     */
    async fetchAndDecode(url) {
        this.init();
        const response = await fetch(url, { credentials: 'same-origin' });
        if (!response.ok) throw new Error(`Failed to fetch audio: ${response.status}`);
        const arrayBuffer = await response.arrayBuffer();
        return this.ctx.decodeAudioData(arrayBuffer);
    }

    /**
     * Add a stem to the engine with a decoded AudioBuffer.
     */
    addStem(laneId, audioBuffer) {
        if (!this.ctx) return;

        // Remove existing nodes for this lane if any
        this.removeStem(laneId);

        const gain = this.ctx.createGain();
        gain.gain.value = 0; // Start silent, will be set by syncAllStems
        gain.connect(this.masterGain);

        this.stemNodes.set(laneId, {
            gain,
            buffer: audioBuffer,
            source: null,
            startOffset: 0,
            startTime: 0,
        });

        // If currently playing, start this stem immediately
        if (this.isPlaying) {
            this._startSource(laneId);
        }

        this._syncStem(laneId);
    }

    /**
     * Remove a stem from the engine.
     */
    removeStem(laneId) {
        const node = this.stemNodes.get(laneId);
        if (!node) return;

        if (node.source) {
            try { node.source.stop(); } catch {}
            node.source.disconnect();
        }
        node.gain.disconnect();
        this.stemNodes.delete(laneId);
    }

    /**
     * Update the current BPM and recalculate all stems.
     */
    setBpm(bpm) {
        this.bpm = bpm;
        this._syncAllStems();
    }

    /**
     * Update the master volume.
     */
    setMasterVolume(volume) {
        this.masterVolume = volume;
        if (this.masterGain) {
            const t = this.ctx.currentTime + RAMP_TIME;
            this.masterGain.gain.linearRampToValueAtTime(volume, t);
        }
    }

    /**
     * Update the lane configs (called when reducer state changes).
     */
    setLanes(lanes) {
        this.lanes = lanes;
        this._syncAllStems();
    }

    /**
     * Start playback of all stems.
     */
    async play() {
        this.init();
        await this._ensureRunning();
        this.isPlaying = true;

        for (const [laneId] of this.stemNodes) {
            this._startSource(laneId);
        }
        this._syncAllStems();
    }

    /**
     * Stop playback, storing offsets for resume.
     */
    stop() {
        this.isPlaying = false;

        for (const [laneId, node] of this.stemNodes) {
            if (node.source) {
                // Calculate current offset for resume
                const elapsed = this.ctx.currentTime - node.startTime;
                const rate = node.source.playbackRate.value || 1;
                node.startOffset = (node.startOffset + elapsed * rate) % (node.buffer.duration || 1);

                try { node.source.stop(); } catch {}
                node.source.disconnect();
                node.source = null;
            }
        }
    }

    /**
     * Get analyser frequency data for level metering.
     * Returns a Uint8Array of frequency bin values.
     */
    getAnalyserData() {
        if (!this.analyser) return null;
        const data = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(data);
        return data;
    }

    /**
     * Get the current RMS level (0-1) from the analyser.
     */
    getLevel() {
        const data = this.getAnalyserData();
        if (!data) return 0;
        let sum = 0;
        for (let i = 0; i < data.length; i++) {
            const normalized = data[i] / 255;
            sum += normalized * normalized;
        }
        return Math.sqrt(sum / data.length);
    }

    /**
     * Tear down everything.
     */
    dispose() {
        this.stop();
        for (const [laneId] of this.stemNodes) {
            this.removeStem(laneId);
        }
        if (this.ctx) {
            this.ctx.close().catch(() => {});
            this.ctx = null;
            this.masterGain = null;
            this.analyser = null;
        }
    }

    // --- Internal ---

    _startSource(laneId) {
        const node = this.stemNodes.get(laneId);
        if (!node || !node.buffer) return;

        // Stop existing source if any
        if (node.source) {
            try { node.source.stop(); } catch {}
            node.source.disconnect();
        }

        const source = this.ctx.createBufferSource();
        source.buffer = node.buffer;
        source.loop = true;
        source.connect(node.gain);

        // Resume from stored offset
        const offset = node.startOffset % node.buffer.duration;
        source.start(0, offset);

        node.source = source;
        node.startTime = this.ctx.currentTime;
    }

    _syncAllStems() {
        for (const [laneId] of this.stemNodes) {
            this._syncStem(laneId);
        }
    }

    _syncStem(laneId) {
        const node = this.stemNodes.get(laneId);
        if (!node || !this.ctx) return;

        const lane = this.lanes.find((l) => l.id === laneId);
        if (!lane) return;

        const t = this.ctx.currentTime + RAMP_TIME;

        // --- Gain ---
        const hasSolo = this.lanes.some((l) => l.solo);
        let gain;

        if (lane.muted) {
            gain = 0;
        } else if (hasSolo && !lane.solo) {
            gain = 0;
        } else {
            const [bpmLow, bpmHigh] = lane.bpmRange;
            gain = volumeAtBpm(this.bpm, bpmLow, bpmHigh, lane.fadeIn, lane.fadeOut, lane.volume, false);
        }

        node.gain.gain.linearRampToValueAtTime(gain, t);

        // --- Playback rate ---
        if (node.source) {
            const baseBpm = 150; // Default base BPM for playback rate calculation
            const speedMultiplier = speedAtBpm(this.bpm, lane.speedCurve, lane.speed);
            const rate = Math.max(0.1, (this.bpm / baseBpm) * speedMultiplier);
            node.source.playbackRate.linearRampToValueAtTime(rate, t);
        }
    }
}
