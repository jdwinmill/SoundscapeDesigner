import { useReducer, useCallback, useEffect, useRef, useState } from 'react';
import { router, usePage } from '@inertiajs/react';
import AppLayout from '../../Layouts/AppLayout';
import DesignerCanvas from './DesignerCanvas';
import DesignerHeader from './DesignerHeader';
import StemPicker from './StemPicker';
import SpeedCurveEditor from './SpeedCurveEditor';
import { designerReducer, initialState, buildSavePayload } from '../../lib/designerReducer';
import { getColor } from '../../lib/stemColors';
import AudioEngine from '../../lib/audioEngine';
import apiFetch from '../../lib/apiFetch';

/**
 * Shared designer page component used by both Create and Edit.
 *
 * @param {object} props
 * @param {object|null} props.soundscape — Existing soundscape data (edit mode) or null (create mode)
 */
export default function DesignerPage({ soundscape = null }) {
    const { auth } = usePage().props;
    const isEditMode = !!soundscape;

    const [state, dispatch] = useReducer(designerReducer, initialState, () => {
        if (soundscape) {
            return designerReducer(initialState, {
                type: 'INIT_FROM_SERVER',
                payload: { soundscape },
            });
        }
        return initialState;
    });

    const engineRef = useRef(null);
    const [level, setLevel] = useState(0);
    const [saving, setSaving] = useState(false);
    const levelFrameRef = useRef(null);
    const [canvasWidth, setCanvasWidth] = useState(800);

    // Track canvas width from DesignerCanvas for speed curve editor
    const handleCanvasWidthChange = useCallback((width) => {
        setCanvasWidth(width);
    }, []);

    // --- Audio Engine ---

    useEffect(() => {
        engineRef.current = new AudioEngine();
        return () => {
            if (levelFrameRef.current) cancelAnimationFrame(levelFrameRef.current);
            engineRef.current?.dispose();
        };
    }, []);

    useEffect(() => {
        engineRef.current?.setLanes(state.lanes);
    }, [state.lanes]);

    useEffect(() => {
        engineRef.current?.setBpm(state.scrubBpm);
    }, [state.scrubBpm]);

    useEffect(() => {
        engineRef.current?.setMasterVolume(state.masterVolume);
    }, [state.masterVolume]);

    useEffect(() => {
        const engine = engineRef.current;
        if (!engine) return;

        if (state.isPlaying) {
            engine.play();
            function updateLevel() {
                setLevel(engine.getLevel());
                levelFrameRef.current = requestAnimationFrame(updateLevel);
            }
            levelFrameRef.current = requestAnimationFrame(updateLevel);
        } else {
            engine.stop();
            if (levelFrameRef.current) {
                cancelAnimationFrame(levelFrameRef.current);
                levelFrameRef.current = null;
            }
            setLevel(0);
        }
    }, [state.isPlaying]);

    // --- Audio buffer management ---

    // Track which lane IDs have had audio fetch initiated
    const fetchedLaneIdsRef = useRef(new Set());

    useEffect(() => {
        const engine = engineRef.current;
        if (!engine) return;

        // Remove stems for deleted lanes
        const currentIds = new Set(state.lanes.map((l) => l.id));
        for (const id of fetchedLaneIdsRef.current) {
            if (!currentIds.has(id)) {
                engine.removeStem(id);
                fetchedLaneIdsRef.current.delete(id);
            }
        }

        // Fetch audio for new lanes that haven't been fetched yet
        for (const lane of state.lanes) {
            if (lane.stemId > 0 && lane.loading && !fetchedLaneIdsRef.current.has(lane.id)) {
                fetchedLaneIdsRef.current.add(lane.id);
                const url = `/api/stem-packs/${lane.stemPackSlug}/stems/${lane.stemId}/download`;
                engine.fetchAndDecode(url)
                    .then((buffer) => {
                        engine.addStem(lane.id, buffer);
                        dispatch({ type: 'SET_AUDIO_BUFFER', payload: { id: lane.id, buffer } });
                    })
                    .catch((err) => {
                        dispatch({ type: 'SET_AUDIO_ERROR', payload: { id: lane.id, error: err.message } });
                    });
            }
        }
    }, [state.lanes]);

    // --- Keyboard shortcuts ---

    useEffect(() => {
        function handleKeyDown(e) {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            if ((e.metaKey || e.ctrlKey) && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                dispatch({ type: 'UNDO' });
            } else if ((e.metaKey || e.ctrlKey) && e.key === 'z' && e.shiftKey) {
                e.preventDefault();
                dispatch({ type: 'REDO' });
            } else if (e.key === 'Delete' || e.key === 'Backspace') {
                if (state.selectedLaneId) {
                    e.preventDefault();
                    dispatch({ type: 'REMOVE_LANE', payload: state.selectedLaneId });
                }
            } else if (e.key === 'Escape') {
                if (state.pickerOpen) {
                    dispatch({ type: 'TOGGLE_PICKER' });
                } else {
                    dispatch({ type: 'SELECT_LANE', payload: null });
                }
            } else if (e.key === ' ') {
                e.preventDefault();
                engineRef.current?.init();
                dispatch({ type: 'SET_PLAYING', payload: !state.isPlaying });
            }
        }

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [state.selectedLaneId, state.isPlaying, state.pickerOpen]);

    // --- Unsaved changes warning ---

    useEffect(() => {
        function handleBeforeUnload(e) {
            if (state.isDirty) {
                e.preventDefault();
                e.returnValue = '';
            }
        }
        window.addEventListener('beforeunload', handleBeforeUnload);
        return () => window.removeEventListener('beforeunload', handleBeforeUnload);
    }, [state.isDirty]);

    // --- Handlers ---

    const handleSelectLane = useCallback((id) => {
        dispatch({ type: 'SELECT_LANE', payload: id });
    }, []);

    const handleUpdateLane = useCallback((id, changes) => {
        dispatch({ type: 'UPDATE_LANE', payload: { id, changes } });
    }, []);

    const handleScrubBpmChange = useCallback((bpm) => {
        dispatch({ type: 'SET_SCRUB_BPM', payload: bpm });
    }, []);

    function handleAddStem(stemData) {
        dispatch({ type: 'ADD_LANE', payload: stemData });
    }

    function handlePlayStop() {
        engineRef.current?.init();
        dispatch({ type: 'SET_PLAYING', payload: !state.isPlaying });
    }

    async function handleSave() {
        const payload = buildSavePayload(state);
        setSaving(true);

        try {
            const url = isEditMode
                ? `/api/soundscapes/${soundscape.slug}`
                : '/api/soundscapes';
            const method = isEditMode ? 'PUT' : 'POST';

            const res = await apiFetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            if (res.ok) {
                dispatch({ type: 'MARK_CLEAN' });
                if (!isEditMode) {
                    const data = await res.json();
                    router.visit(`/s/${data.slug}`);
                }
            } else if (res.status === 422) {
                const json = await res.json();
                const firstError = Object.values(json.errors || {})[0];
                alert(firstError?.[0] || 'Validation failed');
            } else {
                alert('Failed to save');
            }
        } catch {
            alert('Failed to save');
        } finally {
            setSaving(false);
        }
    }

    const selectedLane = state.lanes.find((l) => l.id === state.selectedLaneId);

    return (
        <AppLayout>
            <div className="max-w-7xl mx-auto px-6 py-8">
                <DesignerHeader
                    state={state}
                    dispatch={dispatch}
                    onSave={handleSave}
                    saving={saving}
                />

                <DesignerCanvas
                    lanes={state.lanes}
                    selectedLaneId={state.selectedLaneId}
                    scrubBpm={state.scrubBpm}
                    onSelectLane={handleSelectLane}
                    onUpdateLane={handleUpdateLane}
                    onScrubBpmChange={handleScrubBpmChange}
                    dispatch={dispatch}
                    onWidthChange={handleCanvasWidthChange}
                />

                {/* Add stems */}
                <div className="mt-4">
                    <button
                        onClick={() => dispatch({ type: 'TOGGLE_PICKER' })}
                        className="bg-bg-elevated text-text-primary font-medium px-5 py-2.5 rounded-xl text-sm border border-border-default transition-all duration-250 hover:border-accent-teal"
                    >
                        + Add Stems
                    </button>
                </div>

                {/* Transport bar */}
                <div className="mt-6 bg-bg-secondary rounded-2xl border border-border-subtle p-4 flex items-center gap-6">
                    <button
                        onClick={handlePlayStop}
                        className={`w-10 h-10 rounded-xl flex items-center justify-center text-text-inverse transition-all hover:opacity-90 shrink-0 ${
                            state.isPlaying ? 'bg-highlight-amber' : 'bg-gradient-accent'
                        }`}
                    >
                        {state.isPlaying ? (
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                                <rect x="6" y="4" width="4" height="16" />
                                <rect x="14" y="4" width="4" height="16" />
                            </svg>
                        ) : (
                            <svg className="w-4 h-4 ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                                <polygon points="5,3 19,12 5,21" />
                            </svg>
                        )}
                    </button>

                    <div className="w-2 h-8 bg-bg-tertiary rounded-full overflow-hidden relative shrink-0">
                        <div
                            className="absolute bottom-0 w-full rounded-full transition-all duration-75"
                            style={{
                                height: `${Math.min(level * 300, 100)}%`,
                                background: level > 0.7 ? 'var(--color-error)' : 'var(--color-accent-teal)',
                            }}
                        />
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                        <span className="text-text-muted text-xs font-medium w-8">Vol</span>
                        <input type="range" min={0} max={1} step={0.01} value={state.masterVolume}
                            onChange={(e) => dispatch({ type: 'SET_MASTER_VOLUME', payload: parseFloat(e.target.value) })}
                            className="w-24 accent-accent-teal" />
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                        <span className="text-text-muted text-xs font-medium">BPM</span>
                        <span className="text-accent-teal font-mono text-lg font-bold">{Math.round(state.scrubBpm)}</span>
                    </div>

                    <div className="flex-1">
                        <input type="range" min={60} max={240} step={1} value={state.scrubBpm}
                            onChange={(e) => dispatch({ type: 'SET_SCRUB_BPM', payload: parseFloat(e.target.value) })}
                            className="w-full accent-highlight-amber" />
                    </div>

                    <div className="text-text-muted text-xs shrink-0">
                        {state.lanes.length} stem{state.lanes.length !== 1 && 's'}
                    </div>
                </div>

                {/* Selected lane controls */}
                {selectedLane && (
                    <div className="mt-4 bg-bg-secondary rounded-2xl border border-border-subtle p-4">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-3">
                                <h3 className="font-heading font-semibold text-sm" style={{ color: getColor(selectedLane.colorIndex).fill }}>
                                    {selectedLane.stemName}
                                </h3>
                                {selectedLane.loading && (
                                    <span className="text-text-muted text-xs flex items-center gap-1">
                                        <span className="w-3 h-3 border border-accent-teal border-t-transparent rounded-full animate-spin" />
                                        Loading audio...
                                    </span>
                                )}
                                {selectedLane.error && (
                                    <span className="text-error text-xs">{selectedLane.error}</span>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={() => dispatch({ type: 'SET_MUTED', payload: { id: selectedLane.id, muted: !selectedLane.muted } })}
                                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                                        selectedLane.muted ? 'bg-error/20 text-error' : 'bg-bg-tertiary text-text-muted hover:text-text-secondary'
                                    }`}
                                >
                                    {selectedLane.muted ? 'Muted' : 'Mute'}
                                </button>
                                <button
                                    onClick={() => dispatch({ type: 'SET_SOLO', payload: { id: selectedLane.id, solo: !selectedLane.solo } })}
                                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                                        selectedLane.solo ? 'bg-highlight-amber/20 text-highlight-amber' : 'bg-bg-tertiary text-text-muted hover:text-text-secondary'
                                    }`}
                                >
                                    Solo
                                </button>
                                <button
                                    onClick={() => dispatch({ type: 'EDIT_SPEED_CURVE', payload: state.editingSpeedCurve === selectedLane.id ? null : selectedLane.id })}
                                    className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                                        state.editingSpeedCurve === selectedLane.id ? 'bg-accent-violet/20 text-accent-violet' : 'bg-bg-tertiary text-text-muted hover:text-text-secondary'
                                    }`}
                                >
                                    Speed
                                </button>
                                <button
                                    onClick={() => dispatch({ type: 'REMOVE_LANE', payload: selectedLane.id })}
                                    className="px-3 py-1 rounded-lg text-xs font-medium bg-bg-tertiary text-text-muted hover:text-error transition-colors"
                                >
                                    Remove
                                </button>
                            </div>
                        </div>
                        <div className="grid grid-cols-5 gap-4 text-xs">
                            <div>
                                <span className="text-text-muted block mb-1">BPM Range</span>
                                <span className="text-text-primary font-mono">{selectedLane.bpmRange[0]} – {selectedLane.bpmRange[1]}</span>
                            </div>
                            <div>
                                <span className="text-text-muted block mb-1">Volume</span>
                                <span className="text-text-primary font-mono">{(selectedLane.volume * 100).toFixed(0)}%</span>
                            </div>
                            <div>
                                <span className="text-text-muted block mb-1">Fade In</span>
                                <span className="text-text-primary font-mono">{selectedLane.fadeIn} BPM</span>
                            </div>
                            <div>
                                <span className="text-text-muted block mb-1">Fade Out</span>
                                <span className="text-text-primary font-mono">{selectedLane.fadeOut} BPM</span>
                            </div>
                            <div>
                                <span className="text-text-muted block mb-1">Speed</span>
                                <span className="text-text-primary font-mono">{selectedLane.speed}x</span>
                            </div>
                        </div>

                        {state.editingSpeedCurve === selectedLane.id && (
                            <SpeedCurveEditor
                                lane={selectedLane}
                                canvasWidth={canvasWidth}
                                dispatch={dispatch}
                            />
                        )}
                    </div>
                )}
            </div>

            <StemPicker
                open={state.pickerOpen}
                onClose={() => dispatch({ type: 'TOGGLE_PICKER' })}
                onAddStem={handleAddStem}
                userId={auth.user?.id}
            />
        </AppLayout>
    );
}
