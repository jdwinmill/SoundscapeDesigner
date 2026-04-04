import { describe, it, expect, beforeEach } from 'vitest';
import {
    designerReducer,
    initialState,
    buildSavePayload,
} from '../designerReducer';

function dispatch(state, action) {
    return designerReducer(state, action);
}

function addTestLane(state, overrides = {}) {
    return dispatch(state, {
        type: 'ADD_LANE',
        payload: {
            stemId: 1,
            stemName: 'Test Stem',
            stemPackSlug: 'test-pack',
            bpmRange: [120, 170],
            fadeIn: 10,
            fadeOut: 10,
            volume: 0.8,
            ...overrides,
        },
    });
}

describe('ADD_LANE', () => {
    it('adds a lane with correct defaults', () => {
        const state = addTestLane(initialState);
        expect(state.lanes).toHaveLength(1);
        expect(state.lanes[0].stemId).toBe(1);
        expect(state.lanes[0].stemName).toBe('Test Stem');
        expect(state.lanes[0].bpmRange).toEqual([120, 170]);
        expect(state.lanes[0].volume).toBe(0.8);
        expect(state.lanes[0].muted).toBe(false);
        expect(state.lanes[0].solo).toBe(false);
        expect(state.lanes[0].loading).toBe(true);
        expect(state.lanes[0].audioBuffer).toBeNull();
    });

    it('assigns incrementing color indices', () => {
        let state = addTestLane(initialState);
        state = addTestLane(state, { stemId: 2, stemName: 'Stem 2' });
        expect(state.lanes[0].colorIndex).toBe(0);
        expect(state.lanes[1].colorIndex).toBe(1);
    });

    it('generates unique lane IDs', () => {
        let state = addTestLane(initialState);
        state = addTestLane(state);
        expect(state.lanes[0].id).not.toBe(state.lanes[1].id);
    });

    it('pushes to undo history', () => {
        const state = addTestLane(initialState);
        expect(state.past).toHaveLength(1);
        expect(state.future).toHaveLength(0);
    });

    it('marks state as dirty', () => {
        const state = addTestLane(initialState);
        expect(state.isDirty).toBe(true);
    });

    it('uses default bpmRange when not provided', () => {
        const state = dispatch(initialState, {
            type: 'ADD_LANE',
            payload: { stemId: 1, stemName: 'Test', stemPackSlug: 'test' },
        });
        expect(state.lanes[0].bpmRange).toEqual([120, 170]);
        expect(state.lanes[0].fadeIn).toBe(10);
    });
});

describe('REMOVE_LANE', () => {
    it('removes the specified lane', () => {
        let state = addTestLane(initialState);
        const laneId = state.lanes[0].id;
        state = dispatch(state, { type: 'REMOVE_LANE', payload: laneId });
        expect(state.lanes).toHaveLength(0);
    });

    it('clears selection if removed lane was selected', () => {
        let state = addTestLane(initialState);
        const laneId = state.lanes[0].id;
        state = dispatch(state, { type: 'SELECT_LANE', payload: laneId });
        state = dispatch(state, { type: 'REMOVE_LANE', payload: laneId });
        expect(state.selectedLaneId).toBeNull();
    });

    it('keeps selection if different lane was removed', () => {
        let state = addTestLane(initialState);
        state = addTestLane(state, { stemId: 2 });
        const firstId = state.lanes[0].id;
        const secondId = state.lanes[1].id;
        state = dispatch(state, { type: 'SELECT_LANE', payload: firstId });
        state = dispatch(state, { type: 'REMOVE_LANE', payload: secondId });
        expect(state.selectedLaneId).toBe(firstId);
    });

    it('pushes to undo history', () => {
        let state = addTestLane(initialState);
        const prevPast = state.past.length;
        state = dispatch(state, { type: 'REMOVE_LANE', payload: state.lanes[0].id });
        expect(state.past.length).toBe(prevPast + 1);
    });
});

describe('UPDATE_LANE', () => {
    it('updates specific fields on a lane', () => {
        let state = addTestLane(initialState);
        const id = state.lanes[0].id;
        state = dispatch(state, {
            type: 'UPDATE_LANE',
            payload: { id, changes: { volume: 0.5, bpmRange: [100, 180] } },
        });
        expect(state.lanes[0].volume).toBe(0.5);
        expect(state.lanes[0].bpmRange).toEqual([100, 180]);
    });

    it('does not affect other lanes', () => {
        let state = addTestLane(initialState);
        state = addTestLane(state, { stemId: 2, stemName: 'Other' });
        const id = state.lanes[0].id;
        state = dispatch(state, {
            type: 'UPDATE_LANE',
            payload: { id, changes: { volume: 0.1 } },
        });
        expect(state.lanes[0].volume).toBe(0.1);
        expect(state.lanes[1].volume).toBe(0.8); // unchanged
    });

    it('preserves unmodified fields', () => {
        let state = addTestLane(initialState);
        const id = state.lanes[0].id;
        state = dispatch(state, {
            type: 'UPDATE_LANE',
            payload: { id, changes: { volume: 0.3 } },
        });
        expect(state.lanes[0].fadeIn).toBe(10); // unchanged
        expect(state.lanes[0].stemName).toBe('Test Stem'); // unchanged
    });
});

