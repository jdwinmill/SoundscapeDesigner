import { useState, useEffect } from 'react';
import StemPickerCard from './StemPickerCard';
import apiFetch from '../../lib/apiFetch';

/**
 * Slide-out panel for browsing and adding stems to the designer.
 * Fetches stem packs from the API. Tabs for "My Packs" and "Explore".
 */
export default function StemPicker({ open, onClose, onAddStem, userId }) {
    const [tab, setTab] = useState('mine');
    const [search, setSearch] = useState('');
    const [packs, setPacks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [expandedPack, setExpandedPack] = useState(null);

    useEffect(() => {
        if (!open) return;
        fetchPacks();
    }, [open, tab]);

    async function fetchPacks() {
        setLoading(true);
        try {
            const res = await apiFetch('/api/stem-packs');
            if (res.ok) {
                const json = await res.json();
                setPacks(json.data || []);
            }
        } catch {
            // Silently fail — user can retry
        } finally {
            setLoading(false);
        }
    }

    if (!open) return null;

    // Filter packs based on tab and search
    const filtered = packs.filter((pack) => {
        if (tab === 'mine' && pack.user_id !== userId) return false;
        if (tab === 'explore' && pack.user_id === userId) return false;
        const term = search.toLowerCase();
        if (!term) return true;
        return (
            pack.name.toLowerCase().includes(term) ||
            (pack.genre || '').toLowerCase().includes(term)
        );
    });

    return (
        <div className="fixed inset-0 z-[60] flex justify-end">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/40"
                onClick={onClose}
            />

            {/* Panel */}
            <div className="relative w-full max-w-md bg-bg-secondary border-l border-border-subtle flex flex-col h-full">
                {/* Header */}
                <div className="p-4 border-b border-border-subtle">
                    <div className="flex items-center justify-between mb-3">
                        <h2 className="font-heading font-semibold text-lg">Add Stems</h2>
                        <button
                            onClick={onClose}
                            className="text-text-muted hover:text-text-primary transition-colors p-1"
                        >
                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>

                    {/* Search */}
                    <input
                        type="text"
                        placeholder="Search packs..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full bg-bg-tertiary text-text-primary border border-border-default rounded-xl px-3 py-2 text-sm placeholder-text-muted focus:outline-none focus:border-accent-teal transition-colors mb-3"
                        autoFocus
                    />

                    {/* Tabs */}
                    <div className="flex bg-bg-tertiary rounded-lg p-0.5">
                        <button
                            onClick={() => setTab('mine')}
                            className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                                tab === 'mine'
                                    ? 'bg-bg-elevated text-text-primary'
                                    : 'text-text-muted hover:text-text-secondary'
                            }`}
                        >
                            My Packs
                        </button>
                        <button
                            onClick={() => setTab('explore')}
                            className={`flex-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                                tab === 'explore'
                                    ? 'bg-bg-elevated text-text-primary'
                                    : 'text-text-muted hover:text-text-secondary'
                            }`}
                        >
                            Explore
                        </button>
                    </div>
                </div>

                {/* Pack list */}
                <div className="flex-1 overflow-y-auto p-4 space-y-2">
                    {loading ? (
                        <div className="flex items-center justify-center py-12">
                            <div className="w-6 h-6 border-2 border-accent-teal border-t-transparent rounded-full animate-spin" />
                        </div>
                    ) : filtered.length === 0 ? (
                        <div className="text-center py-12">
                            <p className="text-text-muted text-sm">
                                {search ? 'No packs match your search.' : 'No packs found.'}
                            </p>
                            {tab === 'mine' && !search && (
                                <p className="text-text-muted text-xs mt-2">
                                    Create a stem pack and upload audio files first.
                                </p>
                            )}
                        </div>
                    ) : (
                        filtered.map((pack) => (
                            <div
                                key={pack.id}
                                className="bg-bg-tertiary rounded-xl border border-border-subtle overflow-hidden"
                            >
                                {/* Pack header (click to expand) */}
                                <button
                                    onClick={() => setExpandedPack(expandedPack === pack.id ? null : pack.id)}
                                    className="w-full flex items-center justify-between p-3 hover:bg-bg-elevated transition-colors text-left"
                                >
                                    <div>
                                        <p className="text-text-primary text-sm font-medium">{pack.name}</p>
                                        <p className="text-text-muted text-xs">
                                            {pack.stems?.length || 0} stems
                                            {pack.genre && ` · ${pack.genre}`}
                                        </p>
                                    </div>
                                    <svg
                                        className={`w-4 h-4 text-text-muted transition-transform ${
                                            expandedPack === pack.id ? 'rotate-180' : ''
                                        }`}
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                        strokeWidth={2}
                                    >
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                                    </svg>
                                </button>

                                {/* Stem list (expanded) */}
                                {expandedPack === pack.id && (
                                    <div className="border-t border-border-subtle px-2 py-1">
                                        {pack.stems?.length === 0 ? (
                                            <p className="text-text-muted text-xs py-3 text-center">No stems in this pack.</p>
                                        ) : (
                                            pack.stems?.map((stem) => (
                                                <StemPickerCard
                                                    key={stem.id}
                                                    stem={stem}
                                                    packSlug={pack.slug}
                                                    onAdd={onAddStem}
                                                />
                                            ))
                                        )}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
