export default function FormInput({ label, error, ...props }) {
    return (
        <div>
            {label && (
                <label className="block text-sm font-medium text-text-secondary mb-2">
                    {label}
                </label>
            )}
            <input
                className="w-full bg-bg-tertiary text-text-primary border border-border-default rounded-xl px-4 py-3 text-sm placeholder-text-muted focus:outline-none focus:border-accent-teal focus:ring-1 focus:ring-accent-teal transition-colors"
                {...props}
            />
            {error && <p className="mt-1.5 text-sm text-error">{error}</p>}
        </div>
    );
}
