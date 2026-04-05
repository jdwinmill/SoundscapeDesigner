function csrfToken() {
    return decodeURIComponent(
        document.cookie.match(/XSRF-TOKEN=([^;]+)/)?.[1] || ''
    );
}

let csrfPending = null;

async function ensureCsrf() {
    if (csrfToken()) return;
    if (!csrfPending) {
        csrfPending = fetch('/sanctum/csrf-cookie', { credentials: 'same-origin' })
            .finally(() => { csrfPending = null; });
    }
    await csrfPending;
}

/**
 * Wrapper around fetch that ensures the Sanctum XSRF cookie is set
 * and automatically includes the X-XSRF-TOKEN header.
 */
export default async function apiFetch(url, options = {}) {
    await ensureCsrf();

    const token = csrfToken();
    const headers = { ...(options.headers || {}) };
    if (token) {
        headers['X-XSRF-TOKEN'] = token;
    }

    return fetch(url, {
        ...options,
        credentials: 'same-origin',
        headers,
    });
}
