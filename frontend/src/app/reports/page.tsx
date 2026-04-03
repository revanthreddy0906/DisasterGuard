"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FileText, Download, Calendar, MapPin, Search, AlertTriangle, Eye } from "lucide-react";
import { useAssessment } from "@/context/AssessmentContext";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function ReportsPage() {
    const { assessments, setCurrentAssessment } = useAssessment();
    const router = useRouter();

    const handleViewAnalysis = (assessment: any) => {
        setCurrentAssessment(assessment);
        router.push('/analysis');
    };

    return (
        <div className="space-y-8 max-w-6xl mx-auto pb-10">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Reports & Insights</h1>
                    <p className="text-slate-400 mt-1">Detailed damage summaries and actionable intelligence.</p>
                </div>
                <div className="flex gap-2">
                    <div className="relative">
                        <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
                        <input
                            type="text"
                            placeholder="Search location..."
                            className="h-9 pl-9 pr-4 rounded-lg border border-white/10 bg-white/[0.04] text-sm text-slate-300 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 focus:border-cyan-500/50 w-64 transition-all"
                        />
                    </div>
                </div>
            </div>

            <div className="grid gap-6">
                {assessments.length === 0 ? (
                    <div className="text-center py-20 bg-white/[0.02] rounded-xl border border-dashed border-white/10">
                        <FileText className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                        <h3 className="text-lg font-medium text-slate-300">No Reports Generated</h3>
                        <p className="text-slate-500 text-sm mt-1">Upload imagery to process new reports.</p>
                        <Button asChild className="mt-4" variant="outline">
                            <Link href="/upload">Go to Upload</Link>
                        </Button>
                    </div>
                ) : (
                    assessments.filter(a => a.status === 'complete').map((assessment) => {
                        const damageClass = assessment.results?.damage_class || 'unknown';
                        const confidence = assessment.results?.confidence || 0;
                        const isCritical = damageClass === 'destroyed' || damageClass === 'severe-damage';
                        const priority = damageClass === 'destroyed' ? "Critical" : isCritical ? "High" : "Low";

                        return (
                            <Card key={assessment.id} className="overflow-hidden hover:border-white/15 transition-colors">
                                <div className={`flex flex-col lg:flex-row border-l-4 ${
                                    damageClass === 'destroyed' ? 'border-l-red-500' :
                                    damageClass === 'severe-damage' ? 'border-l-orange-500' :
                                    'border-l-emerald-500'
                                }`}>
                                    {/* Content */}
                                    <div className="p-6 flex-1 min-w-0">
                                        <div className="flex items-start justify-between mb-4">
                                            <div>
                                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                                    {assessment.name}
                                                </h3>
                                                <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                                                    <span className="flex items-center gap-1.5">
                                                        <MapPin className="w-4 h-4 text-slate-500" />
                                                        {assessment.location?.name}
                                                    </span>
                                                    <span className="flex items-center gap-1.5">
                                                        <Calendar className="w-4 h-4 text-slate-500" />
                                                        {new Date(assessment.date).toLocaleDateString()}
                                                    </span>
                                                </div>
                                            </div>
                                            <Badge
                                                variant={priority === 'Critical' ? 'destructive' : priority === 'High' ? 'warning' : 'success'}
                                                className="ml-2 uppercase text-[10px] tracking-wider"
                                            >
                                                {priority} Priority
                                            </Badge>
                                        </div>

                                        {/* Stats */}
                                        <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-4 grid grid-cols-2 lg:grid-cols-4 gap-4">
                                            <div>
                                                <p className="text-xs font-semibold text-slate-500 uppercase">Classification</p>
                                                <p className={`text-sm font-medium mt-1 capitalize ${
                                                    damageClass === 'destroyed' ? 'text-red-400' :
                                                    damageClass === 'severe-damage' ? 'text-orange-400' :
                                                    'text-emerald-400'
                                                }`}>{damageClass.replace('-', ' ')}</p>
                                            </div>
                                            <div>
                                                <p className="text-xs font-semibold text-slate-500 uppercase">Confidence</p>
                                                <p className="text-sm font-medium text-slate-200 mt-1">{(confidence * 100).toFixed(1)}%</p>
                                            </div>
                                            <div>
                                                <p className="text-xs font-semibold text-slate-500 uppercase">Status</p>
                                                <p className="text-sm font-medium text-slate-200 mt-1 capitalize">{assessment.status}</p>
                                            </div>
                                            <div>
                                                <p className="text-xs font-semibold text-slate-500 uppercase">Recommendation</p>
                                                <p className="text-sm font-medium text-slate-300 mt-1 flex items-center gap-1.5">
                                                    {isCritical ? (
                                                        <>
                                                            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                                                            <span>Response team required</span>
                                                        </>
                                                    ) : (
                                                        <span className="text-emerald-400">No action required</span>
                                                    )}
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="p-6 bg-white/[0.02] border-t lg:border-t-0 lg:border-l border-white/[0.06] flex flex-row lg:flex-col items-center justify-center gap-3 w-full lg:w-[200px] shrink-0">
                                        <Button
                                            className="w-full"
                                            onClick={() => handleViewAnalysis(assessment)}
                                        >
                                            <Eye className="mr-2 h-4 w-4" /> View Analysis
                                        </Button>
                                        <Button variant="outline" className="w-full">
                                            <Download className="mr-2 h-4 w-4" /> Download PDF
                                        </Button>
                                    </div>
                                </div>
                            </Card>
                        );
                    })
                )}
            </div>
        </div>
    );
}
