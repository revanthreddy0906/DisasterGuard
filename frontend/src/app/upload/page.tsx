"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Dropzone } from "@/components/upload/Dropzone";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, X, ArrowRight, Loader2, AlertCircle, Beaker } from "lucide-react";
import { formatBytes, cn } from "@/lib/utils";
import { useAssessment } from "@/context/AssessmentContext";
import { predictDamage } from "@/lib/api";
import { Badge } from "@/components/ui/badge";

interface FileWithPreview extends File {
    preview: string;
}

export default function UploadPage() {
    const router = useRouter();
    const { addAssessment, updateAssessment, isBackendOnline } = useAssessment();
    const [unpaired, setUnpaired] = useState<FileWithPreview[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [progress, setProgress] = useState("");

    const processFiles = useCallback((files: File[]) => {
        const newFiles = files.map(file => Object.assign(file, {
            preview: URL.createObjectURL(file)
        })) as FileWithPreview[];
        setUnpaired(prev => [...prev, ...newFiles]);
        setError(null);
    }, []);

    const handleDrop = (acceptedFiles: File[]) => {
        processFiles(acceptedFiles);
    };

    const removeFile = (name: string) => {
        setUnpaired(prev => prev.filter(f => f.name !== name));
    };

    const handleTrySample = async () => {
        setError(null);
        setProgress("Loading sample images...");

        try {
            // Fetch sample pre and post images from the backend
            const res = await fetch("/api/v1/sample-images");
            if (!res.ok) throw new Error("Could not load sample images from backend");
            const data = await res.json();

            // Convert base64 images to File objects
            const preBlob = await fetch(`data:image/png;base64,${data.pre_image}`).then(r => r.blob());
            const postBlob = await fetch(`data:image/png;base64,${data.post_image}`).then(r => r.blob());

            const preFile = new File([preBlob], data.pre_name || "sample_pre.png", { type: "image/png" });
            const postFile = new File([postBlob], data.post_name || "sample_post.png", { type: "image/png" });

            processFiles([preFile, postFile]);
            setProgress("");
        } catch (err: any) {
            setError("Could not load sample data. Make sure the backend is running.");
            setProgress("");
        }
    };

    const handleAnalysis = async () => {
        if (!isBackendOnline) {
            setError("Backend is offline. Please start the backend server first.");
            return;
        }

        setIsProcessing(true);
        setError(null);

        // Detect pre/post images
        let preFile = unpaired.find(f => f.name.toLowerCase().includes('pre'));
        let postFile = unpaired.find(f => f.name.toLowerCase().includes('post'));

        // Fallback: first file = pre, second = post
        if (!preFile) preFile = unpaired[0];
        if (!postFile) postFile = unpaired[1] || unpaired[0];

        // Determine location from filenames — comprehensive mapping for all disaster types
        const filenames = unpaired.map(f => f.name.toLowerCase()).join(' ');
        
        // Priority-ordered: most specific matches first
        const DISASTER_LOCATIONS: { pattern: string; name: string; lat: number; lng: number }[] = [
            { pattern: 'guatemala-volcano',     name: 'Volcán de Fuego, Guatemala',   lat: 14.4747,  lng: -90.8806 },
            { pattern: 'hurricane-florence',     name: 'Wilmington, NC',               lat: 34.2104,  lng: -77.8868 },
            { pattern: 'hurricane-harvey',       name: 'Houston, TX',                  lat: 29.7604,  lng: -95.3698 },
            { pattern: 'hurricane-matthew',      name: 'Port-au-Prince, Haiti',        lat: 18.5944,  lng: -72.3074 },
            { pattern: 'hurricane-michael',      name: 'Mexico Beach, FL',             lat: 29.9472,  lng: -85.4058 },
            { pattern: 'mexico-earthquake',      name: 'Mexico City, Mexico',          lat: 19.4326,  lng: -99.1332 },
            { pattern: 'midwest-flooding',       name: 'Council Bluffs, IA',           lat: 41.2619,  lng: -95.8608 },
            { pattern: 'palu-tsunami',           name: 'Palu, Indonesia',              lat: -0.9003,  lng: 119.8776 },
            { pattern: 'santa-rosa-wildfire',    name: 'Santa Rosa, CA',               lat: 38.4404,  lng: -122.7141 },
            { pattern: 'socal-fire',             name: 'Ventura, CA',                  lat: 34.2746,  lng: -119.2290 },
            // Generic fallbacks (checked last)
            { pattern: 'hurricane',              name: 'Gulf Coast, USA',              lat: 29.7604,  lng: -95.3698 },
            { pattern: 'earthquake',             name: 'Earthquake Zone',              lat: 19.4326,  lng: -99.1332 },
            { pattern: 'fire',                   name: 'Wildfire Zone, CA',            lat: 34.2746,  lng: -119.2290 },
            { pattern: 'flood',                  name: 'Flood Zone, USA',              lat: 41.2619,  lng: -95.8608 },
            { pattern: 'tsunami',                name: 'Tsunami Zone',                 lat: -0.9003,  lng: 119.8776 },
            { pattern: 'volcano',                name: 'Volcanic Zone',                lat: 14.4747,  lng: -90.8806 },
        ];

        let location = { name: "Unknown Region", lat: 37.7749, lng: -122.4194 };
        for (const loc of DISASTER_LOCATIONS) {
            if (filenames.includes(loc.pattern)) {
                location = { name: loc.name, lat: loc.lat, lng: loc.lng };
                break;
            }
        }

        const assessmentId = crypto.randomUUID();

        // Create the assessment entry immediately as "processing"
        const newAssessment = {
            id: assessmentId,
            name: `Assessment: ${location.name}`,
            status: 'processing' as const,
            date: new Date().toISOString(),
            location: location,
            imagePair: {
                pre: preFile.preview,
                post: postFile.preview
            }
        };

        addAssessment(newAssessment);
        setProgress("Sending images to ML model...");

        try {
            // Call the real backend API
            const result = await predictDamage(preFile, postFile);

            setProgress("Analysis complete!");

            // Update the existing assessment with results
            updateAssessment(assessmentId, {
                status: 'complete' as const,
                results: result
            });
            setIsProcessing(false);
            setProgress("");
            router.push('/analysis');
        } catch (err: any) {
            setError(`Analysis failed: ${err.message}`);
            setIsProcessing(false);
            setProgress("");
        }
    };

    return (
        <div className="space-y-8 max-w-5xl mx-auto">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Upload Imagery</h1>
                    <p className="text-slate-400 mt-1">Upload pre-event and post-event satellite imagery for analysis.</p>
                </div>
                <div className="flex items-center gap-3">
                    <Badge variant={isBackendOnline ? "success" : "destructive"} className="text-[10px]">
                        {isBackendOnline ? "● ML Ready" : "● Backend Offline"}
                    </Badge>
                </div>
            </div>

            {/* Error banner */}
            {error && (
                <div className="flex items-center gap-3 p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400">
                    <AlertCircle className="w-5 h-5 shrink-0" />
                    <p className="text-sm">{error}</p>
                    <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-300">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            <Card>
                <CardContent className="pt-6">
                    <Dropzone
                        onDrop={handleDrop}
                        accept={{
                            'image/jpeg': ['.jpg', '.jpeg'],
                            'image/png': ['.png'],
                            'image/tiff': ['.tif', '.tiff']
                        }}
                    />
                    {/* Try with sample data button */}
                    <div className="mt-4 flex justify-center">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleTrySample}
                            disabled={isProcessing || !isBackendOnline}
                            className="text-slate-500 hover:text-cyan-400"
                        >
                            <Beaker className="mr-2 h-4 w-4" />
                            Try with sample data
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Uploaded files list */}
            {unpaired.length > 0 && (
                <Card>
                    <CardHeader>
                        <CardTitle className="text-lg">Uploaded Files ({unpaired.length})</CardTitle>
                        <CardDescription>Files ready for analysis. Need at least 2 files (pre and post event).</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {unpaired.map((file, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 bg-white/[0.03] rounded-lg border border-white/[0.06] group hover:border-cyan-500/20 transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 bg-white/[0.05] rounded-lg overflow-hidden shrink-0 border border-white/[0.06]">
                                            <img src={file.preview} alt={file.name} className="h-full w-full object-cover" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-slate-200 truncate max-w-[300px]">{file.name}</p>
                                            <p className="text-xs text-slate-500">{formatBytes(file.size)}</p>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <Badge
                                            variant={
                                                file.name.toLowerCase().includes('pre') ? "default" :
                                                file.name.toLowerCase().includes('post') ? "warning" :
                                                "secondary"
                                            }
                                            className="text-[10px] uppercase"
                                        >
                                            {file.name.toLowerCase().includes('pre') ? "Pre-Event" :
                                                file.name.toLowerCase().includes('post') ? "Post-Event" : "Unknown"}
                                        </Badge>

                                        <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500 hover:text-red-400" onClick={() => removeFile(file.name)}>
                                            <X className="w-4 h-4" />
                                        </Button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Progress indicator */}
                        {progress && (
                            <div className="mt-4 p-3 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-sm flex items-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                {progress}
                            </div>
                        )}

                        <div className="mt-6 flex justify-end">
                            <Button
                                disabled={unpaired.length < 2 || isProcessing || !isBackendOnline}
                                size="lg"
                                onClick={handleAnalysis}
                            >
                                {isProcessing ? (
                                    <>
                                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                        Processing...
                                    </>
                                ) : (
                                    <>
                                        Run Analysis <ArrowRight className="ml-2 h-4 w-4" />
                                    </>
                                )}
                            </Button>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
