import { Link, usePage, router } from '@inertiajs/react';
import { useState } from 'react';
import FlashMessages from '../Components/FlashMessages';

function NavLink({ href, children, active = false, onClick }) {
    return (
        <Link
            href={href}
            onClick={onClick}
            className={`text-sm font-medium transition-colors duration-250 ${
                active
                    ? 'text-accent-teal'
                    : 'text-text-secondary hover:text-text-primary'
            }`}
        >
            {children}
        </Link>
    );
}

function Nav() {
    const { auth, url } = usePage().props;
    const [mobileOpen, setMobileOpen] = useState(false);

    function handleLogout(e) {
        e.preventDefault();
        router.post('/logout');
    }

    return (
        <nav className="fixed top-0 inset-x-0 z-50 glass">
            <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                <div className="flex items-center gap-8">
                    <Link href="/" className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-accent" />
                        <span className="font-heading font-bold text-lg text-text-primary">
                            Stride
                        </span>
                    </Link>
                    <div className="hidden md:flex items-center gap-6">
                        <NavLink href="/explore" active={url === '/explore'}>
                            Explore
                        </NavLink>
                        {auth.user && (
                            <NavLink href="/dashboard" active={url === '/dashboard'}>
                                Dashboard
                            </NavLink>
                        )}
                    </div>
                </div>

                {/* Desktop auth */}
                <div className="hidden md:flex items-center gap-4">
                    {auth.user ? (
                        <div className="flex items-center gap-4">
                            <Link
                                href={`/u/${auth.user.username}`}
                                className="flex items-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
                            >
                                <div className="w-8 h-8 rounded-full bg-bg-elevated border border-border-default flex items-center justify-center">
                                    <span className="text-xs font-semibold text-accent-teal">
                                        {auth.user.name.charAt(0).toUpperCase()}
                                    </span>
                                </div>
                                <span className="font-medium">{auth.user.username}</span>
                            </Link>
                            <button
                                onClick={handleLogout}
                                className="text-sm text-text-muted hover:text-text-primary transition-colors"
                            >
                                Log out
                            </button>
                        </div>
                    ) : (
                        <>
                            <NavLink href="/login">Log in</NavLink>
                            <Link
                                href="/register"
                                className="bg-gradient-accent text-text-inverse text-sm font-semibold px-4 py-2 rounded-xl transition-all duration-250 hover:opacity-90"
                            >
                                Sign up
                            </Link>
                        </>
                    )}
                </div>

                {/* Mobile hamburger */}
                <button
                    className="md:hidden text-text-secondary p-2"
                    onClick={() => setMobileOpen(!mobileOpen)}
                >
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        {mobileOpen ? (
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        ) : (
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                        )}
                    </svg>
                </button>
            </div>

            {/* Mobile menu */}
            {mobileOpen && (
                <div className="md:hidden border-t border-border-subtle px-6 py-4 space-y-3 bg-bg-secondary">
                    <NavLink href="/explore" onClick={() => setMobileOpen(false)}>
                        Explore
                    </NavLink>
                    {auth.user ? (
                        <>
                            <NavLink href="/dashboard" onClick={() => setMobileOpen(false)}>
                                Dashboard
                            </NavLink>
                            <NavLink href={`/u/${auth.user.username}`} onClick={() => setMobileOpen(false)}>
                                Profile
                            </NavLink>
                            <button
                                onClick={handleLogout}
                                className="block text-sm text-text-muted hover:text-text-primary transition-colors"
                            >
                                Log out
                            </button>
                        </>
                    ) : (
                        <>
                            <NavLink href="/login" onClick={() => setMobileOpen(false)}>
                                Log in
                            </NavLink>
                            <NavLink href="/register" onClick={() => setMobileOpen(false)}>
                                Sign up
                            </NavLink>
                        </>
                    )}
                </div>
            )}
        </nav>
    );
}

function Footer() {
    return (
        <footer className="border-t border-border-subtle">
            <div className="max-w-7xl mx-auto px-6 py-12">
                <div className="flex flex-col md:flex-row justify-between items-start gap-8">
                    <div>
                        <div className="flex items-center gap-2 mb-3">
                            <div className="w-6 h-6 rounded-md bg-gradient-accent" />
                            <span className="font-heading font-bold text-text-primary">
                                StrideSoundscape
                            </span>
                        </div>
                        <p className="text-text-muted text-sm max-w-xs">
                            Design BPM-reactive soundscapes for your runs. Upload stems, choreograph mixes, share with the community.
                        </p>
                    </div>
                    <div className="flex gap-12">
                        <div>
                            <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">Product</h4>
                            <div className="flex flex-col gap-2">
                                <Link href="/explore" className="text-sm text-text-muted hover:text-text-secondary transition-colors">Explore</Link>
                            </div>
                        </div>
                        <div>
                            <h4 className="font-heading font-semibold text-sm text-text-primary mb-3">Account</h4>
                            <div className="flex flex-col gap-2">
                                <Link href="/login" className="text-sm text-text-muted hover:text-text-secondary transition-colors">Log in</Link>
                                <Link href="/register" className="text-sm text-text-muted hover:text-text-secondary transition-colors">Sign up</Link>
                            </div>
                        </div>
                    </div>
                </div>
                <div className="mt-12 pt-6 border-t border-border-subtle text-center">
                    <p className="text-text-muted text-xs">&copy; {new Date().getFullYear()} StrideSoundscape. All rights reserved.</p>
                </div>
            </div>
        </footer>
    );
}

export default function AppLayout({ children }) {
    return (
        <div className="min-h-screen bg-bg-primary flex flex-col">
            <Nav />
            <FlashMessages />
            <main className="flex-1 pt-16">{children}</main>
            <Footer />
        </div>
    );
}
