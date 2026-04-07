/**
 * API client for the DisasterGuard backend (FastAPI)
 */

export interface PredictionResult {
    damage_class: string;
    confidence: number;
    probabilities: Record<string, number>;
    hotspots?: Array<{
        bbox: number[];
        damage_class: string;
        confidence: number;
    }>;
}

type ApiErrorDetail = {
    code?: string;
    message?: string;
};

const API_BASE = "/api/v1";

/**
 * Check if the backend server is reachable
 */
export async function checkBackendHealth(): Promise<boolean> {
    try {
        const res = await fetch("/api/health", { signal: AbortSignal.timeout(3000) });
        return res.ok;
    } catch {
        return false;
    }
}

/**
 * Send a pre/post image pair to the ML model for damage prediction
 */
export async function predictDamage(
    preFile: File,
    postFile: File
): Promise<PredictionResult> {
    const formData = new FormData();
    formData.append("pre_image", preFile);
    formData.append("post_image", postFile);

    const res = await fetch(`${API_BASE}/predict`, {
        method: "POST",
        body: formData,
    });

    if (!res.ok) {
        const rawBody = await res.text();
        let errorMessage = `Prediction failed (${res.status})`;

        if (rawBody) {
            try {
                const parsed = JSON.parse(rawBody) as { detail?: string | ApiErrorDetail };
                if (typeof parsed.detail === "string") {
                    errorMessage = parsed.detail;
                } else if (parsed.detail?.message) {
                    errorMessage = parsed.detail.message;
                } else {
                    errorMessage = rawBody;
                }
            } catch {
                errorMessage = rawBody;
            }
        }

        throw new Error(`Prediction failed (${res.status}): ${errorMessage}`);
    }

    return res.json();
}

/**
 * Load sample images from the data/sample directory via the backend
 */
export async function getSampleImages(): Promise<{ pre: string; post: string } | null> {
    try {
        const res = await fetch(`${API_BASE}/sample-images`, { signal: AbortSignal.timeout(5000) });
        if (!res.ok) return null;
        return res.json();
    } catch {
        return null;
    }
}
