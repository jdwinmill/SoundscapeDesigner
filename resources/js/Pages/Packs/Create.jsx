import { router } from '@inertiajs/react';
import { useState, useRef, useCallback } from 'react';
import AppLayout from '../../Layouts/AppLayout';
import FormInput from '../../Components/FormInput';

function csrfToken() {
    return decodeURIComponent(
        document.cookie.match(/XSRF-TOKEN=([^;]+)/)?.[1] || ''
    );
}

function DropZone({ onFiles, disabled }) {
    const [dragOver, setDragOver] = useState(false);
    const inputRef = useRef(null);

    function handleDrop(e) {
        e.preventDefault();
        setDragOver(false);
        if (disabled) return;
        const files = Array.from(e.dataTransfer.files).filter((f) =>
            /\.(wav|mp3|ogg|flac|aiff)$/i.test(f.name)
        );
        if (files.length) onFiles(files);
    }

    function handleChange(e) {
        const files = Array.from(e.target.files);
        if (files.length) onFiles(files);
        e.target.value = '';
    }

    return (
        <div
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => !disabled && inputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-250 ${
                disabled
                    ? 'border-border-subtle opacity-50 cursor-not-allowed'
                    : dragOver
                        ? 'border-accent-teal bg-accent-teal/5'
                        : 'border-border-default hover:border-border-strong'
            }`}
        >
            <div className="w-12 h-12 rounded-xl bg-bg-tertiary mx-auto mb-4 flex items-center justify-center">
                <svg className="w-6 h-6 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
            </div>
            <p className="text-text-secondary font-medium mb-1">
                Drop audio files here
            </p>
            <p className="text-text-muted text-sm">
                or click to browse &middot; WAV, MP3, OGG, FLAC, AIFF
            </p>
            <input
                ref={inputRef}
                type="file"
                multiple
                accept=".wav,.mp3,.ogg,.flac,.aiff"
                onChange={handleChange}
                className="hidden"
            />
        </div>
    );
}

function StemItem({ stem, onRemove }) {
    const statusColors = {
        pending: 'text-text-muted',
        uploading: 'text-highlight-amber',
        done: 'text-success',
        error: 'text-error',
    };

    const statusLabels = {
        pending: 'Waiting...',
        uploading: 'Uploading...',
        done: 'Uploaded',
        error: stem.error || 'Failed',
    };

    return (
        <div className="flex items-center justify-between py-3 border-b border-border-subtle last:border-0">
            <div className="flex items-center gap-3 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-bg-tertiary flex items-center justify-center shrink-0">
                    {stem.status === 'uploading' ? (
                        <div className="w-4 h-4 border-2 border-highlight-amber border-t-transparent rounded-full animate-spin" />
                    ) : stem.status === 'done' ? (
                        <svg className="w-4 h-4 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                    ) : stem.status === 'error' ? (
                        <span className="text-error text-xs font-bold">!</span>
                    ) : (
                        <span className="text-text-muted text-xs">~</span>
                    )}
                </div>
                <div className="min-w-0">
                    <p className="text-text-primary text-sm font-medium truncate">{stem.name}</p>
                    <p className={`text-xs ${statusColors[stem.status]}`}>
                        {statusLabels[stem.status]}
                    </p>
                </div>
            </div>
            {(stem.status === 'pending' || stem.status === 'error') && (
                <button
                    onClick={() => onRemove(stem.id)}
                    className="text-text-muted hover:text-error text-sm shrink-0 ml-2"
                >
                    &times;
                </button>
            )}
        </div>
    );
}

export default function Create() {
    const [packName, setPackName] = useState('');
    const [genre, setGenre] = useState('');
    const [tagInput, setTagInput] = useState('');
    const [tags, setTags] = useState([]);
    const [stems, setStems] = useState([]);
    const [packSlug, setPackSlug] = useState(null);
    const [creating, setCreating] = useState(false);
    const [error, setError] = useState('');
    const [showOptional, setShowOptional] = useState(false);

    let nextId = useRef(0);

    function addTag(e) {
        if (e.key === 'Enter' && tagInput.trim()) {
            e.preventDefault();
            if (!tags.includes(tagInput.trim())) {
                setTags([...tags, tagInput.trim()]);
            }
            setTagInput('');
        }
    }

    function removeTag(tag) {
        setTags(tags.filter((t) => t !== tag));
    }

    function handleFiles(files) {
        const newStems = files.map((file) => ({
            id: `stem-${nextId.current++}`,
            file,
            name: file.name.replace(/\.[^.]+$/, ''),
            status: 'pending',
            error: null,
        }));
        setStems((prev) => [...prev, ...newStems]);
    }

    function removeStem(id) {
        setStems((prev) => prev.filter((s) => s.id !== id));
    }

    const uploadStem = useCallback(async (slug, stem) => {
        setStems((prev) =>
            prev.map((s) => (s.id === stem.id ? { ...s, status: 'uploading' } : s))
        );

        const formData = new FormData();
        formData.append('file', stem.file);
        formData.append('name', stem.name);

        try {
            const res = await fetch(`/api/stem-packs/${slug}/stems`, {
                method: 'POST',
                headers: { 'X-XSRF-TOKEN': csrfToken() },
                credentials: 'same-origin',
                body: formData,
            });

            if (res.ok) {
                setStems((prev) =>
                    prev.map((s) => (s.id === stem.id ? { ...s, status: 'done' } : s))
                );
            } else {
                const json = await res.json().catch(() => ({}));
                const msg = Object.values(json.errors || {})[0]?.[0] || 'Upload failed';
                setStems((prev) =>
                    prev.map((s) => (s.id === stem.id ? { ...s, status: 'error', error: msg } : s))
                );
            }
        } catch {
            setStems((prev) =>
                prev.map((s) => (s.id === stem.id ? { ...s, status: 'error', error: 'Network error' } : s))
            );
        }
    }, []);

    async function handleSubmit(e) {
        e.preventDefault();
        if (!packName.trim()) return;

        setCreating(true);
        setError('');

        try {
            // Step 1: Create the pack
            const body = { name: packName.trim() };
            if (genre.trim()) body.genre = genre.trim();
            if (tags.length) body.tags = tags;

            const res = await fetch('/api/stem-packs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-XSRF-TOKEN': csrfToken(),
                },
                credentials: 'same-origin',
                body: JSON.stringify(body),
            });

            if (!res.ok) {
                const json = await res.json().catch(() => ({}));
                setError(json.errors?.name?.[0] || 'Failed to create pack');
                setCreating(false);
                return;
            }

            const pack = await res.json();
            setPackSlug(pack.slug);

            // Step 2: Upload all pending stems
            const pending = stems.filter((s) => s.status === 'pending');
            await Promise.all(pending.map((stem) => uploadStem(pack.slug, stem)));

            // Step 3: Redirect to the pack
            router.visit(`/packs/${pack.slug}`);
        } catch {
            setError('Something went wrong');
            setCreating(false);
        }
    }

    const pendingCount = stems.filter((s) => s.status === 'pending').length;
    const uploadingCount = stems.filter((s) => s.status === 'uploading').length;
    const isWorking = creating || uploadingCount > 0;

    return (
        <AppLayout>
            <div className="max-w-2xl mx-auto px-6 py-12">
                <h1 className="font-heading text-3xl font-bold mb-2">Create Stem Pack</h1>
                <p className="text-text-secondary mb-8">
                    Name your pack, drop your stems, and you're done.
                </p>

                <form onSubmit={handleSubmit} className="space-y-6">
                    {/* Pack name */}
                    <div className="bg-bg-secondary rounded-2xl p-6 border border-border-subtle space-y-4">
                        <FormInput
                            label="Pack name"
                            type="text"
                            placeholder="e.g. Deep Ambient Loops"
                            value={packName}
                            onChange={(e) => setPackName(e.target.value)}
                            autoFocus
                        />

                        {/* Optional metadata toggle */}
                        <button
                            type="button"
                            onClick={() => setShowOptional(!showOptional)}
                            className="text-sm text-text-muted hover:text-text-secondary transition-colors"
                        >
                            {showOptional ? '- Hide options' : '+ Genre, tags (optional)'}
                        </button>

                        {showOptional && (
                            <div className="space-y-4 pt-2">
                                <FormInput
                                    label="Genre"
                                    type="text"
                                    placeholder="e.g. ambient, electronic, lo-fi"
                                    value={genre}
                                    onChange={(e) => setGenre(e.target.value)}
                                />
                                <div>
                                    <label className="block text-sm font-medium text-text-secondary mb-2">Tags</label>
                                    <div className="flex flex-wrap gap-2 mb-2">
                                        {tags.map((tag) => (
                                            <span
                                                key={tag}
                                                className="bg-bg-tertiary text-text-secondary text-xs px-2.5 py-1 rounded-md flex items-center gap-1.5"
                                            >
                                                {tag}
                                                <button type="button" onClick={() => removeTag(tag)} className="text-text-muted hover:text-error">
                                                    &times;
                                                </button>
                                            </span>
                                        ))}
                                    </div>
                                    <input
                                        type="text"
                                        placeholder="Type a tag and press Enter"
                                        value={tagInput}
                                        onChange={(e) => setTagInput(e.target.value)}
                                        onKeyDown={addTag}
                                        className="w-full bg-bg-tertiary text-text-primary border border-border-default rounded-xl px-4 py-3 text-sm placeholder-text-muted focus:outline-none focus:border-accent-teal transition-colors"
                                    />
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Stem drop zone */}
                    <DropZone onFiles={handleFiles} disabled={isWorking} />

                    {/* Stem list */}
                    {stems.length > 0 && (
                        <div className="bg-bg-secondary rounded-2xl border border-border-subtle p-6">
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-heading font-semibold text-sm text-text-secondary">
                                    {stems.length} stem{stems.length !== 1 && 's'}
                                </h3>
                                {pendingCount > 0 && !isWorking && (
                                    <button
                                        type="button"
                                        onClick={() => setStems([])}
                                        className="text-xs text-text-muted hover:text-error transition-colors"
                                    >
                                        Clear all
                                    </button>
                                )}
                            </div>
                            {stems.map((stem) => (
                                <StemItem
                                    key={stem.id}
                                    stem={stem}
                                    onRemove={removeStem}
                                />
                            ))}
                        </div>
                    )}

                    {error && (
                        <p className="text-sm text-error">{error}</p>
                    )}

                    {/* Submit */}
                    <button
                        type="submit"
                        disabled={isWorking || !packName.trim()}
                        className="w-full bg-gradient-accent text-text-inverse font-semibold py-3.5 rounded-xl text-lg transition-all duration-250 hover:opacity-90 disabled:opacity-50"
                    >
                        {isWorking
                            ? uploadingCount > 0
                                ? `Uploading ${uploadingCount} stem${uploadingCount !== 1 ? 's' : ''}...`
                                : 'Creating pack...'
                            : stems.length > 0
                                ? `Create pack with ${stems.length} stem${stems.length !== 1 ? 's' : ''}`
                                : 'Create empty pack'
                        }
                    </button>
                </form>
            </div>
        </AppLayout>
    );
}
