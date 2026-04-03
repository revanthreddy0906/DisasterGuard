"use client";

import { useState, useMemo } from "react";
import Map, { Source, Layer } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAssessment } from "@/context/AssessmentContext";
import { Navigation, Thermometer, AlertTriangle, Layers, Satellite } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

const MAP_STYLE = {
    version: 8,
    sources: {
        'esri-dark': {
            type: 'raster',
            tiles: [
                'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}'
            ],
            tileSize: 256,
            attribution: 'Esri, Garmin, FAO, NOAA'
        }
    },
    layers: [
        {
            id: 'background',
            type: 'background',
            paint: { 'background-color': '#0a0e1a' }
        },
        {
            id: 'dark-layer',
            type: 'raster',
            source: 'esri-dark',
            minzoom: 0,
            maxzoom: 22
        }
    ]
};

const heatmapLayer: any = {
    id: 'heatmap',
    type: 'heatmap',
    paint: {
        'heatmap-weight': ['interpolate', ['linear'], ['get', 'mag'], 0, 0, 6, 1],
        'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 0, 1, 9, 3],
        'heatmap-color': [
            'interpolate', ['linear'], ['heatmap-density'],
            0, 'rgba(6,182,212,0)',
            0.2, 'rgb(6,182,212)',
            0.4, 'rgb(139,92,246)',
            0.6, 'rgb(249,115,22)',
            0.8, 'rgb(239,68,68)',
            1, 'rgb(220,38,38)'
        ],
        'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 0, 2, 9, 20],
        'heatmap-opacity': ['interpolate', ['linear'], ['zoom'], 7, 1, 18, 0.5]
    }
};

