import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { cn } from "@/lib/utils";
import { AssessmentProvider } from "@/context/AssessmentContext";

const inter = Inter({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "DisasterGuard Enterprise",
  description: "Geospatial AI Damage Assessment Platform — Satellite imagery analysis powered by deep learning",
};

import { PageTransition } from "@/components/layout/PageTransition";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={cn(inter.className, "bg-[#0a0e1a] text-slate-100 overflow-hidden antialiased")}>
        {/* Animated gradient mesh background */}
        <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden" aria-hidden="true">
          <div className="absolute -top-[40%] -left-[20%] w-[70%] h-[70%] rounded-full bg-cyan-500/[0.03] blur-[120px] animate-float-slow" />
          <div className="absolute -bottom-[30%] -right-[20%] w-[60%] h-[60%] rounded-full bg-violet-500/[0.04] blur-[120px] animate-float-slow-reverse" />
          <div className="absolute top-[20%] right-[10%] w-[40%] h-[40%] rounded-full bg-indigo-500/[0.02] blur-[100px] animate-float-slower" />
        </div>

        <AssessmentProvider>
          <div className="flex h-screen relative z-10">
            <Sidebar />
            <div className="flex-1 flex flex-col pl-64 transition-all duration-300">
              <Header />
              <main className="flex-1 overflow-auto p-8 relative">
                <PageTransition>
                  {children}
                </PageTransition>
              </main>
            </div>
          </div>
        </AssessmentProvider>
      </body>
    </html>
  );
}
