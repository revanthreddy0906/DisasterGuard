"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Map as MapIcon,
    Upload,
    BarChart3,
    FileText,
    Settings,
    Satellite,
    Flame
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
    { icon: LayoutDashboard, label: "Dashboard", href: "/" },
    { icon: Upload, label: "Upload Data", href: "/upload" },
    { icon: MapIcon, label: "Spatial Analysis", href: "/analysis" },
    { icon: Flame, label: "Hotspots", href: "/hotspots" },
    { icon: BarChart3, label: "Analytics", href: "/analytics" },
    { icon: FileText, label: "Reports", href: "/reports" },
];

export function Sidebar() {
    const pathname = usePathname();

    return (
        <aside className="w-64 h-screen bg-[#0c1122]/90 backdrop-blur-xl text-white flex flex-col border-r border-white/[0.06] fixed left-0 top-0 z-50">
            {/* Logo */}
            <div className="h-16 flex items-center px-6 border-b border-white/[0.06]">
                <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                        <Satellite className="w-4 h-4 text-white" />
                    </div>
                    <span className="font-bold text-lg tracking-tight text-white">
                        Disaster<span className="text-cyan-400">Guard</span>
                    </span>
                </div>
            </div>

            {/* Navigation */}
            <nav className="flex-1 py-6 px-3 space-y-1">
                {navItems.map((item) => {
                    const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            className={cn(
                                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 relative",
                                isActive
                                    ? "bg-gradient-to-r from-cyan-500/15 to-violet-500/10 text-cyan-300 shadow-sm"
                                    : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]"
                            )}
                        >
                            {isActive && (
                                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full bg-gradient-to-b from-cyan-400 to-violet-500" />
                            )}
                            <item.icon className={cn("w-[18px] h-[18px]", isActive && "text-cyan-400")} />
                            {item.label}
                        </Link>
                    );
                })}
            </nav>

            {/* Footer */}
            <div className="p-4 border-t border-white/[0.06]">
                <button className="flex items-center gap-3 px-3 py-2.5 w-full text-slate-400 hover:text-slate-200 hover:bg-white/[0.04] rounded-lg text-sm font-medium transition-all duration-200">
                    <Settings className="w-[18px] h-[18px]" />
                    Settings
                </button>
            </div>
        </aside>
    );
}
