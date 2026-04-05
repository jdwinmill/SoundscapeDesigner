import { Link, usePage } from '@inertiajs/react';
import { useState } from 'react';
import AppLayout from '../../Layouts/AppLayout';
import apiFetch from '../../lib/apiFetch';

async function apiPost(url, body = {}) {
    return apiFetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
}

export default function Show() {
    const { soundscape, auth, isFavorited } = usePage().props;
    const [favorited, setFavorited] = useState(isFavorited || false);
    const [favCount, setFavCount] = useState(soundscape.favorites_count || 0);

    async function toggleFavorite() {
        const res = await apiPost('/api/favorites/toggle', {
            type: 'soundscape',
            id: soundscape.id,
        });
        if (res.ok) {
            const json = await res.json();
            setFavorited(json.favorited);
            setFavCount((c) => (json.favorited ? c + 1 : c - 1));
        }
    }

    async function cloneSoundscape() {
        const res = await apiPost(`/api/soundscapes/${soundscape.slug}/clone`);
        if (res.ok) {
            window.location.href = '/dashboard';
        }
    }

    return (
        <AppLayout>
            <div className="max-w-5xl mx-auto px-6 py-12">
                {/* Header */}
                <div className="mb-10">
                    <h1 className="font-heading text-4xl font-bold mb-2">{soundscape.name}</h1>
                    <div className="flex items-center gap-3 mb-4">
                        {soundscape.user && (
                            <Link
                                href={`/u/${soundscape.user.username}`}
                                className="text-text-secondary text-sm hover:text-accent-teal transition-colors"
                            >
                                by {soundscape.user.username}
                            </Link>
                        )}
                        <span className="text-text-muted text-sm">&middot;</span>
                        <span className="text-accent-teal font-mono text-sm font-semibold">
                            {soundscape.base_bpm} BPM
                        </span>
                    </div>

                    {soundscape.description && (
                        <p className="text-text-secondary max-w-2xl mb-6">{soundscape.description}</p>
                    )}

                    {soundscape.tags?.length > 0 && (
                        <div className="flex flex-wrap gap-2 mb-6">
                            {soundscape.tags.map((tag) => (
                                <span key={tag.id} className="bg-bg-tertiary text-text-muted text-xs px-2.5 py-1 rounded-md">
                                    {tag.name}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex flex-wrap gap-3">
                        {auth?.user && (
                            <>
                                {soundscape.user_id === auth.user.id && (
                                    <Link
                                        href={`/soundscapes/${soundscape.slug}/edit`}
                                        className="px-5 py-2.5 rounded-xl text-sm font-medium bg-gradient-accent text-text-inverse transition-all duration-250 hover:opacity-90"
                                    >
                                        Edit
                                    </Link>
                                )}
                                <button
                                    onClick={toggleFavorite}
                                    className={`px-5 py-2.5 rounded-xl text-sm font-medium border transition-all duration-250 ${
                                        favorited
                                            ? 'bg-highlight-amber/10 border-highlight-amber text-highlight-amber'
                                            : 'bg-bg-elevated border-border-default text-text-secondary hover:border-highlight-amber'
                                    }`}
                                >
                                    {favorited ? 'Favorited' : 'Favorite'} ({favCount})
                                </button>
                                {soundscape.is_public && soundscape.user_id !== auth.user.id && (
                                    <button
                                        onClick={cloneSoundscape}
                                        className="px-5 py-2.5 rounded-xl text-sm font-medium bg-bg-elevated border border-border-default text-text-secondary hover:border-accent-teal transition-all duration-250"
                                    >
                                        Clone to my account
                                    </button>
                                )}
                            </>
                        )}
                    </div>
                </div>

                {/* Config / Stems in this soundscape */}
                <section>
                    <h2 className="font-heading text-xl font-semibold mb-4">Stems in this mix</h2>
                    <div className="bg-bg-secondary rounded-2xl border border-border-subtle divide-y divide-border-subtle">
                        {soundscape.config?.stems?.length === 0 ? (
                            <p className="text-text-muted text-center py-8">No stems configured.</p>
                        ) : (
                            soundscape.config?.stems?.map((stem, i) => (
                                <div key={i} className="flex items-center justify-between p-5">
                                    <div>
                                        <p className="text-text-primary font-medium text-sm">{stem.file}</p>
                                        <p className="text-text-muted text-xs mt-1">
                                            BPM range: {stem.bpmRange?.[0]} – {stem.bpmRange?.[1]}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-4 text-xs text-text-muted">
                                        <span>Vol: {(stem.volume * 100).toFixed(0)}%</span>
                                        <span>Speed: {stem.speed}x</span>
                                        <span>Fade: {stem.fadeIn}↑ {stem.fadeOut}↓</span>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </section>
            </div>
        </AppLayout>
    );
}
