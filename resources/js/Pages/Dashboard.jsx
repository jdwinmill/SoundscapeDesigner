import { Link, usePage } from '@inertiajs/react';
import AppLayout from '../Layouts/AppLayout';
import SoundscapeCard from '../Components/SoundscapeCard';
import PackCard from '../Components/PackCard';

function EmptyState({ title, description, action, actionHref }) {
    return (
        <div className="text-center py-12 bg-bg-secondary rounded-2xl border border-border-subtle">
            <p className="text-text-secondary font-medium mb-2">{title}</p>
            <p className="text-text-muted text-sm mb-6">{description}</p>
            {action && (
                <Link
                    href={actionHref}
                    className="inline-block bg-gradient-accent text-text-inverse font-semibold px-6 py-3 rounded-xl text-sm transition-all duration-250 hover:opacity-90"
                >
                    {action}
                </Link>
            )}
        </div>
    );
}

export default function Dashboard() {
    const { auth, packs, soundscapes } = usePage().props;

    return (
        <AppLayout>
            <div className="max-w-7xl mx-auto px-6 py-12">
                <div className="flex items-center justify-between mb-10">
                    <div>
                        <h1 className="font-heading text-4xl font-bold mb-2">Dashboard</h1>
                        <p className="text-text-secondary">
                            Welcome back, {auth.user.name}
                        </p>
                    </div>
                </div>

                {/* Stem Packs */}
                <section className="mb-16">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="font-heading text-2xl font-semibold">Your Stem Packs</h2>
                        <Link
                            href="/packs/create"
                            className="bg-bg-elevated text-text-primary font-medium px-4 py-2 rounded-xl text-sm border border-border-default transition-all duration-250 hover:border-accent-violet"
                        >
                            + New Pack
                        </Link>
                    </div>
                    {packs.length === 0 ? (
                        <EmptyState
                            title="No stem packs yet"
                            description="Upload your first audio stems to get started."
                            action="Create a pack"
                            actionHref="/packs/create"
                        />
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {packs.map((pack) => (
                                <PackCard key={pack.id} pack={pack} />
                            ))}
                        </div>
                    )}
                </section>

                {/* Soundscapes */}
                <section>
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="font-heading text-2xl font-semibold">Your Soundscapes</h2>
                        <Link
                            href="/soundscapes/create"
                            className="bg-bg-elevated text-text-primary font-medium px-4 py-2 rounded-xl text-sm border border-border-default transition-all duration-250 hover:border-accent-teal"
                        >
                            + New Soundscape
                        </Link>
                    </div>
                    {soundscapes.length === 0 ? (
                        <EmptyState
                            title="No soundscapes yet"
                            description="Create a soundscape by combining stems with BPM-reactive curves."
                            action="Create a soundscape"
                            actionHref="/soundscapes/create"
                        />
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {soundscapes.map((s) => (
                                <SoundscapeCard key={s.id} soundscape={s} />
                            ))}
                        </div>
                    )}
                </section>
            </div>
        </AppLayout>
    );
}
