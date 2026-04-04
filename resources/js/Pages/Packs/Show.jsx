import { Link, usePage, router } from '@inertiajs/react';
import { useState, useRef } from 'react';
import AppLayout from '../../Layouts/AppLayout';

function StemRow({ stem }) {
    return (
        <div className="flex items-center justify-between py-4 border-b border-border-subtle last:border-0">
            <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-lg bg-bg-tertiary flex items-center justify-center">
                    <span className="text-accent-violet text-xs font-semibold">
                        {stem.role_type?.[0]?.toUpperCase() || '?'}
                    </span>
                </div>
                <div>
                    <p className="text-text-primary font-medium text-sm">{stem.name}</p>
                    <p className="text-text-muted text-xs">
                        {stem.role_type} &middot; {stem.role_layer} &middot; {stem.bpm} BPM
                    </p>
                </div>
            </div>
            <div className="flex items-center gap-4">
                <div className="hidden md:flex items-center gap-3 text-xs text-text-muted">
                    <span title="Intensity">E {(stem.intensity * 100).toFixed(0)}%</span>
                    <span title="Brightness">B {(stem.brightness * 100).toFixed(0)}%</span>
                    <span title="Warmth">W {(stem.warmth * 100).toFixed(0)}%</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-md ${
                    stem.key === 'none'
                        ? 'bg-bg-tertiary text-text-muted'
                        : 'bg-bg-tertiary text-accent-teal'
                }`}>
                    {stem.key}
                </span>
            </div>
        </div>
    );
}

function StemUpload({ packSlug }) {
    const fileRef = useRef(null);
    const [uploading, setUploading] = useState(false);
    const [name, setName] = useState('');
    const [error, setError] = useState('');

    async function handleUpload(e) {
        e.preventDefault();
        const file = fileRef.current?.files[0];
        if (!file || !name) return;

        setUploading(true);
        setError('');

        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', name);

        try {
            const res = await fetch(`/api/stem-packs/${packSlug}/stems`, {
                method: 'POST',
                headers: {
                    'X-XSRF-TOKEN': decodeURIComponent(
                        document.cookie.match(/XSRF-TOKEN=([^;]+)/)?.[1] || ''
                    ),
                },
                credentials: 'same-origin',
                body: formData,
            });

            if (res.ok) {
                setName('');
                fileRef.current.value = '';
                router.reload({ only: ['pack'] });
            } else if (res.status === 422) {
                const json = await res.json();
                const firstError = Object.values(json.errors || {})[0];
                setError(firstError?.[0] || 'Validation failed');
            } else {
                setError('Upload failed');
            }
        } catch {
            setError('Upload failed');
        } finally {
            setUploading(false);
        }
    }

    return (
        <form onSubmit={handleUpload} className="bg-bg-secondary rounded-2xl border border-border-subtle p-6">
            <h3 className="font-heading font-semibold text-lg mb-4">Upload Stem</h3>
            <div className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">Stem name</label>
                    <input
                        type="text"
                        placeholder="e.g. Kick Drum"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        className="w-full bg-bg-tertiary text-text-primary border border-border-default rounded-xl px-4 py-3 text-sm placeholder-text-muted focus:outline-none focus:border-accent-teal transition-colors"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-2">Audio file</label>
                    <input
                        ref={fileRef}
                        type="file"
                        accept=".wav,.mp3,.ogg,.flac,.aiff"
                        className="w-full text-sm text-text-muted file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-bg-tertiary file:text-text-secondary file:font-medium file:cursor-pointer hover:file:bg-bg-elevated"
                    />
                </div>
                {error && <p className="text-sm text-error">{error}</p>}
                <button
                    type="submit"
                    disabled={uploading || !name}
                    className="bg-gradient-accent text-text-inverse font-semibold px-6 py-2.5 rounded-xl text-sm transition-all duration-250 hover:opacity-90 disabled:opacity-50"
                >
                    {uploading ? 'Uploading...' : 'Upload'}
                </button>
            </div>
        </form>
    );
}

export default function Show() {
    const { pack, isOwner } = usePage().props;

    return (
        <AppLayout>
            <div className="max-w-5xl mx-auto px-6 py-12">
                {/* Header */}
                <div className="mb-10">
                    <div className="flex items-start justify-between">
                        <div>
                            <h1 className="font-heading text-4xl font-bold mb-2">{pack.name}</h1>
                            {pack.user && (
                                <Link
                                    href={`/u/${pack.user.username}`}
                                    className="text-text-secondary text-sm hover:text-accent-teal transition-colors"
                                >
                                    by {pack.user.username}
                                </Link>
                            )}
                        </div>
                        {pack.genre && (
                            <span className="bg-bg-tertiary text-accent-violet text-sm font-medium px-3 py-1.5 rounded-lg">
                                {pack.genre}
                            </span>
                        )}
                    </div>

                    {pack.mood_summary && (
                        <p className="text-text-secondary mt-4 max-w-2xl">{pack.mood_summary}</p>
                    )}

                    <div className="flex flex-wrap gap-4 mt-6 text-sm text-text-muted">
                        <span className="font-mono">{pack.bpm_center} BPM</span>
                        {pack.key_center && <span>Key: {pack.key_center}</span>}
                        <span>{pack.stems?.length || 0} stems</span>
                    </div>

                    {pack.tags?.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-4">
                            {pack.tags.map((tag) => (
                                <span key={tag.id} className="bg-bg-tertiary text-text-muted text-xs px-2.5 py-1 rounded-md">
                                    {tag.name}
                                </span>
                            ))}
                        </div>
                    )}
                </div>

                {/* Owner: stem upload */}
                {isOwner && (
                    <section className="mb-10">
                        <StemUpload packSlug={pack.slug} />
                    </section>
                )}

                {/* Stems list */}
                <section>
                    <h2 className="font-heading text-xl font-semibold mb-4">Stems</h2>
                    <div className="bg-bg-secondary rounded-2xl border border-border-subtle p-6">
                        {pack.stems?.length === 0 ? (
                            <p className="text-text-muted text-center py-8">No stems in this pack yet.</p>
                        ) : (
                            pack.stems?.map((stem) => <StemRow key={stem.id} stem={stem} />)
                        )}
                    </div>
                </section>
            </div>
        </AppLayout>
    );
}
