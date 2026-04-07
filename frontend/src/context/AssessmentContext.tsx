"use client";

import { createContext, useContext, useState, useEffect } from 'react';
import { checkBackendHealth } from '@/lib/api';

export interface Assessment {
    id: string;
    name: string;
    status: 'processing' | 'complete' | 'failed';
    date: string;
    imagePair?: { pre: string; post: string };
    results?: {
        damage_class: string;
        confidence: number;
        probabilities: Record<string, number>;
        hotspots?: Array<{
            bbox: number[];
            damage_class: string;
            confidence: number;
        }>;
        source_dimensions?: {
            width: number;
            height: number;
        };
    };
    location?: {
        name: string;
        lat: number;
        lng: number;
    };
}

interface AssessmentContextType {
    assessments: Assessment[];
    addAssessment: (assessment: Assessment) => void;
    updateAssessment: (id: string, updates: Partial<Assessment>) => void;
    currentAssessment: Assessment | null;
    setCurrentAssessment: (assessment: Assessment | null) => void;
    isBackendOnline: boolean;
    isDemoMode: boolean;
    setIsDemoMode: (val: boolean) => void;
}

const AssessmentContext = createContext<AssessmentContextType | undefined>(undefined);
const STORAGE_KEY = 'disasterguard.assessments.v1';
const PERSIST_ASSESSMENTS = process.env.NEXT_PUBLIC_PERSIST_ASSESSMENTS === 'true';

type PersistedAssessmentState = {
    assessments: Assessment[];
    currentAssessmentId: string | null;
    isDemoMode: boolean;
};

function sanitizeImagePair(imagePair?: { pre: string; post: string }) {
    if (!imagePair) return undefined;

    const pre = imagePair.pre.startsWith('blob:') ? '' : imagePair.pre;
    const post = imagePair.post.startsWith('blob:') ? '' : imagePair.post;
    if (!pre || !post) return undefined;
    return { pre, post };
}

export function AssessmentProvider({ children }: { children: React.ReactNode }) {
    const [assessments, setAssessments] = useState<Assessment[]>([]);
    const [currentAssessment, setCurrentAssessment] = useState<Assessment | null>(null);
    const [isBackendOnline, setIsBackendOnline] = useState(false);
    const [isDemoMode, setIsDemoMode] = useState(false);
    const [isStorageHydrated, setIsStorageHydrated] = useState(false);

    useEffect(() => {
        checkBackendHealth().then(setIsBackendOnline);
        const interval = setInterval(() => {
            checkBackendHealth().then(setIsBackendOnline);
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (!PERSIST_ASSESSMENTS) {
            localStorage.removeItem(STORAGE_KEY);
            setIsStorageHydrated(true);
            return;
        }

        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) {
            setIsStorageHydrated(true);
            return;
        }

        try {
            const parsed = JSON.parse(raw) as PersistedAssessmentState;
            if (!Array.isArray(parsed.assessments)) {
                throw new Error('Invalid persisted assessments payload.');
            }

            setAssessments(parsed.assessments);
            setIsDemoMode(Boolean(parsed.isDemoMode));
            if (parsed.currentAssessmentId) {
                const restoredCurrent = parsed.assessments.find(a => a.id === parsed.currentAssessmentId) || null;
                setCurrentAssessment(restoredCurrent);
            }
        } catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            console.error(`Failed to restore persisted assessment state: ${message}`);
            localStorage.removeItem(STORAGE_KEY);
        } finally {
            setIsStorageHydrated(true);
        }
    }, []);

    useEffect(() => {
        if (!PERSIST_ASSESSMENTS) return;
        if (!isStorageHydrated) return;
        const payload: PersistedAssessmentState = {
            assessments: assessments.map(a => ({
                ...a,
                imagePair: sanitizeImagePair(a.imagePair),
            })),
            currentAssessmentId: currentAssessment?.id ?? null,
            isDemoMode,
        };
        localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    }, [assessments, currentAssessment, isDemoMode, isStorageHydrated]);

    const addAssessment = (assessment: Assessment) => {
        setAssessments(prev => [assessment, ...prev]);
        setCurrentAssessment(assessment);
    };

    const updateAssessment = (id: string, updates: Partial<Assessment>) => {
        setAssessments(prev =>
            prev.map(a => a.id === id ? { ...a, ...updates } : a)
        );
        if (currentAssessment?.id === id) {
            setCurrentAssessment(prev => prev ? { ...prev, ...updates } : null);
        }
    };

    return (
        <AssessmentContext.Provider value={{ assessments, addAssessment, updateAssessment, currentAssessment, setCurrentAssessment, isBackendOnline, isDemoMode, setIsDemoMode }}>
            {children}
        </AssessmentContext.Provider>
    );
}

export function useAssessment() {
    const context = useContext(AssessmentContext);
    if (context === undefined) {
        throw new Error('useAssessment must be used within an AssessmentProvider');
    }
    return context;
}
