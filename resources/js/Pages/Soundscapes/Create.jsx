import AppLayout from '../../Layouts/AppLayout';

export default function Create() {
    return (
        <AppLayout>
            <div className="max-w-5xl mx-auto px-6 py-12">
                <h1 className="font-heading text-3xl font-bold mb-4">Create Soundscape</h1>
                <p className="text-text-secondary mb-8">
                    The soundscape designer will be available here — shape volume and speed curves, preview in real time with Web Audio.
                </p>
                <div className="bg-bg-secondary rounded-2xl border border-border-subtle p-20 text-center">
                    <div className="w-16 h-16 rounded-2xl bg-bg-tertiary mx-auto mb-6 flex items-center justify-center">
                        <span className="text-2xl text-accent-teal">~</span>
                    </div>
                    <p className="text-text-muted text-lg font-heading font-medium mb-2">Soundscape Designer</p>
                    <p className="text-text-muted text-sm">Coming soon</p>
                </div>
            </div>
        </AppLayout>
    );
}
