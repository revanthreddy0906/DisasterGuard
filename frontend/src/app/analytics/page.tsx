"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, Share2, BarChart2, PieChart as PieIcon, TrendingUp } from "lucide-react";
import { ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, Legend, LineChart, Line } from "recharts";
import { useAssessment } from "@/context/AssessmentContext";
import Link from "next/link";

const COLORS = ['#10b981', '#f59e0b', '#ef4444'];

const darkTooltipStyle = {
    background: '#151d33',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '8px',
    color: '#f1f5f9'
};

export default function AnalyticsPage() {
    const { assessments } = useAssessment();

    const damageCounts = { destroyed: 0, severe: 0, noDamage: 0 };
    const regionImpactData: Array<{
        name: string;
        confidence: number;
        critical: number;
    }> = [];

    assessments.forEach(a => {
        if (a.results) {
            if (a.results.damage_class === 'destroyed') damageCounts.destroyed++;
            else if (a.results.damage_class === 'severe-damage') damageCounts.severe++;
            else if (a.results.damage_class === 'no-damage') damageCounts.noDamage++;

            regionImpactData.push({
                name: a.location?.name?.split(',')[0] || a.name,
                confidence: Math.round(a.results.confidence * 100),
                critical: a.results.damage_class === 'destroyed' || a.results.damage_class === 'severe-damage' ? 1 : 0
            });
        }
    });

    const pieData = [
        { name: 'No Damage', value: damageCounts.noDamage },
        { name: 'Severe Damage', value: damageCounts.severe },
        { name: 'Destroyed', value: damageCounts.destroyed },
    ].filter(d => d.value > 0);

    const velocityData = assessments.map((a, i) => ({
        name: `Job ${i + 1}`,
        confidence: a.results ? Math.round(a.results.confidence * 100) : 0
    }));

    if (assessments.length === 0) {
        return (
            <div className="h-[calc(100vh-6rem)] flex items-center justify-center">
                <Card className="max-w-md w-full">
                    <CardContent className="flex flex-col items-center justify-center py-12 text-slate-500">
                        <BarChart2 className="w-12 h-12 mb-4 text-slate-600" />
                        <h3 className="text-lg font-semibold text-slate-300 mb-2">No Analytics Available</h3>
                        <p className="text-sm text-center mb-4">Upload imagery to generate insights and analytics.</p>
                        <Button asChild variant="outline" size="sm">
                            <Link href="/upload">Upload Imagery</Link>
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-white">Analytics</h1>
                    <p className="text-slate-400 mt-1">Deep dive into damage assessment metrics and trends.</p>
                </div>
                <div className="flex gap-3">
                    <Button variant="outline">
                        <Share2 className="mr-2 h-4 w-4" /> Share
                    </Button>
                    <Button>
                        <Download className="mr-2 h-4 w-4" /> Export Report
                    </Button>
                </div>
            </div>

            {/* Charts grid */}
            <div className="grid gap-4 md:grid-cols-2">
                {/* Pie Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-lg">
                            <PieIcon className="w-4 h-4 text-cyan-400" /> Damage Distribution
                        </CardTitle>
                        <CardDescription>Proportion of damage classes identified.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={pieData}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        fill="#8884d8"
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {pieData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip contentStyle={darkTooltipStyle} />
                                    <Legend wrapperStyle={{ color: '#94a3b8' }} />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Bar Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-lg">
                            <BarChart2 className="w-4 h-4 text-violet-400" /> Confidence by Region
                        </CardTitle>
                        <CardDescription>Model confidence score by assessment.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={regionImpactData}>
                                    <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} stroke="#64748b" />
                                    <YAxis fontSize={12} tickLine={false} axisLine={false} stroke="#64748b" />
                                    <Tooltip contentStyle={darkTooltipStyle} />
                                    <Legend wrapperStyle={{ color: '#94a3b8' }} />
                                    <Bar dataKey="confidence" name="Confidence %" fill="url(#barGradient2)" radius={[6, 6, 0, 0]} />
                                    <defs>
                                        <linearGradient id="barGradient2" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="0%" stopColor="#8b5cf6" />
                                            <stop offset="100%" stopColor="#06b6d4" />
                                        </linearGradient>
                                    </defs>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Line Chart */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-lg">
                        <TrendingUp className="w-4 h-4 text-emerald-400" /> Model Confidence Trend
                    </CardTitle>
                    <CardDescription>Confidence scores across sequential assessments.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-[250px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={velocityData}>
                                <XAxis dataKey="name" fontSize={12} tickLine={false} axisLine={false} stroke="#64748b" />
                                <YAxis fontSize={12} tickLine={false} axisLine={false} stroke="#64748b" />
                                <Tooltip contentStyle={darkTooltipStyle} />
                                <Line type="monotone" dataKey="confidence" stroke="#06b6d4" strokeWidth={3} dot={{ r: 4, fill: '#06b6d4' }} activeDot={{ r: 8 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
