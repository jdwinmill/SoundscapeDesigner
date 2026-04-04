import { Link } from '@inertiajs/react';
import AppLayout from '../Layouts/AppLayout';

function HeroSection() {
    return (
        <section className="relative overflow-hidden">
            {/* Background glow */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full opacity-10"
                 style={{ background: 'radial-gradient(circle, var(--color-accent-teal) 0%, transparent 70%)' }} />
            <div className="absolute top-1/3 right-1/4 w-[600px] h-[600px] rounded-full opacity-10"
                 style={{ background: 'radial-gradient(circle, var(--color-accent-violet) 0%, transparent 70%)' }} />

            <div className="relative max-w-7xl mx-auto px-6 pt-24 pb-20 md:pt-36 md:pb-32">
                <div className="max-w-3xl">
                    <h1 className="font-heading text-5xl md:text-7xl font-bold leading-tight mb-6">
                        Your run.<br />
                        <span className="text-gradient">Your sound.</span>
                    </h1>
                    <p className="text-text-secondary text-lg md:text-xl leading-relaxed mb-10 max-w-xl">
                        Design soundscapes that react to your pace. Upload stems, shape volume and speed curves, and let the music move with you.
                    </p>
                    <div className="flex flex-wrap gap-4">
                        <Link
                            href="/register"
                            className="bg-gradient-accent text-text-inverse font-semibold px-8 py-4 rounded-xl text-lg transition-all duration-250 hover:opacity-90 hover:glow-teal"
                        >
                            Start creating
                        </Link>
                        <Link
                            href="/explore"
                            className="bg-bg-elevated text-text-primary font-medium px-8 py-4 rounded-xl text-lg border border-border-default transition-all duration-250 hover:border-accent-teal"
                        >
                            Explore soundscapes
                        </Link>
                    </div>
                </div>
            </div>
        </section>
    );
}

function FeatureCard({ icon, title, description }) {
    return (
        <div className="bg-bg-secondary rounded-2xl p-8 border border-border-subtle transition-all duration-250 hover:border-border-default hover:glow-teal">
            <div className="w-12 h-12 rounded-xl bg-bg-tertiary flex items-center justify-center mb-5 text-2xl">
                {icon}
            </div>
            <h3 className="font-heading font-semibold text-xl mb-3">{title}</h3>
            <p className="text-text-secondary text-sm leading-relaxed">{description}</p>
        </div>
    );
}

function FeaturesSection() {
    return (
        <section className="max-w-7xl mx-auto px-6 py-20">
            <div className="text-center mb-16">
                <h2 className="font-heading text-3xl md:text-4xl font-bold mb-4">
                    How it works
                </h2>
                <p className="text-text-secondary text-lg max-w-2xl mx-auto">
                    Three steps to a soundscape that breathes with your stride.
                </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <FeatureCard
                    icon={<span className="text-accent-teal">1</span>}
                    title="Upload your stems"
                    description="Bring your audio — loops, textures, beats. Tag them with mood, energy, and musical metadata so the system knows what they are."
                />
                <FeatureCard
                    icon={<span className="text-accent-violet">2</span>}
                    title="Shape your curves"
                    description="Design volume and speed curves that map to BPM ranges. As your pace changes, your mix adapts — louder drums at tempo, ambient pads for cooldown."
                />
                <FeatureCard
                    icon={<span className="text-highlight-amber">3</span>}
                    title="Run with it"
                    description="Export your soundscape to the mobile app. GPS tracks your pace, translates it to BPM, and your mix reacts in real time."
                />
            </div>
        </section>
    );
}

function CTASection() {
    return (
        <section className="max-w-7xl mx-auto px-6 py-20">
            <div className="relative rounded-3xl overflow-hidden">
                <div className="absolute inset-0 bg-gradient-accent opacity-10" />
                <div className="relative glass rounded-3xl p-12 md:p-20 text-center">
                    <h2 className="font-heading text-3xl md:text-4xl font-bold mb-4">
                        Ready to find your flow?
                    </h2>
                    <p className="text-text-secondary text-lg mb-8 max-w-xl mx-auto">
                        Join the community of runners designing their own sonic experiences.
                    </p>
                    <Link
                        href="/register"
                        className="inline-block bg-gradient-accent text-text-inverse font-semibold px-8 py-4 rounded-xl text-lg transition-all duration-250 hover:opacity-90"
                    >
                        Create your account
                    </Link>
                </div>
            </div>
        </section>
    );
}

export default function Home() {
    return (
        <AppLayout>
            <HeroSection />
            <FeaturesSection />
            <CTASection />
        </AppLayout>
    );
}
