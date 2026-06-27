'use client';

import { useRef, useCallback } from 'react';
import html2canvas from 'html2canvas';
import { AnalysisResult } from '../lib/types';
import PokemonCard from './PokemonCard';
import ShareButtons from './ShareButtons';

interface ResultScreenProps {
  result: AnalysisResult;
  onReset: () => void;
}

export default function ResultScreen({ result, onReset }: ResultScreenProps) {
  const cardRef = useRef<HTMLDivElement>(null);

  const captureCard = useCallback(async (): Promise<Blob | null> => {
    if (!cardRef.current) return null;
    try {
      const canvas = await html2canvas(cardRef.current, {
        backgroundColor: '#0a0a0a',
        scale: 2,
        useCORS: true,
        logging: false,
      });
      return new Promise((resolve) => {
        canvas.toBlob((blob) => resolve(blob), 'image/png');
      });
    } catch {
      return null;
    }
  }, []);

  return (
    <div className="flex flex-col items-center min-h-[80vh] px-4 py-8">
      <div className="card-flip mb-6">
        <PokemonCard ref={cardRef} result={result} />
      </div>

      <ShareButtons
        onCapture={captureCard}
        name={result.name}
        percentage={result.guruPercentage}
      />

      <button
        onClick={onReset}
        className="mt-6 text-gray-500 hover:text-gray-300 text-sm transition-all"
      >
        🔍 Analisar Outro Suspeito
      </button>
    </div>
  );
}
