import { usePage } from '@inertiajs/react';
import AppLayout from '../../Layouts/AppLayout';
import SoundscapeCard from '../../Components/SoundscapeCard';
import PackCard from '../../Components/PackCard';

export default function Profile() {
    const { profile, packs, soundscapes } = usePage().props;

    return (
        <AppLayout>
            <div className="max-w-7xl mx-auto px-6 py-12">
                {/* Profile header */}
                <div className="flex items-center gap-5 mb-12">
                    <div className="w-20 h-20 rounded-full bg-bg-elevated border border-border-default flex items-center justify-center">
                        <span className="text-2xl font-bold text-accent-teal">
                            {profile.name.charAt(0).toUpperCase()}
                        </span>
                    </div>
                    <div>
                        <h1 className="font-heading text-3xl font-bold">{profile.name}</h1>
                        <p className="text-text-muted text-sm">@{profile.username}</p>
                        <p className="text-text-muted text-xs mt-1">
                            Joined {new Date(profile.joined).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                        </p>
                    </div>
                </div>

                {/* Packs */}
                {packs.length > 0 && (
                    <section className="mb-16">
                        <h2 className="font-heading text-2xl font-semibold mb-6">Stem Packs</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {packs.map((pack) => (
                                <PackCard key={pack.id} pack={pack} />
                            ))}
                        </div>
                    </section>
                )}

                {/* Soundscapes */}
                {soundscapes.length > 0 && (
                    <section>
                        <h2 className="font-heading text-2xl font-semibold mb-6">Soundscapes</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {soundscapes.map((s) => (
                                <SoundscapeCard key={s.id} soundscape={s} />
                            ))}
                        </div>
                    </section>
                )}

                {packs.length === 0 && soundscapes.length === 0 && (
                    <div className="text-center py-20">
                        <p className="text-text-muted text-lg">Nothing shared yet</p>
                        <p className="text-text-muted text-sm mt-2">
                            This user hasn't published any packs or soundscapes.
                        </p>
                    </div>
                )}
            </div>
        </AppLayout>
    );
}
