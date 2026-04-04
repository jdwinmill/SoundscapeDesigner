import { usePage } from '@inertiajs/react';
import { useEffect, useState } from 'react';

export default function FlashMessages() {
    const { flash } = usePage().props;
    const [visible, setVisible] = useState(false);
    const [message, setMessage] = useState('');
    const [type, setType] = useState('success');

    useEffect(() => {
        if (flash?.success) {
            setMessage(flash.success);
            setType('success');
            setVisible(true);
        } else if (flash?.error) {
            setMessage(flash.error);
            setType('error');
            setVisible(true);
        }
    }, [flash?.success, flash?.error]);

    useEffect(() => {
        if (visible) {
            const timer = setTimeout(() => setVisible(false), 4000);
            return () => clearTimeout(timer);
        }
    }, [visible]);

    if (!visible) return null;

    return (
        <div className="fixed top-20 right-6 z-50 animate-in fade-in slide-in-from-top-2">
            <div
                className={`glass rounded-xl px-5 py-3 text-sm font-medium shadow-lg ${
                    type === 'success' ? 'text-success border border-success/20' : 'text-error border border-error/20'
                }`}
            >
                {message}
                <button
                    onClick={() => setVisible(false)}
                    className="ml-3 text-text-muted hover:text-text-primary"
                >
                    &times;
                </button>
            </div>
        </div>
    );
}
