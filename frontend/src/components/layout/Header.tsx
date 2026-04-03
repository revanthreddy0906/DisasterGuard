"use client";

import { Bell, Search, User } from "lucide-react";
import { useAssessment } from "@/context/AssessmentContext";

export function Header() {
    const { isDemoMode, setIsDemoMode } = useAssessment();
    return (
        <header className="h-16 bg-[#0c1122]/80 backdrop-blur-xl border-b border-white/[0.06] flex items-center justify-between px-8 sticky top-0 z-40">
            {/* Search */}
            <div className="flex items-center gap-4 w-1/3">
                <div className="relative w-full max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search projects, regions..."
                        className="w-full pl-9 pr-4 py-2 text-sm rounded-lg bg-white/[0.04] border border-white/[0.08] text-slate-300 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500/50 focus:ring-2 focus:ring-cyan-500/20 transition-all duration-200"
                    />
                </div>
            </div>

            {/* Right section */}
            <div className="flex items-center gap-4">
                <button 
                    onClick={() => setIsDemoMode(!isDemoMode)}
                    className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-colors ${
                        isDemoMode 
                            ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30' 
                            : 'bg-white/5 text-slate-400 border-white/10 hover:text-slate-300'
                    }`}
                >
                    {isDemoMode ? 'Demo Mode On' : 'Demo Mode Off'}
                </button>

                <div className="h-6 w-px bg-white/[0.08] mx-1"></div>

                <button className="relative p-2 text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] rounded-lg transition-all duration-200">
                    <Bell className="w-5 h-5" />
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-cyan-400 rounded-full"></span>
                </button>

                <div className="h-6 w-px bg-white/[0.08] mx-1"></div>

                <div className="flex items-center gap-3 pl-2">
                    <div className="text-right hidden md:block">
                        <p className="text-sm font-semibold text-slate-200">Abhinav R.</p>
                        <p className="text-xs text-slate-500">Lead Analyst</p>
                    </div>
                    <div className="w-9 h-9 bg-gradient-to-br from-cyan-500/20 to-violet-500/20 rounded-lg flex items-center justify-center border border-white/[0.08] text-cyan-400">
                        <User className="w-5 h-5" />
                    </div>
                </div>
            </div>
        </header>
    );
}
