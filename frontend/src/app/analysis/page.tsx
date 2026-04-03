"use client";

import { MapComponent } from "@/components/map/MapComponent";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, MapPin, Calendar, AlertTriangle, Ruler, Navigation, ImageIcon, Satellite } from "lucide-react";
import { useAssessment } from "@/context/AssessmentContext";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

export default function AnalysisPage() {
    const { currentAssessment } = useAssessment();

    const damageClass = currentAssessment?.results?.damage_class || 'unknown';
    const confidence = currentAssessment?.results?.confidence || 0;
    const probabilities = currentAssessment?.results?.probabilities || {};

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col lg:flex-row gap-6">

            {/* Left panel */}
            <div className="w-full lg:w-[400px] shrink-0 h-full flex flex-col gap-4 overflow-y-auto pr-1">
                {currentAssessment ? (
                    <>
                        <Card className="flex-none border-l-4 border-l-cyan-500">
                            <CardHeader className="pb-2">
                                <div className="flex items-start justify-between">
                                    <div>
                                        <CardTitle className="text-xl font-bold">Assessment Report</CardTitle>
                                        <CardDescription className="mt-1 flex items-center gap-2">
                                            <Calendar className="w-3 h-3" />
                                            {new Date(currentAssessment.date).toLocaleDateString()}
                                        </CardDescription>
                                    </div>
                                    <Badge variant={currentAssessment.status === 'complete' ? 'success' : 'default'}>
                                        {currentAssessment.status === 'complete' ? 'Complete' : 'Processing'}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="flex items-center text-slate-200 text-sm mb-4 font-semibold px-3 py-2 bg-white/[0.04] rounded-lg border border-white/[0.06]">
                                    <MapPin className="w-4 h-4 mr-2 text-red-400" />
                                    <span>{currentAssessment.location?.name || "Unknown Location"}</span>
                                </div>

                                {/* Damage Classification Result */}
                                <div className={`p-4 rounded-lg mb-4 border ${
                                    damageClass === 'destroyed' ? 'bg-red-500/10 border-red-500/20' :
                                    damageClass === 'severe-damage' ? 'bg-orange-500/10 border-orange-500/20' :
                                    'bg-emerald-500/10 border-emerald-500/20'
                                }`}>
                                    <div className="flex items-center gap-2 mb-2">
                                        <AlertTriangle className={`w-4 h-4 ${
                                            damageClass === 'destroyed' ? 'text-red-400' :
                                            damageClass === 'severe-damage' ? 'text-orange-400' :
                                            'text-emerald-400'
                                        }`} />
                                        <span className="text-sm font-bold text-white uppercase">{damageClass.replace('-', ' ')}</span>
                                    </div>
                                    <p className="text-xs text-slate-400">Confidence: <span className="text-white font-semibold">{(confidence * 100).toFixed(1)}%</span></p>
                                </div>

                                {/* Probability breakdown */}
                                <div className="space-y-3">
                                    <p className="text-xs font-semibold text-slate-500 uppercase">Probability Breakdown</p>
                                    {Object.entries(probabilities).map(([cls, prob]) => (
                                        <div key={cls} className="space-y-1.5">
                                            <div className="flex justify-between text-sm">
                                                <span className="text-slate-400 capitalize">{cls}</span>
                                                <span className="font-medium text-slate-200">{((prob as number) * 100).toFixed(1)}%</span>
                                            </div>
                                            <div className="h-2 bg-white/[0.05] rounded-full overflow-hidden">
                                                <div
                                                    className={`h-full rounded-full ${
                                                        cls === 'destroyed' ? 'bg-gradient-to-r from-red-500 to-red-400' :
                                                        cls === 'severe-damage' ? 'bg-gradient-to-r from-orange-500 to-amber-400' :
                                                        'bg-gradient-to-r from-emerald-500 to-cyan-400'
                                                    }`}
                                                    style={{ width: `${(prob as number) * 100}%` }}
                                                />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Button className="w-full" variant="outline">
                                    <Download className="mr-2 h-4 w-4" /> Download Report
                                </Button>
                            </CardFooter>
                        </Card>

                        {/* Input Imagery */}
                        <Card className="flex-1 min-h-[200px]">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-base">Input Imagery</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="space-y-2">
                                    <p className="text-xs font-semibold text-slate-500 uppercase">Pre-Event Reference</p>
                                    <div className="w-full h-32 bg-white/[0.03] rounded-lg overflow-hidden border border-white/[0.06]">
                                        {currentAssessment.imagePair?.pre ? (
                                            <img src={currentAssessment.imagePair.pre} className="w-full h-full object-cover" alt="Pre-event" />
                                        ) : (
                                            <div className="flex flex-col items-center justify-center h-full text-slate-500">
                                                <ImageIcon className="w-6 h-6 mb-1" />
                                                <span className="text-xs">No Image Available</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <p className="text-xs font-semibold text-slate-500 uppercase">Post-Event Capture</p>
                                    <div className="w-full h-32 bg-white/[0.03] rounded-lg overflow-hidden border border-white/[0.06]">
                                        {currentAssessment.imagePair?.post ? (
                                            <img src={currentAssessment.imagePair.post} className="w-full h-full object-cover" alt="Post-event" />
                                        ) : (
                                            <div className="flex flex-col items-center justify-center h-full text-slate-500">
                                                <ImageIcon className="w-6 h-6 mb-1" />
                                                <span className="text-xs">No Image Available</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </>
                ) : (
                    <Card className="flex-1 flex items-center justify-center">
                        <CardContent className="text-center py-12">
                            <Satellite className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                            <h3 className="text-lg font-semibold text-slate-300 mb-2">No Assessment Selected</h3>
                            <p className="text-sm text-slate-500 mb-4">Upload imagery to generate an analysis report.</p>
                            <Button asChild variant="outline" size="sm">
                                <Link href="/upload">Go to Upload</Link>
                            </Button>
                        </CardContent>
                    </Card>
                )}
            </div>

            {/* Map */}
            <div className="flex-1 bg-[#0a0e1a] rounded-xl shadow-lg border border-white/[0.08] relative overflow-hidden flex flex-col">
                <div className="absolute top-4 left-0 right-0 z-10 px-4 flex justify-between items-start pointer-events-none">
                    <div className="bg-[#0c1122]/90 backdrop-blur-xl px-4 py-2 rounded-lg border border-white/[0.08] shadow-xl pointer-events-auto">
                        <h2 className="text-white font-semibold text-sm flex items-center">
                            <Navigation className="w-4 h-4 mr-2 text-cyan-400" />
                            Spatial Analysis View
                        </h2>
                    </div>
                    {currentAssessment?.location && (
                        <div className="bg-[#0c1122]/90 backdrop-blur-xl px-3 py-1.5 rounded-lg border border-white/[0.08] shadow-xl pointer-events-auto text-xs text-cyan-400 font-mono">
                            LAT: {currentAssessment.location.lat.toFixed(4)} | LNG: {currentAssessment.location.lng.toFixed(4)}
                        </div>
                    )}
                </div>

                {currentAssessment?.location ? (
                    <MapComponent
                        key={`${currentAssessment.location.lat}-${currentAssessment.location.lng}`}
                        geoJsonData={currentAssessment.results}
                        initialViewState={{
                            longitude: currentAssessment.location.lng,
                            latitude: currentAssessment.location.lat,
                            zoom: 15
                        }}
                    />
                ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 gap-3">
                        <Satellite className="w-10 h-10 text-slate-600" />
                        <p className="text-sm">Upload imagery to view spatial analysis</p>
                    </div>
                )}
            </div>
        </div>
    );
}
