/**
 * Designer Reducer — State management for the Soundscape Designer.
 *
 * Uses a snapshot-based undo/redo system. Design-changing actions
 * push the previous state to `past` before applying. Transport and
 * UI-only actions skip the history.
 */

let nextLaneId = 0;

export function generateLaneId() {
    return `lane-${nextLaneId++}`;
}

export const BPM_MIN = 60;
export const BPM_MAX = 240;

export const initialState = {
    // Soundscape metadata
    name: '',
    description: '',
    baseBpm: 150,
    isPublic: false,
    tags: [],

    // Stem lanes
    lanes: [],

    // Transport
    scrubBpm: 150,
    isPlaying: false,
    masterVolume: 0.8,

    // UI
    selectedLaneId: null,
    pickerOpen: false,
    editingSpeedCurve: null,
    isDirty: false,

    // History
    past: [],
    future: [],
};

/**
 * Take a snapshot of the design state (for undo/redo).
 * Excludes runtime-only fields (audioBuffer, loading, UI state).
 */
function snapshot(state) {
    return {
        name: state.name,
        description: state.description,
        baseBpm: state.baseBpm,
        isPublic: state.isPublic,
        tags: [...state.tags],
        lanes: state.lanes.map((lane) => ({
            ...lane,
            // Exclude runtime fields from snapshot
            audioBuffer: undefined,
            loading: undefined,
            error: undefined,
        })),
    };
}

/**
 * Restore a snapshot into the current state, preserving runtime fields.
 */
function restoreSnapshot(state, snap) {
    return {
        ...state,
        name: snap.name,
        description: snap.description,
        baseBpm: snap.baseBpm,
        isPublic: snap.isPublic,
        tags: snap.tags,
        lanes: snap.lanes.map((snapLane) => {
            const existing = state.lanes.find((l) => l.id === snapLane.id);
            return {
                ...snapLane,
                audioBuffer: existing?.audioBuffer || null,
                loading: existing?.loading || false,
                error: existing?.error || null,
            };
        }),
        isDirty: true,
    };
}

/**
 * Push current state to history before a design change.
 */
function pushHistory(state) {
    return {
        past: [...state.past.slice(-49), snapshot(state)], // Keep max 50 entries
        future: [],
    };
}

