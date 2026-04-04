import { Link, usePage } from '@inertiajs/react';

export default function SoundscapeCard({ soundscape }) {
    const { auth } = usePage().props;
    const isOwner = auth.user?.id === soundscape.user_id;

    return (
        <div className="bg-bg-secondary rounded-2xl p-6 border border-border-subtle transition-all duration-250 hover:border-border-default hover:glow-teal relative">
            <Link href={`/s/${soundscape.slug}`} className="block">
                <div className="flex items-start justify-between mb-4">
                    <div>
                        <h3 className="font-heading font-semibold text-lg text-text-primary">{soundscape.name}</h3>
                        {soundscape.user && (
                            <p className="text-text-muted text-sm mt-1">by {soundscape.user.username}</p>
                        )}
                    </div>
                    <div className="text-right">
                        <span className="text-accent-teal font-mono text-sm font-semibold">
                            {soundscape.base_bpm} BPM
                        </span>
                    </div>
                </div>

                {soundscape.description && (
                    <p className="text-text-secondary text-sm mb-4 line-clamp-2">{soundscape.description}</p>
                )}

                <div className="flex items-center justify-between">
                    <div className="flex flex-wrap gap-1.5">
                        {(soundscape.tags || []).slice(0, 3).map((tag) => (
                            <span
                                key={tag.id}
                                className="bg-bg-tertiary text-text-muted text-xs px-2 py-0.5 rounded-md"
                            >
                                {tag.name}
                            </span>
                        ))}
                    </div>
                    {soundscape.favorites_count > 0 && (
                        <span className="text-text-muted text-xs">
                            {soundscape.favorites_count} fav{soundscape.favorites_count !== 1 && 's'}
                        </span>
                    )}
                </div>
            </Link>

            {isOwner && (
                <Link
                    href={`/soundscapes/${soundscape.slug}/edit`}
                    className="absolute top-4 right-4 text-text-muted hover:text-accent-teal transition-colors p-1"
                    title="Edit soundscape"
                    onClick={(e) => e.stopPropagation()}
                >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125" />
                    </svg>
                </Link>
            )}
        </div>
    );
}
