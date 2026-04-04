/**
 * A single stem card within the picker panel.
 * Shows stem name, role, key, and an "Add" button.
 */
export default function StemPickerCard({ stem, packSlug, onAdd }) {
    return (
        <div className="flex items-center justify-between py-2.5 px-3 rounded-lg hover:bg-bg-tertiary transition-colors group">
            <div className="min-w-0 mr-3">
                <p className="text-text-primary text-sm font-medium truncate">{stem.name}</p>
                <p className="text-text-muted text-xs truncate">
                    {stem.role_type || 'stem'}
                    {stem.key && stem.key !== 'none' && ` · ${stem.key}`}
                    {stem.bpm && ` · ${stem.bpm} BPM`}
                </p>
            </div>
            <button
                onClick={() => onAdd({
                    stemId: stem.id,
                    stemName: stem.name,
                    stemPackSlug: packSlug,
                    bpmRange: [
                        Math.max(60, Math.round((stem.bpm || 150) - 30)),
                        Math.min(240, Math.round((stem.bpm || 150) + 30)),
                    ],
                })}
                className="shrink-0 text-xs font-medium px-3 py-1 rounded-lg bg-bg-elevated text-text-muted opacity-0 group-hover:opacity-100 hover:text-accent-teal hover:border-accent-teal border border-border-default transition-all"
            >
                + Add
            </button>
        </div>
    );
}