export default function HotspotsPage() {
    const { assessments } = useAssessment();
    const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>(
        assessments.length > 0 ? assessments[0].id : ""
    );

    const selectedAssessment = assessments.find(a => a.id === selectedAssessmentId);

    // Create a point for the assessment location with damage magnitude
    const heatmapData = useMemo(() => {
        if (!selectedAssessment?.results || !selectedAssessment?.location) return null;

        const results = selectedAssessment.results as any;
        const baseLng = selectedAssessment.location.lng;
        const baseLat = selectedAssessment.location.lat;

        if (results.hotspots && results.hotspots.length > 0) {
            const features = results.hotspots.map((patch: any) => {
                let mag = 0;
                if (patch.damage_class === 'destroyed') mag = 3;
                else if (patch.damage_class === 'severe-damage') mag = 2;
                else mag = 0.5;

                // Patches are returned in source image coordinates (e.g., 224x224 patch within 1024x1024).
                // Example bounding box: [x, y, width, height]
                const [x, y, w, h] = patch.bbox;
                const normalize = 1024; // Approximation for scale mapping
                
                // Offset latitude and longitude proportionally.
                // 0.003 degrees corresponds to roughly 300 meters, typical bounds for high-res images
                const lngOffset = ((x + w/2) / normalize - 0.5) * 0.003;
                const latOffset = (0.5 - (y + h/2) / normalize) * 0.003;

                return {
                    type: "Feature" as const,
                    properties: { mag, confidence: patch.confidence, class: patch.damage_class },
                    geometry: {
                        type: "Point" as const,
                        coordinates: [baseLng + lngOffset, baseLat + latOffset]
                    }
                };
            });

            return {
                type: "FeatureCollection" as const,
                features
            };
        }

        // Fallback if no patches are present
        let mag = 0;
        if (selectedAssessment.results.damage_class === 'destroyed') mag = 3;
        else if (selectedAssessment.results.damage_class === 'severe-damage') mag = 2;
        else mag = 0.5;

        return {
            type: "FeatureCollection" as const,
            features: [{
                type: "Feature" as const,
                properties: { mag },
                geometry: {
                    type: "Point" as const,
                    coordinates: [baseLng, baseLat]
                }
            }]
        };
    }, [selectedAssessment]);

    if (assessments.length === 0) {
        return (
            <div className="h-[calc(100vh-6rem)] flex items-center justify-center">
                <Card className="max-w-md w-full">
                    <CardContent className="text-center py-12">
                        <Layers className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-slate-300 mb-2">No Hotspot Data</h3>
                        <p className="text-sm text-slate-500 mb-4">Upload and analyze imagery to view damage hotspots.</p>
                        <Button asChild variant="outline" size="sm">
                            <Link href="/upload">Upload Imagery</Link>
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="space-y-6 h-[calc(100vh-6rem)] flex flex-col">
            <div className="flex items-center justify-between shrink-0">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Hotspot Analysis</h1>
                    <p className="text-slate-400 mt-1">Identify high-density damage zones using spatial clustering.</p>
                </div>
                <div className="flex gap-4">
                    <Select value={selectedAssessmentId} onValueChange={setSelectedAssessmentId}>
                        <SelectTrigger className="w-[280px]">
                            <SelectValue placeholder="Select Assessment" />
                        </SelectTrigger>
                        <SelectContent>
                            {assessments.map(a => (
                                <SelectItem key={a.id} value={a.id}>{a.name}</SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 min-h-0">
                {/* Sidebar */}
                <div className="lg:col-span-1 space-y-4">
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center">
                                <Thermometer className="w-5 h-5 mr-2 text-orange-400" />
                                Intensity Scale
                            </CardTitle>
                            <CardDescription>Damage concentration levels.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <div className="h-6 w-full rounded-md bg-gradient-to-r from-cyan-500 via-violet-500 via-orange-500 to-red-600 border border-white/10"></div>
                                <div className="flex justify-between text-xs text-slate-500 font-medium">
                                    <span>Low Density</span>
                                    <span>Critical Cluster</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg flex items-center">
                                <Layers className="w-5 h-5 mr-2 text-violet-400" />
                                Analysis Stats
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {selectedAssessment?.location && (
                                <div className="bg-white/[0.03] p-3 rounded-lg border border-white/[0.06]">
                                    <p className="text-xs text-slate-500 uppercase font-semibold">Location</p>
                                    <p className="text-sm font-medium text-slate-200 mt-1">
                                        {selectedAssessment.location.lat.toFixed(4)}, {selectedAssessment.location.lng.toFixed(4)}
                                    </p>
                                </div>
                            )}

                            {selectedAssessment?.results && (
                                <div className="bg-white/[0.03] p-3 rounded-lg border border-white/[0.06]">
                                    <p className="text-xs text-slate-500 uppercase font-semibold">Damage Class</p>
                                    <p className="text-sm font-medium text-slate-200 mt-1 capitalize">
                                        {selectedAssessment.results.damage_class.replace('-', ' ')}
                                    </p>
                                </div>
                            )}

                            <div className="flex items-start gap-3 p-3 bg-cyan-500/5 text-cyan-300 rounded-lg text-sm border border-cyan-500/10">
                                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                                <p className="text-xs">Red zones indicate where damaged structures cluster. Prioritize for reconnaissance.</p>
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Map */}
                <div className="lg:col-span-3 bg-[#0a0e1a] rounded-xl overflow-hidden border border-white/[0.08] relative shadow-2xl">
                    {heatmapData && selectedAssessment?.location ? (
                        <Map
                            initialViewState={{
                                longitude: selectedAssessment.location.lng,
                                latitude: selectedAssessment.location.lat,
                                zoom: 14
                            }}
                            style={{ width: '100%', height: '100%' }}
                            mapStyle={MAP_STYLE as any}
                        >
                            <Source type="geojson" data={heatmapData}>
                                <Layer {...heatmapLayer} />
                            </Source>

                            <div className="absolute top-4 left-4 bg-[#0c1122]/90 backdrop-blur-xl text-white px-3 py-1.5 rounded-lg border border-white/[0.08] text-xs font-mono shadow-lg">
                                <Navigation className="w-3 h-3 inline-block mr-2 text-cyan-400" />
                                HEATMAP MODE
                            </div>
                        </Map>
                    ) : (
                        <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 gap-4">
                            <Satellite className="w-12 h-12 text-slate-600" />
                            <p>Select an assessment to view damage heatmap.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