export function designerReducer(state, action) {
    switch (action.type) {
        // --- Design changes (with undo history) ---

        case 'SET_METADATA': {
            const history = pushHistory(state);
            return {
                ...state,
                ...history,
                ...action.payload,
                isDirty: true,
            };
        }

        case 'ADD_LANE': {
            const history = pushHistory(state);
            const newLane = {
                id: generateLaneId(),
                stemId: action.payload.stemId,
                stemName: action.payload.stemName,
                stemPackSlug: action.payload.stemPackSlug,
                bpmRange: action.payload.bpmRange || [120, 170],
                fadeIn: action.payload.fadeIn ?? 10,
                fadeOut: action.payload.fadeOut ?? 10,
                volume: action.payload.volume ?? 0.8,
                speed: action.payload.speed ?? 1.0,
                speedCurve: action.payload.speedCurve || null,
                muted: false,
                solo: false,
                colorIndex: state.lanes.length,
                sortOrder: state.lanes.length,
                // Runtime
                audioBuffer: null,
                loading: true,
                error: null,
            };
            return {
                ...state,
                ...history,
                lanes: [...state.lanes, newLane],
                isDirty: true,
            };
        }

        case 'REMOVE_LANE': {
            const history = pushHistory(state);
            return {
                ...state,
                ...history,
                lanes: state.lanes.filter((l) => l.id !== action.payload),
                selectedLaneId: state.selectedLaneId === action.payload ? null : state.selectedLaneId,
                editingSpeedCurve: state.editingSpeedCurve === action.payload ? null : state.editingSpeedCurve,
                isDirty: true,
            };
        }

        case 'UPDATE_LANE': {
            const history = pushHistory(state);
            return {
                ...state,
                ...history,
                lanes: state.lanes.map((lane) =>
                    lane.id === action.payload.id
                        ? { ...lane, ...action.payload.changes }
                        : lane
                ),
                isDirty: true,
            };
        }

        // Drag operations: push one undo entry at start, then update without history
        case 'DRAG_START': {
            const history = pushHistory(state);
            return { ...state, ...history };
        }

        case 'DRAG_UPDATE_LANE': {
            return {
                ...state,
                lanes: state.lanes.map((lane) =>
                    lane.id === action.payload.id
                        ? { ...lane, ...action.payload.changes }
                        : lane
                ),
                isDirty: true,
            };
        }

        case 'REORDER_LANES': {
            const history = pushHistory(state);
            return {
                ...state,
                ...history,
                lanes: action.payload.map((id, i) => {
                    const lane = state.lanes.find((l) => l.id === id);
                    return { ...lane, sortOrder: i };
                }),
                isDirty: true,
            };
        }

        case 'SET_MUTED': {
            const history = pushHistory(state);
            return {
                ...state,
                ...history,
                lanes: state.lanes.map((lane) =>
                    lane.id === action.payload.id
                        ? { ...lane, muted: action.payload.muted }
                        : lane
                ),
                isDirty: true,
            };
        }

        case 'SET_SOLO': {
            const history = pushHistory(state);
            return {
                ...state,
                ...history,
                lanes: state.lanes.map((lane) =>
                    lane.id === action.payload.id
                        ? { ...lane, solo: action.payload.solo }
                        : lane
                ),
                isDirty: true,
            };
        }

        case 'UPDATE_SPEED_CURVE': {
            const history = pushHistory(state);
            return {
                ...state,
                ...history,
                lanes: state.lanes.map((lane) =>
                    lane.id === action.payload.id
                        ? { ...lane, speedCurve: action.payload.speedCurve }
                        : lane
                ),
                isDirty: true,
            };
        }

        // --- Undo / Redo ---

        case 'UNDO': {
            if (state.past.length === 0) return state;
            const previous = state.past[state.past.length - 1];
            return {
                ...restoreSnapshot(state, previous),
                past: state.past.slice(0, -1),
                future: [snapshot(state), ...state.future.slice(0, 49)],
            };
        }

        case 'REDO': {
            if (state.future.length === 0) return state;
            const next = state.future[0];
            return {
                ...restoreSnapshot(state, next),
                past: [...state.past, snapshot(state)],
                future: state.future.slice(1),
            };
        }

        // --- Transport / UI (no undo) ---

        case 'SET_SCRUB_BPM':
            return { ...state, scrubBpm: action.payload };

        case 'SET_PLAYING':
            return { ...state, isPlaying: action.payload };

        case 'SET_MASTER_VOLUME':
            return { ...state, masterVolume: action.payload };

        case 'SELECT_LANE':
            return { ...state, selectedLaneId: action.payload };

        case 'TOGGLE_PICKER':
            return { ...state, pickerOpen: !state.pickerOpen };

        case 'EDIT_SPEED_CURVE':
            return { ...state, editingSpeedCurve: action.payload };

        case 'SET_AUDIO_BUFFER':
            return {
                ...state,
                lanes: state.lanes.map((lane) =>
                    lane.id === action.payload.id
                        ? { ...lane, audioBuffer: action.payload.buffer, loading: false, error: null }
                        : lane
                ),
            };

        case 'SET_AUDIO_ERROR':
            return {
                ...state,
                lanes: state.lanes.map((lane) =>
                    lane.id === action.payload.id
                        ? { ...lane, loading: false, error: action.payload.error }
                        : lane
                ),
            };

        case 'MARK_CLEAN':
            return { ...state, isDirty: false };

        // --- Initialize from server data (edit mode) ---

        case 'INIT_FROM_SERVER': {
            const { soundscape } = action.payload;
            return {
                ...initialState,
                name: soundscape.name,
                description: soundscape.description || '',
                baseBpm: soundscape.base_bpm,
                isPublic: soundscape.is_public,
                tags: (soundscape.tags || []).map((t) => t.name),
                lanes: (soundscape.stems || []).map((stem, i) => ({
                    id: generateLaneId(),
                    stemId: stem.id,
                    stemName: stem.name,
                    stemPackSlug: stem.stem_pack?.slug || '',
                    bpmRange: JSON.parse(stem.pivot.bpm_range),
                    fadeIn: parseFloat(stem.pivot.fade_in),
                    fadeOut: parseFloat(stem.pivot.fade_out),
                    volume: parseFloat(stem.pivot.volume),
                    speed: parseFloat(stem.pivot.speed),
                    speedCurve: stem.pivot.speed_curve ? JSON.parse(stem.pivot.speed_curve) : null,
                    muted: false,
                    solo: false,
                    colorIndex: i,
                    sortOrder: parseInt(stem.pivot.sort_order),
                    audioBuffer: null,
                    loading: true,
                    error: null,
                })),
                scrubBpm: soundscape.base_bpm,
            };
        }

        default:
            return state;
    }
}

/**
 * Build the API payload from designer state.
 */
export function buildSavePayload(state) {
    return {
        name: state.name,
        description: state.description || null,
        base_bpm: state.baseBpm,
        is_public: state.isPublic,
        tags: state.tags,
        stems: state.lanes.map((lane, i) => ({
            stem_id: lane.stemId,
            bpm_range: lane.bpmRange,
            fade_in: lane.fadeIn,
            fade_out: lane.fadeOut,
            volume: lane.volume,
            speed: lane.speed,
            speed_curve: lane.speedCurve,
            sort_order: i,
        })),
    };
}
