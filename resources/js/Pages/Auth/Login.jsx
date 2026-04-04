import { Link, useForm } from '@inertiajs/react';
import AppLayout from '../../Layouts/AppLayout';
import FormInput from '../../Components/FormInput';

export default function Login() {
    const { data, setData, post, processing, errors } = useForm({
        email: '',
        password: '',
    });

    function handleSubmit(e) {
        e.preventDefault();
        post('/login');
    }

    return (
        <AppLayout>
            <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-6">
                <div className="w-full max-w-md">
                    <div className="text-center mb-8">
                        <h1 className="font-heading text-3xl font-bold mb-2">Welcome back</h1>
                        <p className="text-text-secondary">
                            Log in to your account to continue
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="bg-bg-secondary rounded-2xl p-8 border border-border-subtle space-y-5">
                        <FormInput
                            label="Email"
                            type="email"
                            placeholder="you@example.com"
                            value={data.email}
                            onChange={(e) => setData('email', e.target.value)}
                            error={errors.email}
                            autoFocus
                        />
                        <FormInput
                            label="Password"
                            type="password"
                            placeholder="Your password"
                            value={data.password}
                            onChange={(e) => setData('password', e.target.value)}
                            error={errors.password}
                        />
                        <button
                            type="submit"
                            disabled={processing}
                            className="w-full bg-gradient-accent text-text-inverse font-semibold py-3 rounded-xl transition-all duration-250 hover:opacity-90 disabled:opacity-50"
                        >
                            {processing ? 'Logging in...' : 'Log in'}
                        </button>
                    </form>

                    <p className="text-center mt-6 text-text-secondary text-sm">
                        Don't have an account?{' '}
                        <Link href="/register" className="text-accent-teal hover:underline font-medium">
                            Sign up
                        </Link>
                    </p>
                </div>
            </div>
        </AppLayout>
    );
}
