'use client';

import { useState, useCallback } from 'react';
import { AppStep, AnalysisResult } from './lib/types';
import StartScreen from './components/StartScreen';
import InputScreen from './components/InputScreen';
import LoadingScreen from './components/LoadingScreen';
import AdjustScreen from './components/AdjustScreen';
import ResultScreen from './components/ResultScreen';

export default function Home() {
  const [step, setStep] = useState<AppStep>('start');
  const [handle, setHandle] = useState('');
  const [, setUploadedPhoto] = useState<string | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(async (inputHandle: string, photo: string | null) => {
    setHandle(inputHandle);
    setUploadedPhoto(photo);
    setStep('loading');
    setError(null);

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 50000);

      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ handle: inputHandle, photo }),
        signal: controller.signal,
      });

      clearTimeout(timeout);

      if (!res.ok) {
        throw new Error('Falha na análise');
      }

      const data: AnalysisResult = await res.json();

      // Override photo if user uploaded one
      if (photo) {
        data.photo = photo;
      }

      setAnalysisResult(data);
      setStep('adjust');
    } catch (err) {
      console.error('Analysis error:', err);
      setError('Não foi possível completar a análise. Tente novamente.');
      setStep('input');
    }
  }, []);

  const handleConfirm = useCallback((result: AnalysisResult) => {
    setAnalysisResult(result);
    setStep('result');
  }, []);

  const handleReset = useCallback(() => {
    setStep('start');
    setHandle('');
    setUploadedPhoto(null);
    setAnalysisResult(null);
    setError(null);
  }, []);

  return (
    <main className="max-w-2xl mx-auto">
      {step === 'start' && (
        <StartScreen onStart={() => setStep('input')} />
      )}

      {step === 'input' && (
        <>
          <InputScreen onSubmit={handleSubmit} onBack={() => setStep('start')} />
          {error && (
            <div className="text-center text-red-500 text-sm mt-4 px-4">
              ⚠️ {error}
            </div>
          )}
        </>
      )}

      {step === 'loading' && (
        <LoadingScreen handle={handle} />
      )}

      {step === 'adjust' && analysisResult && (
        <AdjustScreen
          result={analysisResult}
          onConfirm={handleConfirm}
          onBack={() => setStep('input')}
        />
      )}

      {step === 'result' && analysisResult && (
        <ResultScreen result={analysisResult} onReset={handleReset} />
      )}
    </main>
  );
}
