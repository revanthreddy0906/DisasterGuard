"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { ArrowRight, BarChart3, Upload, Layers, AlertTriangle, Calendar, MapPin, Satellite } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";
import { useAssessment } from "@/context/AssessmentContext";
import { Badge } from "@/components/ui/badge";

export default function Dashboard() {
    const { assessments, isBackendOnline } = useAssessment();

    const totalAssessments = assessments.length;

    const totalBuildings = assessments.reduce((acc, curr) => {
        return acc + (curr.results ? 1 : 0);
    }, 0);

    const criticalDamage = assessments.filter(a =>
        a.results?.damage_class === 'destroyed' || a.results?.damage_class === 'severe-damage'
    ).length;

    const activeProjects = assessments.filter(a => a.status === 'processing').length;

    const damageCounts = { destroyed: 0, severe: 0, noDamage: 0 };
    assessments.forEach(a => {
        if (a.results) {
            if (a.results.damage_class === 'destroyed') damageCounts.destroyed++;
            else if (a.results.damage_class === 'severe-damage') damageCounts.severe++;
            else if (a.results.damage_class === 'no-damage') damageCounts.noDamage++;
        }
    });

    const chartData = [
        { name: 'No Damage', value: damageCounts.noDamage },
        { name: 'Severe', value: damageCounts.severe },
        { name: 'Destroyed', value: damageCounts.destroyed },
    ];

    return (
        <div className="space-y-8">
            {/* Page header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Dashboard</h1>
                    <p className="text-slate-400 mt-1">Overview of disaster assessment operations.</p>
                </div>
                <div className="flex items-center gap-3">
                    <Badge variant={isBackendOnline ? "success" : "destructive"} className="text-[10px]">
                        {isBackendOnline ? "● API Online" : "● API Offline"}
                    </Badge>
                    <Button asChild>
                        <Link href="/upload">
                            New Assessment <ArrowRight className="ml-2 h-4 w-4" />
                        </Link>
                    </Button>
                </div>
            </div>

            {/* Stats cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Total Assessments</CardTitle>
                        <div className="p-2 rounded-lg bg-cyan-500/10">
                            <Layers className="h-4 w-4 text-cyan-400" />
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{totalAssessments}</div>
                        <p className="text-xs text-slate-500 mt-1">
                            {assessments.length > 0 ? "Latest: " + (assessments[0].location?.name || assessments[0].name) : "No data yet"}
                        </p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Images Processed</CardTitle>
                        <div className="p-2 rounded-lg bg-violet-500/10">
                            <Upload className="h-4 w-4 text-violet-400" />
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{totalBuildings}</div>
                        <p className="text-xs text-slate-500 mt-1">Across {totalAssessments} assessments</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Critical Damage</CardTitle>
                        <div className="p-2 rounded-lg bg-red-500/10">
                            <AlertTriangle className="h-4 w-4 text-red-400" />
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-red-400">{criticalDamage}</div>
                        <p className="text-xs text-slate-500 mt-1">Destroyed or Severe</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium text-slate-400">Active Processing</CardTitle>
                        <div className="p-2 rounded-lg bg-amber-500/10">
                            <BarChart3 className="h-4 w-4 text-amber-400" />
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold text-white">{activeProjects}</div>
                        <p className="text-xs text-slate-500 mt-1">Jobs in queue</p>
                    </CardContent>
                </Card>
            </div>

            {/* Charts & Recent */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                {/* Chart */}
                <Card className="col-span-4">
                    <CardHeader>
                        <CardTitle className="text-lg">Damage Distribution</CardTitle>
                        <CardDescription>
                            Aggregated damage classification across all assessments.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="pl-2">
                        <div className="h-[300px]">
                            {totalAssessments > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={chartData}>
                                        <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} stroke="#64748b" />
                                        <YAxis fontSize={12} tickLine={false} axisLine={false} stroke="#64748b" />
                                        <Tooltip
                                            contentStyle={{
                                                background: '#151d33',
                                                border: '1px solid rgba(255,255,255,0.1)',
                                                borderRadius: '8px',
                                                color: '#f1f5f9'
                                            }}
                                        />
                                        <Bar dataKey="value" fill="url(#barGradient)" radius={[6, 6, 0, 0]} />
                                        <defs>
                                            <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="0%" stopColor="#06b6d4" />
                                                <stop offset="100%" stopColor="#8b5cf6" />
                                            </linearGradient>
                                        </defs>
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-3">
                                    <Satellite className="w-10 h-10 text-slate-600" />
                                    <p className="text-sm">No assessment data available.</p>
                                    <Button asChild variant="outline" size="sm">
                                        <Link href="/upload">Upload Imagery</Link>
                                    </Button>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Recent Assessments */}
                <Card className="col-span-3">
                    <CardHeader>
                        <CardTitle className="text-lg">Recent Assessments</CardTitle>
                        <CardDescription>
                            Latest upload and analysis activity.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-5">
                            {assessments.length === 0 ? (
                                <div className="text-center py-8 text-slate-500">
                                    <p className="text-sm">No recent activity.</p>
                                    <p className="text-xs text-slate-600 mt-1">Start by uploading satellite imagery.</p>
                                </div>
                            ) : (
                                assessments.slice(0, 5).map((assessment, i) => (
                                    <div key={i} className="flex items-center">
                                        <div className="h-9 w-9 rounded-lg bg-white/[0.05] flex items-center justify-center border border-white/[0.08] shrink-0">
                                            <MapPin className="h-4 w-4 text-slate-400" />
                                        </div>
                                        <div className="ml-4 space-y-1 overflow-hidden">
                                            <p className="text-sm font-medium leading-none text-slate-200 truncate">{assessment.name}</p>
                                            <p className="text-xs text-slate-500 truncate">
                                                {assessment.location?.name || 'Unknown Location'}
                                            </p>
                                        </div>
                                        <div className="ml-auto font-medium pl-2">
                                            <Badge variant={assessment.status === 'complete' ? 'success' : assessment.status === 'failed' ? 'destructive' : 'default'}>
                                                {assessment.status}
                                            </Badge>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