describe('SET_MUTED / SET_SOLO', () => {
    it('toggles muted', () => {
        let state = addTestLane(initialState);
        const id = state.lanes[0].id;
        state = dispatch(state, { type: 'SET_MUTED', payload: { id, muted: true } });
        expect(state.lanes[0].muted).toBe(true);
        state = dispatch(state, { type: 'SET_MUTED', payload: { id, muted: false } });
        expect(state.lanes[0].muted).toBe(false);
    });

    it('toggles solo', () => {
        let state = addTestLane(initialState);
        const id = state.lanes[0].id;
        state = dispatch(state, { type: 'SET_SOLO', payload: { id, solo: true } });
        expect(state.lanes[0].solo).toBe(true);
    });
});

describe('SET_METADATA', () => {
    it('updates metadata fields', () => {
        const state = dispatch(initialState, {
            type: 'SET_METADATA',
            payload: { name: 'My Soundscape', baseBpm: 160 },
        });
        expect(state.name).toBe('My Soundscape');
        expect(state.baseBpm).toBe(160);
    });

    it('pushes to undo history', () => {
        const state = dispatch(initialState, {
            type: 'SET_METADATA',
            payload: { name: 'Test' },
        });
        expect(state.past).toHaveLength(1);
    });
});

describe('Undo / Redo', () => {
    it('undoes ADD_LANE', () => {
        let state = addTestLane(initialState);
        expect(state.lanes).toHaveLength(1);
        state = dispatch(state, { type: 'UNDO' });
        expect(state.lanes).toHaveLength(0);
        expect(state.future).toHaveLength(1);
    });

    it('redoes after undo', () => {
        let state = addTestLane(initialState);
        state = dispatch(state, { type: 'UNDO' });
        state = dispatch(state, { type: 'REDO' });
        expect(state.lanes).toHaveLength(1);
    });

    it('clears future on new action after undo', () => {
        let state = addTestLane(initialState);
        state = dispatch(state, { type: 'UNDO' });
        expect(state.future).toHaveLength(1);
        state = addTestLane(state, { stemId: 99 });
        expect(state.future).toHaveLength(0);
    });

    it('does nothing on UNDO with empty history', () => {
        const state = dispatch(initialState, { type: 'UNDO' });
        expect(state).toBe(initialState);
    });

    it('does nothing on REDO with empty future', () => {
        const state = dispatch(initialState, { type: 'REDO' });
        expect(state).toBe(initialState);
    });

    it('undoes UPDATE_LANE', () => {
        let state = addTestLane(initialState);
        const id = state.lanes[0].id;
        state = dispatch(state, {
            type: 'UPDATE_LANE',
            payload: { id, changes: { volume: 0.1 } },
        });
        expect(state.lanes[0].volume).toBe(0.1);
        state = dispatch(state, { type: 'UNDO' });
        expect(state.lanes[0].volume).toBe(0.8);
    });

    it('limits history to 50 entries', () => {
        let state = initialState;
        for (let i = 0; i < 60; i++) {
            state = dispatch(state, {
                type: 'SET_METADATA',
                payload: { name: `Name ${i}` },
            });
        }
        expect(state.past.length).toBeLessThanOrEqual(50);
    });
});

