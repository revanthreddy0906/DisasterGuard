"use client";

import { useDropzone, type FileRejection } from "react-dropzone";
import { UploadCloud } from "lucide-react";
import { cn, formatBytes } from "@/lib/utils";

interface DropzoneProps {
    onDrop: (acceptedFiles: File[], rejectedFiles: FileRejection[]) => void;
    accept?: Record<string, string[]>;
    maxSize?: number;
    maxFiles?: number;
}

export function Dropzone({ onDrop, accept, maxSize = 10 * 1024 * 1024, maxFiles }: DropzoneProps) {
    const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
        onDrop,
        accept,
        maxSize,
        maxFiles,
    });

    return (
        <div
            {...getRootProps()}
            className={cn(
                "border-2 border-dashed rounded-xl p-10 transition-all duration-200 cursor-pointer flex flex-col items-center justify-center text-center gap-4",
                isDragActive && "border-cyan-500/60 bg-cyan-500/5 scale-[0.99]",
                isDragReject && "border-red-500/60 bg-red-500/5",
                !isDragActive && "border-white/10 bg-white/[0.02] hover:border-cyan-500/30 hover:bg-white/[0.04]"
            )}
        >
            <input {...getInputProps()} />
            <div className={cn(
                "p-4 rounded-full bg-white/[0.05] mb-2 transition-colors",
                isDragActive && "bg-cyan-500/10"
            )}>
                <UploadCloud className={cn(
                    "w-8 h-8 text-slate-500",
                    isDragActive && "text-cyan-400"
                )} />
            </div>
            <div>
                <p className="text-lg font-semibold text-slate-200">
                    {isDragActive ? "Drop files here" : "Drag & drop files here"}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                    or click to select files
                </p>
            </div>
            <div className="flex gap-4 text-xs text-slate-500 font-medium">
                <span>Max size: {formatBytes(maxSize)}</span>
                {maxFiles ? <span>Max files: {maxFiles}</span> : null}
                <span>Formats: JPG, PNG, TIFF</span>
            </div>
        </div>
    );
}
