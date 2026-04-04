import { useState } from 'react';

/**
 * Header section for the soundscape designer.
 * Name input, optional description/tags, save/publish buttons.
 */
export default function DesignerHeader({ state, dispatch, onSave, saving }) {
    const [showDetails, setShowDetails] = useState(false);
    const [tagInput, setTagInput] = useState('');

    function addTag(e) {
        if (e.key === 'Enter' && tagInput.trim()) {
            e.preventDefault();
            if (!state.tags.includes(tagInput.trim())) {
                dispatch({
                    type: 'SET_METADATA',
                    payload: { tags: [...state.tags, tagInput.trim()] },
                });
            }
            setTagInput('');
        }
    }

    function removeTag(tag) {
        dispatch({
            type: 'SET_METADATA',
            payload: { tags: state.tags.filter((t) => t !== tag) },
        });
    }

    return (
        <div className="mb-6">
            <div className="flex items-center justify-between">
                <div className="flex-1 mr-4">
                    <input
                        type="text"
                        placeholder="Untitled Soundscape"
                        value={state.name}
                        onChange={(e) => dispatch({ type: 'SET_METADATA', payload: { name: e.target.value } })}
                        className="bg-transparent text-text-primary font-heading text-3xl font-bold placeholder-text-muted focus:outline-none w-full"
                    />
                </div>
                <div className="flex items-center gap-3">
                    {/* Undo/Redo */}
                    <button
                        onClick={() => dispatch({ type: 'UNDO' })}
                        disabled={state.past.length === 0}
                        className="text-text-muted hover:text-text-primary disabled:opacity-30 transition-colors p-2"
                        title="Undo (Ctrl+Z)"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 15L3 9m0 0l6-6M3 9h12a6 6 0 010 12h-3" />
                        </svg>
                    </button>
                    <button
                        onClick={() => dispatch({ type: 'REDO' })}
                        disabled={state.future.length === 0}
                        className="text-text-muted hover:text-text-primary disabled:opacity-30 transition-colors p-2"
                        title="Redo (Ctrl+Shift+Z)"
                    >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M15 15l6-6m0 0l-6-6m6 6H9a6 6 0 000 12h3" />
                        </svg>
                    </button>

                    <div className="w-px h-6 bg-border-default mx-1" />

                    {/* Public toggle */}
                    <button
                        onClick={() => dispatch({ type: 'SET_METADATA', payload: { isPublic: !state.isPublic } })}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                            state.isPublic
                                ? 'border-success/30 text-success bg-success/10'
                                : 'border-border-default text-text-muted bg-bg-elevated hover:text-text-secondary'
                        }`}
                    >
                        {state.isPublic ? 'Public' : 'Private'}
                    </button>

                    <button
                        onClick={onSave}
                        disabled={saving || !state.name.trim() || state.lanes.length === 0}
                        className="bg-gradient-accent text-text-inverse font-semibold px-6 py-2.5 rounded-xl text-sm transition-all duration-250 hover:opacity-90 disabled:opacity-50"
                    >
                        {saving ? 'Saving...' : state.isDirty ? 'Save' : 'Saved'}
                    </button>
                </div>
            </div>

            {/* Details toggle */}
            <button
                onClick={() => setShowDetails(!showDetails)}
                className="text-text-muted text-xs mt-2 hover:text-text-secondary transition-colors"
            >
                {showDetails ? '- Hide details' : '+ Description, tags'}
            </button>

            {showDetails && (
                <div className="mt-3 space-y-3">
                    <textarea
                        placeholder="Describe this soundscape..."
                        value={state.description}
                        onChange={(e) => dispatch({ type: 'SET_METADATA', payload: { description: e.target.value } })}
                        className="w-full bg-bg-tertiary text-text-primary border border-border-default rounded-xl px-4 py-3 text-sm placeholder-text-muted focus:outline-none focus:border-accent-teal transition-colors resize-none"
                        rows={2}
                    />
                    <div>
                        <label className="text-text-muted text-xs block mb-1">Target pace (BPM)</label>
                        <input
                            type="number"
                            min={60}
                            max={240}
                            value={state.baseBpm}
                            onChange={(e) => dispatch({ type: 'SET_METADATA', payload: { baseBpm: parseInt(e.target.value) || 150 } })}
                            className="w-32 bg-bg-tertiary text-text-primary border border-border-default rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-accent-teal transition-colors"
                        />
                        <span className="text-text-muted text-xs ml-2">The runner's home pace — used by the iOS app</span>
                    </div>
                    <div>
                        <div className="flex flex-wrap gap-1.5 mb-2">
                            {state.tags.map((tag) => (
                                <span
                                    key={tag}
                                    className="bg-bg-tertiary text-text-secondary text-xs px-2 py-0.5 rounded-md flex items-center gap-1"
                                >
                                    {tag}
                                    <button onClick={() => removeTag(tag)} className="text-text-muted hover:text-error">&times;</button>
                                </span>
                            ))}
                        </div>
                        <input
                            type="text"
                            placeholder="Add tag and press Enter"
                            value={tagInput}
                            onChange={(e) => setTagInput(e.target.value)}
                            onKeyDown={addTag}
                            className="w-full bg-bg-tertiary text-text-primary border border-border-default rounded-xl px-3 py-2 text-sm placeholder-text-muted focus:outline-none focus:border-accent-teal transition-colors"
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