describe('Drag operations (DRAG_START + DRAG_UPDATE_LANE)', () => {
    it('DRAG_START pushes one undo entry', () => {
        let state = addTestLane(initialState);
        const prevPast = state.past.length;
        state = dispatch(state, { type: 'DRAG_START' });
        expect(state.past.length).toBe(prevPast + 1);
    });

    it('DRAG_UPDATE_LANE does not push undo history', () => {
        let state = addTestLane(initialState);
        state = dispatch(state, { type: 'DRAG_START' });
        const pastAfterStart = state.past.length;

        // Simulate 50 drag moves — none should push history
        for (let i = 0; i < 50; i++) {
            state = dispatch(state, {
                type: 'DRAG_UPDATE_LANE',
                payload: { id: state.lanes[0].id, changes: { volume: 0.5 + i * 0.01 } },
            });
        }
        expect(state.past.length).toBe(pastAfterStart);
    });

    it('DRAG_UPDATE_LANE applies changes', () => {
        let state = addTestLane(initialState);
        const id = state.lanes[0].id;
        state = dispatch(state, {
            type: 'DRAG_UPDATE_LANE',
            payload: { id, changes: { bpmRange: [130, 180] } },
        });
        expect(state.lanes[0].bpmRange).toEqual([130, 180]);
    });

    it('one undo reverses entire drag operation', () => {
        let state = addTestLane(initialState);
        const id = state.lanes[0].id;
        const originalVolume = state.lanes[0].volume;

        // Start drag
        state = dispatch(state, { type: 'DRAG_START' });

        // Simulate many drag moves
        for (let i = 0; i < 20; i++) {
            state = dispatch(state, {
                type: 'DRAG_UPDATE_LANE',
                payload: { id, changes: { volume: 0.1 + i * 0.04 } },
            });
        }
        expect(state.lanes[0].volume).not.toBe(originalVolume);

        // One undo should revert to state before drag started
        state = dispatch(state, { type: 'UNDO' });
        expect(state.lanes[0].volume).toBe(originalVolume);
    });

    it('marks state as dirty', () => {
        let state = addTestLane(initialState);
        state = dispatch(state, { type: 'MARK_CLEAN' });
        state = dispatch(state, {
            type: 'DRAG_UPDATE_LANE',
            payload: { id: state.lanes[0].id, changes: { volume: 0.3 } },
        });
        expect(state.isDirty).toBe(true);
    });
});

describe('Transport actions do not affect undo history', () => {
    it('SET_SCRUB_BPM does not push history', () => {
        const state = dispatch(initialState, { type: 'SET_SCRUB_BPM', payload: 180 });
        expect(state.scrubBpm).toBe(180);
        expect(state.past).toHaveLength(0);
    });

    it('SET_PLAYING does not push history', () => {
        const state = dispatch(initialState, { type: 'SET_PLAYING', payload: true });
        expect(state.isPlaying).toBe(true);
        expect(state.past).toHaveLength(0);
    });

    it('SET_MASTER_VOLUME does not push history', () => {
        const state = dispatch(initialState, { type: 'SET_MASTER_VOLUME', payload: 0.5 });
        expect(state.masterVolume).toBe(0.5);
        expect(state.past).toHaveLength(0);
    });

    it('SELECT_LANE does not push history', () => {
        let state = addTestLane(initialState);
        const prevPast = state.past.length;
        state = dispatch(state, { type: 'SELECT_LANE', payload: state.lanes[0].id });
        expect(state.past.length).toBe(prevPast);
    });

    it('SET_AUDIO_BUFFER does not push history', () => {
        let state = addTestLane(initialState);
        const prevPast = state.past.length;
        state = dispatch(state, {
            type: 'SET_AUDIO_BUFFER',
            payload: { id: state.lanes[0].id, buffer: 'fake-buffer' },
        });
        expect(state.lanes[0].audioBuffer).toBe('fake-buffer');
        expect(state.lanes[0].loading).toBe(false);
        expect(state.past.length).toBe(prevPast);
    });
});

describe('TOGGLE_PICKER', () => {
    it('opens the picker', () => {
        const state = dispatch(initialState, { type: 'TOGGLE_PICKER' });
        expect(state.pickerOpen).toBe(true);
    });

    it('closes the picker when already open', () => {
        let state = dispatch(initialState, { type: 'TOGGLE_PICKER' });
        state = dispatch(state, { type: 'TOGGLE_PICKER' });
        expect(state.pickerOpen).toBe(false);
    });

    it('does not push undo history', () => {
        const state = dispatch(initialState, { type: 'TOGGLE_PICKER' });
        expect(state.past).toHaveLength(0);
    });
});

