"use client";

import { useMemo } from 'react';
import Map, { Marker, Popup } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapPin, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';
import type { StyleSpecification } from 'maplibre-gl';
import type { PredictionResult } from '@/lib/api';

const MAP_STYLE = {
    version: 8,
    sources: {
        'esri-satellite': {
            type: 'raster',
            tiles: [
                'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
            ],
            tileSize: 256,
            attribution: 'Esri, Maxar, Earthstar Geographics'
        }
    },
    layers: [
        {
            id: 'background',
            type: 'background',
            paint: {
                'background-color': '#0a0e1a'
            }
        },
        {
            id: 'satellite-layer',
            type: 'raster',
            source: 'esri-satellite',
            minzoom: 0,
            maxzoom: 22
        }
    ]
};

interface MapComponentProps {
    initialViewState?: {
        longitude: number;
        latitude: number;
        zoom: number;
    };
    geoJsonData?: PredictionResult;
}

export function MapComponent({ initialViewState, geoJsonData }: MapComponentProps) {
    const [showPopup, setShowPopup] = useState(true);

    const damageInfo = useMemo(() => {
        if (!geoJsonData) return null;
        return {
            damage_class: geoJsonData.damage_class || 'unknown',
            confidence: geoJsonData.confidence || 0,
            probabilities: geoJsonData.probabilities || {}
        };
    }, [geoJsonData]);

    const hasCritical = damageInfo?.damage_class === 'destroyed' || damageInfo?.damage_class === 'severe-damage';

    return (
        <div className="relative w-full h-full rounded-xl overflow-hidden border border-white/[0.08] bg-[#0a0e1a] shadow-inner">
            <Map
                initialViewState={initialViewState || {
                    longitude: 0,
                    latitude: 20,
                    zoom: 2
                }}
                scrollZoom={true}
                dragPan={true}
                doubleClickZoom={true}
                boxZoom={true}
                style={{ width: '100%', height: '100%' }}
                mapStyle={MAP_STYLE as StyleSpecification}
            >
                {/* Location marker */}
                {initialViewState && (
                    <>
                        <Marker
                            longitude={initialViewState.longitude}
                            latitude={initialViewState.latitude}
                            anchor="bottom"
                            onClick={(e) => {
                                e.originalEvent.stopPropagation();
                                setShowPopup(!showPopup);
                            }}
                        >
                            <div className="flex flex-col items-center group cursor-pointer hover:scale-110 transition-transform">
                                <MapPin className={`w-10 h-10 drop-shadow-2xl ${hasCritical ? 'text-red-500 fill-red-500/20' : 'text-cyan-400 fill-cyan-400/20'}`} />
                            </div>
                        </Marker>

                        {showPopup && damageInfo && (
                            <Popup
                                longitude={initialViewState.longitude}
                                latitude={initialViewState.latitude}
                                anchor="top"
                                closeButton={false}
                                closeOnClick={false}
                                offset={10}
                                maxWidth="280px"
                                className="z-50"
                            >
                                <div className="p-0 font-sans">
                                    <div className={`flex items-center gap-2 px-4 py-3 rounded-t-xl border-b border-white/10 ${hasCritical ? 'bg-red-500/10' : 'bg-emerald-500/10'}`}>
                                        {hasCritical ? (
                                            <AlertTriangle className="w-4 h-4 text-red-400" />
                                        ) : (
                                            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                                        )}
                                        <span className={`font-bold text-sm ${hasCritical ? 'text-red-300' : 'text-emerald-300'}`}>
                                            {damageInfo.damage_class === 'destroyed' ? 'Destroyed' :
                                             damageInfo.damage_class === 'severe-damage' ? 'Severe Damage' :
                                             'No Damage Detected'}
                                        </span>
                                    </div>

                                    <div className="p-4 space-y-2.5">
                                        <div className="flex justify-between items-center text-xs">
                                            <span className="text-slate-400">Confidence</span>
                                            <span className="font-bold text-cyan-300">
                                                {(damageInfo.confidence * 100).toFixed(1)}%
                                            </span>
                                        </div>
                                        {Object.entries(damageInfo.probabilities).map(([cls, prob]) => (
                                            <div key={cls} className="space-y-1">
                                                <div className="flex justify-between text-xs">
                                                    <span className="text-slate-400 capitalize">{cls}</span>
                                                    <span className="text-slate-300">{((prob as number) * 100).toFixed(1)}%</span>
                                                </div>
                                                <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-violet-500"
                                                        style={{ width: `${(prob as number) * 100}%` }}
                                                    />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </Popup>
                        )}
                    </>
                )}
            </Map>
        </div>
    );
}
