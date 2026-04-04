import { usePage, router } from '@inertiajs/react';
import { useState } from 'react';
import AppLayout from '../Layouts/AppLayout';
import SoundscapeCard from '../Components/SoundscapeCard';
import PackCard from '../Components/PackCard';

export default function Explore() {
    const { soundscapes, packs, search: initialSearch } = usePage().props;
    const [tab, setTab] = useState('soundscapes');
    const [search, setSearch] = useState(initialSearch || '');
    const [debounceTimer, setDebounceTimer] = useState(null);

    function handleSearch(value) {
        setSearch(value);
        if (debounceTimer) clearTimeout(debounceTimer);
        setDebounceTimer(setTimeout(() => {
            router.get('/explore', value ? { search: value } : {}, {
                preserveState: true,
                preserveScroll: true,
            });
        }, 300));
    }

    const items = tab === 'soundscapes' ? soundscapes : packs;

    return (
        <AppLayout>
            <div className="max-w-7xl mx-auto px-6 py-12">
                <div className="mb-10">
                    <h1 className="font-heading text-4xl font-bold mb-4">Explore</h1>
                    <p className="text-text-secondary text-lg">
                        Discover soundscapes and stem packs from the community.
                    </p>
                </div>

                {/* Search + Tabs */}
                <div className="flex flex-col md:flex-row gap-4 mb-8">
                    <input
                        type="text"
                        placeholder="Search..."
                        value={search}
                        onChange={(e) => handleSearch(e.target.value)}
                        className="flex-1 bg-bg-tertiary text-text-primary border border-border-default rounded-xl px-4 py-3 text-sm placeholder-text-muted focus:outline-none focus:border-accent-teal transition-colors"
                    />
                    <div className="flex bg-bg-secondary rounded-xl border border-border-subtle p-1">
                        <button
                            onClick={() => setTab('soundscapes')}
                            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all duration-250 ${
                                tab === 'soundscapes'
                                    ? 'bg-bg-elevated text-text-primary'
                                    : 'text-text-muted hover:text-text-secondary'
                            }`}
                        >
                            Soundscapes
                        </button>
                        <button
                            onClick={() => setTab('packs')}
                            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all duration-250 ${
                                tab === 'packs'
                                    ? 'bg-bg-elevated text-text-primary'
                                    : 'text-text-muted hover:text-text-secondary'
                            }`}
                        >
                            Stem Packs
                        </button>
                    </div>
                </div>

                {/* Results */}
                {items.data.length === 0 ? (
                    <div className="text-center py-20">
                        <p className="text-text-muted text-lg">No results found</p>
                        <p className="text-text-muted text-sm mt-2">
                            {search ? 'Try a different search term.' : 'Nothing here yet. Be the first to share!'}
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {items.data.map((item) =>
                            tab === 'soundscapes' ? (
                                <SoundscapeCard key={item.id} soundscape={item} />
                            ) : (
                                <PackCard key={item.id} pack={item} />
                            )
                        )}
                    </div>
                )}
            </div>
        </AppLayout>
    );
}
