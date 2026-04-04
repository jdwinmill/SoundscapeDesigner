/**
 * Design Tokens — StrideSoundscape
 *
 * Single source of truth for the visual system.
 * Change values here to retheme the entire app.
 *
 * New age fitness vibe: dark, energetic, breathable.
 */

export const colors = {
    // Base
    bg: {
        primary: '#0a0a0f',
        secondary: '#111118',
        tertiary: '#1a1a24',
        elevated: '#222230',
    },

    // Accent gradient endpoints
    accent: {
        teal: '#00d4aa',
        violet: '#7c3aed',
        gradient: 'linear-gradient(135deg, #00d4aa 0%, #7c3aed 100%)',
    },

    // Warm highlight
    highlight: {
        amber: '#f59e0b',
        gold: '#fbbf24',
    },

    // Text
    text: {
        primary: '#f0f0f5',
        secondary: '#8b8b9e',
        muted: '#5a5a6e',
        inverse: '#0a0a0f',
    },

    // Semantic
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6',

    // Border
    border: {
        subtle: '#1f1f2e',
        default: '#2a2a3d',
        strong: '#3a3a50',
    },
};

export const typography = {
    fontFamily: {
        heading: "'Sora', sans-serif",
        body: "'Inter', sans-serif",
    },
    fontSize: {
        xs: '0.75rem',     // 12px
        sm: '0.875rem',    // 14px
        base: '1rem',      // 16px
        lg: '1.125rem',    // 18px
        xl: '1.25rem',     // 20px
        '2xl': '1.5rem',   // 24px
        '3xl': '1.875rem', // 30px
        '4xl': '2.25rem',  // 36px
        '5xl': '3rem',     // 48px
        '6xl': '3.75rem',  // 60px
    },
    fontWeight: {
        normal: '400',
        medium: '500',
        semibold: '600',
        bold: '700',
    },
    lineHeight: {
        tight: '1.1',
        snug: '1.25',
        normal: '1.5',
        relaxed: '1.75',
    },
};

export const spacing = {
    px: '1px',
    0: '0',
    1: '0.25rem',   // 4px
    2: '0.5rem',    // 8px
    3: '0.75rem',   // 12px
    4: '1rem',      // 16px
    5: '1.25rem',   // 20px
    6: '1.5rem',    // 24px
    8: '2rem',      // 32px
    10: '2.5rem',   // 40px
    12: '3rem',     // 48px
    16: '4rem',     // 64px
    20: '5rem',     // 80px
    24: '6rem',     // 96px
    32: '8rem',     // 128px
};

export const radii = {
    none: '0',
    sm: '0.375rem',  // 6px
    md: '0.5rem',    // 8px
    lg: '0.75rem',   // 12px
    xl: '1rem',      // 16px
    '2xl': '1.5rem', // 24px
    full: '9999px',
};

export const effects = {
    // Glow effects for interactive elements
    glow: {
        teal: '0 0 20px rgba(0, 212, 170, 0.3)',
        violet: '0 0 20px rgba(124, 58, 237, 0.3)',
        amber: '0 0 20px rgba(245, 158, 11, 0.3)',
    },

    // Glass morphism
    glass: {
        bg: 'rgba(17, 17, 24, 0.7)',
        blur: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.05)',
    },

    // Shadows
    shadow: {
        sm: '0 1px 2px rgba(0, 0, 0, 0.3)',
        md: '0 4px 6px rgba(0, 0, 0, 0.3)',
        lg: '0 10px 15px rgba(0, 0, 0, 0.4)',
        xl: '0 20px 25px rgba(0, 0, 0, 0.5)',
    },

    // Transitions
    transition: {
        fast: '150ms ease',
        normal: '250ms ease',
        slow: '400ms ease',
    },
};

export const breakpoints = {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
};
