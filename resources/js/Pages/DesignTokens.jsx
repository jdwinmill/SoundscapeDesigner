import { colors, typography, effects, radii } from '../lib/tokens';

const ColorSwatch = ({ name, value }) => (
    <div className="flex items-center gap-3">
        <div
            className="w-12 h-12 rounded-lg border border-border-default shrink-0"
            style={{ backgroundColor: value }}
        />
        <div>
            <p className="text-sm font-medium text-text-primary">{name}</p>
            <p className="text-xs text-text-muted font-mono">{value}</p>
        </div>
    </div>
);

const GradientSwatch = ({ name, value }) => (
    <div className="flex items-center gap-3">
        <div
            className="w-12 h-12 rounded-lg shrink-0"
            style={{ background: value }}
        />
        <div>
            <p className="text-sm font-medium text-text-primary">{name}</p>
        </div>
    </div>
);

const Section = ({ title, children }) => (
    <section className="mb-12">
        <h2 className="text-2xl font-semibold mb-6 font-heading">{title}</h2>
        {children}
    </section>
);

export default function DesignTokens() {
    return (
        <div className="min-h-screen bg-bg-primary p-8 max-w-6xl mx-auto">
            <h1 className="text-4xl font-bold font-heading mb-2">
                <span className="text-gradient">StrideSoundscape</span> Design Tokens
            </h1>
            <p className="text-text-secondary mb-12">
                Single source of truth for the visual system. Adjust in{' '}
                <code className="text-accent-teal text-sm">resources/js/lib/tokens.js</code> and{' '}
                <code className="text-accent-teal text-sm">resources/css/app.css</code>.
            </p>

            {/* Colors */}
            <Section title="Backgrounds">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(colors.bg).map(([name, value]) => (
                        <ColorSwatch key={name} name={`bg.${name}`} value={value} />
                    ))}
                </div>
            </Section>

            <Section title="Accent & Highlight">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <ColorSwatch name="accent.teal" value={colors.accent.teal} />
                    <ColorSwatch name="accent.violet" value={colors.accent.violet} />
                    <GradientSwatch name="accent.gradient" value={colors.accent.gradient} />
                    <ColorSwatch name="highlight.amber" value={colors.highlight.amber} />
                    <ColorSwatch name="highlight.gold" value={colors.highlight.gold} />
                </div>
            </Section>

            <Section title="Text">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(colors.text).map(([name, value]) => (
                        <div key={name} className="flex items-center gap-3">
                            <p className="text-lg font-medium" style={{ color: value }}>
                                Aa
                            </p>
                            <div>
                                <p className="text-sm font-medium text-text-primary">text.{name}</p>
                                <p className="text-xs text-text-muted font-mono">{value}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </Section>

            <Section title="Semantic">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <ColorSwatch name="success" value={colors.success} />
                    <ColorSwatch name="warning" value={colors.warning} />
                    <ColorSwatch name="error" value={colors.error} />
                    <ColorSwatch name="info" value={colors.info} />
                </div>
            </Section>

            <Section title="Borders">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {Object.entries(colors.border).map(([name, value]) => (
                        <div key={name} className="p-4 rounded-lg" style={{ border: `2px solid ${value}` }}>
                            <p className="text-sm font-medium text-text-primary">border.{name}</p>
                            <p className="text-xs text-text-muted font-mono">{value}</p>
                        </div>
                    ))}
                </div>
            </Section>

            {/* Typography */}
            <Section title="Typography">
                <div className="space-y-6">
                    <div>
                        <p className="text-text-muted text-sm mb-2">Heading — Sora</p>
                        <p className="font-heading text-4xl font-bold">The quick brown fox</p>
                    </div>
                    <div>
                        <p className="text-text-muted text-sm mb-2">Body — Inter</p>
                        <p className="font-body text-lg">The quick brown fox jumps over the lazy dog</p>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
                        {Object.entries(typography.fontSize).map(([name, value]) => (
                            <div key={name}>
                                <p className="text-text-muted text-xs mb-1">{name} ({value})</p>
                                <p style={{ fontSize: value }} className="font-heading font-semibold">Stride</p>
                            </div>
                        ))}
                    </div>
                </div>
            </Section>

            {/* Radii */}
            <Section title="Border Radius">
                <div className="flex flex-wrap gap-4">
                    {Object.entries(radii).filter(([n]) => n !== 'none' && n !== 'full').map(([name, value]) => (
                        <div key={name} className="flex flex-col items-center gap-2">
                            <div
                                className="w-16 h-16 bg-bg-elevated border border-border-default"
                                style={{ borderRadius: value }}
                            />
                            <p className="text-xs text-text-muted">{name} ({value})</p>
                        </div>
                    ))}
                    <div className="flex flex-col items-center gap-2">
                        <div className="w-16 h-16 bg-bg-elevated border border-border-default rounded-full" />
                        <p className="text-xs text-text-muted">full</p>
                    </div>
                </div>
            </Section>

            {/* Effects */}
            <Section title="Glow Effects">
                <div className="flex flex-wrap gap-6">
                    {Object.entries(effects.glow).map(([name, value]) => (
                        <div
                            key={name}
                            className="w-24 h-24 rounded-xl bg-bg-elevated flex items-center justify-center"
                            style={{ boxShadow: value }}
                        >
                            <p className="text-xs text-text-secondary">{name}</p>
                        </div>
                    ))}
                </div>
            </Section>

            <Section title="Glass Morphism">
                <div className="relative h-32 rounded-xl overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-accent opacity-30" />
                    <div className="absolute inset-4 glass rounded-lg flex items-center justify-center">
                        <p className="text-text-primary font-medium">Glass panel over gradient</p>
                    </div>
                </div>
            </Section>

            <Section title="Shadows">
                <div className="flex flex-wrap gap-6">
                    {Object.entries(effects.shadow).map(([name, value]) => (
                        <div
                            key={name}
                            className="w-24 h-24 rounded-xl bg-bg-elevated flex items-center justify-center"
                            style={{ boxShadow: value }}
                        >
                            <p className="text-xs text-text-secondary">{name}</p>
                        </div>
                    ))}
                </div>
            </Section>

            {/* Buttons */}
            <Section title="Button Examples">
                <div className="flex flex-wrap gap-4">
                    <button className="bg-gradient-accent text-text-inverse font-semibold px-6 py-3 rounded-xl transition-all duration-250 hover:glow-teal">
                        Primary Action
                    </button>
                    <button className="bg-bg-elevated text-text-primary font-medium px-6 py-3 rounded-xl border border-border-default transition-all duration-250 hover:border-accent-teal">
                        Secondary
                    </button>
                    <button className="text-accent-teal font-medium px-6 py-3 rounded-xl transition-all duration-250 hover:bg-bg-tertiary">
                        Ghost
                    </button>
                    <button className="bg-highlight-amber text-text-inverse font-semibold px-6 py-3 rounded-xl transition-all duration-250 hover:glow-amber">
                        Highlight CTA
                    </button>
                </div>
            </Section>

            {/* Cards */}
            <Section title="Card Examples">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-bg-secondary rounded-2xl p-6 border border-border-subtle">
                        <h3 className="font-heading font-semibold text-lg mb-2">Solid Card</h3>
                        <p className="text-text-secondary text-sm">Standard card with subtle border.</p>
                    </div>
                    <div className="glass rounded-2xl p-6">
                        <h3 className="font-heading font-semibold text-lg mb-2">Glass Card</h3>
                        <p className="text-text-secondary text-sm">Frosted glass effect.</p>
                    </div>
                    <div className="bg-bg-secondary rounded-2xl p-6 border border-border-subtle glow-teal">
                        <h3 className="font-heading font-semibold text-lg mb-2">Glow Card</h3>
                        <p className="text-text-secondary text-sm">With teal glow accent.</p>
                    </div>
                </div>
            </Section>
        </div>
    );
}
