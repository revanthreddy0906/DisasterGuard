import * as React from "react"
import { cn } from "@/lib/utils"
import { Slot } from "@radix-ui/react-slot"

export interface ButtonProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link"
    size?: "default" | "sm" | "lg" | "icon"
    asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant = "default", size = "default", asChild = false, ...props }, ref) => {
        const Comp = asChild ? Slot : "button"
        return (
            <Comp
                ref={ref}
                className={cn(
                    "inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-500/50 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a0e1a] disabled:pointer-events-none disabled:opacity-50 cursor-pointer",
                    {
                        "bg-gradient-to-r from-cyan-500 to-violet-600 text-white hover:from-cyan-400 hover:to-violet-500 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/30": variant === "default",
                        "bg-gradient-to-r from-red-500 to-orange-500 text-white hover:from-red-400 hover:to-orange-400 shadow-lg shadow-red-500/20": variant === "destructive",
                        "border border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white hover:border-white/20": variant === "outline",
                        "bg-white/10 text-slate-200 hover:bg-white/15 hover:text-white": variant === "secondary",
                        "text-slate-300 hover:bg-white/5 hover:text-white": variant === "ghost",
                        "text-cyan-400 underline-offset-4 hover:underline hover:text-cyan-300": variant === "link",
                        "h-10 px-5 py-2": size === "default",
                        "h-9 rounded-md px-3 text-xs": size === "sm",
                        "h-11 rounded-lg px-8 text-base": size === "lg",
                        "h-10 w-10": size === "icon",
                    },
                    className
                )}
                {...props}
            />
        )
    }
)
Button.displayName = "Button"

export { Button }
