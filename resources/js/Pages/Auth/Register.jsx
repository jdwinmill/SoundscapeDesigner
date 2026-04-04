import { Link, useForm } from '@inertiajs/react';
import AppLayout from '../../Layouts/AppLayout';
import FormInput from '../../Components/FormInput';

export default function Register() {
    const { data, setData, post, processing, errors } = useForm({
        name: '',
        username: '',
        email: '',
        password: '',
        password_confirmation: '',
    });

    function handleSubmit(e) {
        e.preventDefault();
        post('/register');
    }

    return (
        <AppLayout>
            <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-6 py-12">
                <div className="w-full max-w-md">
                    <div className="text-center mb-8">
                        <h1 className="font-heading text-3xl font-bold mb-2">Create your account</h1>
                        <p className="text-text-secondary">
                            Start designing soundscapes for your runs
                        </p>
                    </div>

                    <form onSubmit={handleSubmit} className="bg-bg-secondary rounded-2xl p-8 border border-border-subtle space-y-5">
                        <FormInput
                            label="Name"
                            type="text"
                            placeholder="Your name"
                            value={data.name}
                            onChange={(e) => setData('name', e.target.value)}
                            error={errors.name}
                            autoFocus
                        />
                        <FormInput
                            label="Username"
                            type="text"
                            placeholder="Pick a username"
                            value={data.username}
                            onChange={(e) => setData('username', e.target.value)}
                            error={errors.username}
                        />
                        <FormInput
                            label="Email"
                            type="email"
                            placeholder="you@example.com"
                            value={data.email}
                            onChange={(e) => setData('email', e.target.value)}
                            error={errors.email}
                        />
                        <FormInput
                            label="Password"
                            type="password"
                            placeholder="Create a password"
                            value={data.password}
                            onChange={(e) => setData('password', e.target.value)}
                            error={errors.password}
                        />
                        <FormInput
                            label="Confirm password"
                            type="password"
                            placeholder="Confirm your password"
                            value={data.password_confirmation}
                            onChange={(e) => setData('password_confirmation', e.target.value)}
                            error={errors.password_confirmation}
                        />
                        <button
                            type="submit"
                            disabled={processing}
                            className="w-full bg-gradient-accent text-text-inverse font-semibold py-3 rounded-xl transition-all duration-250 hover:opacity-90 disabled:opacity-50"
                        >
                            {processing ? 'Creating account...' : 'Create account'}
                        </button>
                    </form>

                    <p className="text-center mt-6 text-text-secondary text-sm">
                        Already have an account?{' '}
                        <Link href="/login" className="text-accent-teal hover:underline font-medium">
                            Log in
                        </Link>
                    </p>
                </div>
            </div>
        </AppLayout>
    );
}
