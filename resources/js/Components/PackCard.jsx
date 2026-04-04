import { Link } from '@inertiajs/react';

export default function PackCard({ pack }) {
    return (
        <Link
            href={`/packs/${pack.slug}`}
            className="bg-bg-secondary rounded-2xl p-6 border border-border-subtle transition-all duration-250 hover:border-border-default hover:glow-violet block"
        >
            <div className="flex items-start justify-between mb-3">
                <h3 className="font-heading font-semibold text-lg text-text-primary">{pack.name}</h3>
                {pack.genre && (
                    <span className="bg-bg-tertiary text-accent-violet text-xs font-medium px-2.5 py-1 rounded-lg">
                        {pack.genre}
                    </span>
                )}
            </div>

            {pack.user && (
                <p className="text-text-muted text-sm mb-3">by {pack.user.username}</p>
            )}

            {pack.mood_summary && (
                <p className="text-text-secondary text-sm mb-4 line-clamp-2">{pack.mood_summary}</p>
            )}

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-text-muted text-xs">
                    <span>{pack.stems_count ?? pack.stems?.length ?? 0} stems</span>
                    <span className="font-mono">{pack.bpm_center} BPM</span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                    {(pack.tags || []).slice(0, 2).map((tag) => (
                        <span
                            key={tag.id}
                            className="bg-bg-tertiary text-text-muted text-xs px-2 py-0.5 rounded-md"
                        >
                            {tag.name}
                        </span>
                    ))}
                </div>
            </div>
        </Link>
    );
}
