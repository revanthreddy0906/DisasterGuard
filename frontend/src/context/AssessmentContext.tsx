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

export function AssessmentProvider({ children }: { children: React.ReactNode }) {
    const [assessments, setAssessments] = useState<Assessment[]>([]);
    const [currentAssessment, setCurrentAssessment] = useState<Assessment | null>(null);
    const [isBackendOnline, setIsBackendOnline] = useState(false);
    const [isDemoMode, setIsDemoMode] = useState(false);

    useEffect(() => {
        checkBackendHealth().then(setIsBackendOnline);
        const interval = setInterval(() => {
            checkBackendHealth().then(setIsBackendOnline);
        }, 30000);
        return () => clearInterval(interval);
    }, []);

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