describe('INIT_FROM_SERVER', () => {
    it('initializes state from server soundscape data', () => {
        const serverData = {
            soundscape: {
                name: 'My Run Mix',
                description: 'A chill mix',
                base_bpm: 160,
                is_public: true,
                tags: [{ name: 'running' }, { name: 'chill' }],
                stems: [
                    {
                        id: 42,
                        name: 'Kick Loop',
                        stem_pack: { slug: 'my-pack' },
                        pivot: {
                            bpm_range: JSON.stringify([120, 170]),
                            fade_in: '8',
                            fade_out: '12',
                            volume: '0.7',
                            speed: '1.0',
                            speed_curve: null,
                            sort_order: '0',
                        },
                    },
                    {
                        id: 43,
                        name: 'Pad',
                        stem_pack: { slug: 'my-pack' },
                        pivot: {
                            bpm_range: JSON.stringify([100, 200]),
                            fade_in: '15',
                            fade_out: '15',
                            volume: '0.5',
                            speed: '1.2',
                            speed_curve: JSON.stringify([[100, 0.9], [200, 1.1]]),
                            sort_order: '1',
                        },
                    },
                ],
            },
        };

        const state = dispatch(initialState, {
            type: 'INIT_FROM_SERVER',
            payload: serverData,
        });

        expect(state.name).toBe('My Run Mix');
        expect(state.description).toBe('A chill mix');
        expect(state.baseBpm).toBe(160);
        expect(state.isPublic).toBe(true);
        expect(state.tags).toEqual(['running', 'chill']);
        expect(state.scrubBpm).toBe(160);
        expect(state.lanes).toHaveLength(2);

        // First lane
        expect(state.lanes[0].stemId).toBe(42);
        expect(state.lanes[0].stemName).toBe('Kick Loop');
        expect(state.lanes[0].stemPackSlug).toBe('my-pack');
        expect(state.lanes[0].bpmRange).toEqual([120, 170]);
        expect(state.lanes[0].fadeIn).toBe(8);
        expect(state.lanes[0].fadeOut).toBe(12);
        expect(state.lanes[0].volume).toBe(0.7);
        expect(state.lanes[0].speed).toBe(1.0);
        expect(state.lanes[0].speedCurve).toBeNull();
        expect(state.lanes[0].loading).toBe(true);

        // Second lane with speed curve
        expect(state.lanes[1].stemId).toBe(43);
        expect(state.lanes[1].speed).toBe(1.2);
        expect(state.lanes[1].speedCurve).toEqual([[100, 0.9], [200, 1.1]]);
    });

    it('resets history on init', () => {
        let state = addTestLane(initialState);
        state = dispatch(state, {
            type: 'INIT_FROM_SERVER',
            payload: {
                soundscape: {
                    name: 'Test',
                    description: '',
                    base_bpm: 150,
                    is_public: false,
                    tags: [],
                    stems: [],
                },
            },
        });
        expect(state.past).toHaveLength(0);
        expect(state.future).toHaveLength(0);
    });

    it('handles missing optional fields', () => {
        const state = dispatch(initialState, {
            type: 'INIT_FROM_SERVER',
            payload: {
                soundscape: {
                    name: 'Minimal',
                    base_bpm: 150,
                    is_public: false,
                    stems: [],
                },
            },
        });
        expect(state.description).toBe('');
        expect(state.tags).toEqual([]);
        expect(state.lanes).toHaveLength(0);
    });
});

describe('MARK_CLEAN', () => {
    it('sets isDirty to false', () => {
        let state = addTestLane(initialState);
        expect(state.isDirty).toBe(true);
        state = dispatch(state, { type: 'MARK_CLEAN' });
        expect(state.isDirty).toBe(false);
    });
});

describe('buildSavePayload', () => {
    it('maps state to API format', () => {
        let state = dispatch(initialState, {
            type: 'SET_METADATA',
            payload: { name: 'Test Scape', baseBpm: 160, isPublic: true, tags: ['running'] },
        });
        state = addTestLane(state);
        state = addTestLane(state, { stemId: 2, stemName: 'Stem 2', bpmRange: [140, 190], volume: 0.6 });

        const payload = buildSavePayload(state);

        expect(payload.name).toBe('Test Scape');
        expect(payload.base_bpm).toBe(160);
        expect(payload.is_public).toBe(true);
        expect(payload.tags).toEqual(['running']);
        expect(payload.stems).toHaveLength(2);
        expect(payload.stems[0].stem_id).toBe(1);
        expect(payload.stems[0].bpm_range).toEqual([120, 170]);
        expect(payload.stems[0].fade_in).toBe(10);
        expect(payload.stems[0].volume).toBe(0.8);
        expect(payload.stems[0].sort_order).toBe(0);
        expect(payload.stems[1].stem_id).toBe(2);
        expect(payload.stems[1].sort_order).toBe(1);
    });

    it('includes speed_curve when set', () => {
        let state = addTestLane(initialState);
        const id = state.lanes[0].id;
        state = dispatch(state, {
            type: 'UPDATE_SPEED_CURVE',
            payload: { id, speedCurve: [[120, 0.9], [170, 1.1]] },
        });

        const payload = buildSavePayload(state);
        expect(payload.stems[0].speed_curve).toEqual([[120, 0.9], [170, 1.1]]);
    });

    it('sets speed_curve to null when not defined', () => {
        const state = addTestLane(initialState);
        const payload = buildSavePayload(state);
        expect(payload.stems[0].speed_curve).toBeNull();
    });
});
