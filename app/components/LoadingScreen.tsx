'use client';

import { useState, useEffect } from 'react';
import { LOADING_PHASES } from '../lib/constants';

interface LoadingScreenProps {
  handle: string;
}

export default function LoadingScreen({ handle }: LoadingScreenProps) {
  const [phaseIndex, setPhaseIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setPhaseIndex((prev) => {
        if (prev < LOADING_PHASES.length - 1) return prev + 1;
        return prev;
      });
    }, 2500);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
      <div className="fade-in text-center">
        {/* Radar */}
        <div className="relative w-48 h-48 mx-auto mb-8">
          {/* Radar circles */}
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="absolute inset-0 rounded-full border border-green-500/20 radar-pulse"
              style={{
                transform: `scale(${0.4 + i * 0.2})`,
                animationDelay: `${i * 0.3}s`,
              }}
            />
          ))}
          {/* Radar sweep */}
          <div className="absolute inset-0 radar-spin">
            <div
              className="absolute top-1/2 left-1/2 w-1/2 h-0.5 origin-left"
              style={{
                background: 'linear-gradient(to right, rgba(34,197,94,0.8), transparent)',
              }}
            />
          </div>
          {/* Center dot */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-green-500 rounded-full shadow-[0_0_10px_rgba(34,197,94,0.6)]" />
          {/* Blips */}
          {phaseIndex > 1 && (
            <div className="absolute top-[30%] left-[60%] w-2 h-2 bg-red-500 rounded-full radar-pulse" />
          )}
          {phaseIndex > 3 && (
            <div className="absolute top-[60%] left-[35%] w-2 h-2 bg-yellow-500 rounded-full radar-pulse" style={{ animationDelay: '0.5s' }} />
          )}
          {phaseIndex > 5 && (
            <div className="absolute top-[45%] left-[70%] w-2 h-2 bg-red-400 rounded-full radar-pulse" style={{ animationDelay: '1s' }} />
          )}
        </div>

        <h2 className="text-lg font-bold text-green-500 mb-2 tracking-wider">
          ANALISANDO: {handle.toUpperCase()}
        </h2>

        <div className="max-w-sm mx-auto space-y-2 mb-6">
          {LOADING_PHASES.map((phase, i) => (
            <div
              key={phase}
              className={`text-xs transition-all duration-500 flex items-center gap-2 justify-center ${
                i < phaseIndex ? 'text-green-500/50' : i === phaseIndex ? 'text-green-400' : 'text-gray-700'
              }`}
            >
              <span>{i < phaseIndex ? '✓' : i === phaseIndex ? '►' : '○'}</span>
              <span>{phase}</span>
            </div>
          ))}
        </div>

        {/* Progress bar */}
        <div className="w-64 mx-auto h-1 bg-gray-800 rounded overflow-hidden">
          <div
            className="h-full bg-green-500 transition-all duration-1000 ease-out"
            style={{ width: `${((phaseIndex + 1) / LOADING_PHASES.length) * 100}%` }}
          />
        </div>

        <p className="text-xs text-gray-600 mt-4">
          Isso pode levar alguns segundos...
        </p>
      </div>
    </div>
  );
}
