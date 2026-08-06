'use client';

import { useState } from 'react';
import { AnalysisResult, CriterionScore } from '../lib/types';
import { CRITERIA, getVerdict, calculateGuruPercentage, getBarColor, formatFollowers, PLATFORM_ICONS, PLATFORM_COLORS } from '../lib/constants';

interface AdjustScreenProps {
  result: AnalysisResult;
  onConfirm: (result: AnalysisResult) => void;
  onBack: () => void;
}

export default function AdjustScreen({ result, onConfirm, onBack }: AdjustScreenProps) {
  const [criteria, setCriteria] = useState<CriterionScore[]>(result.criteria);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const percentage = calculateGuruPercentage(criteria);
  const verdict = getVerdict(percentage);

  const adjustScore = (id: string, delta: number) => {
    setCriteria((prev) =>
      prev.map((c) =>
        c.id === id ? { ...c, score: Math.max(0, Math.min(10, c.score + delta)) } : c
      )
    );
  };

  const handleConfirm = () => {
    const updated: AnalysisResult = {
      ...result,
      criteria,
      guruPercentage: percentage,
      verdict,
    };
    onConfirm(updated);
  };

  return (
    <div className="flex flex-col items-center min-h-[80vh] px-4 py-8">
      <div className="fade-in w-full max-w-lg">
        <button onClick={onBack} className="text-gray-500 hover:text-gray-300 text-sm mb-4">
          ← Voltar
        </button>

        {/* Header with photo and info */}
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-full bg-gray-800 border-2 border-green-500/30 overflow-hidden flex-shrink-0">
            {result.photo ? (
              <img src={result.photo} alt={result.name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-2xl">👤</div>
            )}
          </div>
          <div className="min-w-0">
            <h2 className="text-lg font-bold text-green-500 truncate">{result.name}</h2>
            <p className="text-xs text-gray-500 truncate">{result.bio}</p>
            {result.followersEstimate > 0 && (
              <p className="text-xs text-gray-400 mt-1">
                ~{formatFollowers(result.followersEstimate)} seguidores
              </p>
            )}
          </div>
        </div>

        {/* Social profiles */}
        {result.socials.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-6">
            {result.socials.map((social) => (
              <span
                key={social.platform}
                className={`${PLATFORM_COLORS[social.platform]} text-white text-xs px-2 py-1 rounded flex items-center gap-1`}
              >
                {PLATFORM_ICONS[social.platform]} @{social.handle}
              </span>
            ))}
          </div>
        )}

        {/* Live verdict preview */}
        <div className="border rounded p-4 mb-6 text-center" style={{ borderColor: verdict.color + '40' }}>
          <div className="text-3xl mb-1">{verdict.emoji}</div>
          <div className="text-2xl font-bold" style={{ color: verdict.color }}>
            {percentage}% GURU
          </div>
          <div className="text-sm font-bold" style={{ color: verdict.color }}>
            {verdict.title}
          </div>
        </div>

        {/* Criteria with adjustable scores */}
        <div className="space-y-3 mb-6">
          <h3 className="text-xs text-green-500/60 uppercase tracking-wider">{`// Critérios de Análise`}</h3>
          {criteria.map((criterion) => {
            const meta = CRITERIA.find((c) => c.id === criterion.id);
            return (
              <div key={criterion.id} className="border border-gray-800 rounded p-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-bold text-gray-300">{criterion.label}</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => adjustScore(criterion.id, -1)}
                      className="w-7 h-7 rounded bg-gray-800 hover:bg-gray-700 text-green-500 font-bold text-sm flex items-center justify-center"
                    >
                      −
                    </button>
                    <span className="text-sm font-bold w-6 text-center" style={{ color: criterion.score <= 3 ? '#22c55e' : criterion.score <= 6 ? '#eab308' : '#ef4444' }}>
                      {criterion.score}
                    </span>
                    <button
                      onClick={() => adjustScore(criterion.id, 1)}
                      className="w-7 h-7 rounded bg-gray-800 hover:bg-gray-700 text-red-500 font-bold text-sm flex items-center justify-center"
                    >
                      +
                    </button>
                  </div>
                </div>
                {/* Bar */}
                <div className="h-2 bg-gray-800 rounded overflow-hidden mb-1">
                  <div
                    className={`h-full rounded transition-all duration-300 ${getBarColor(criterion.score)}`}
                    style={{ width: `${criterion.score * 10}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-gray-600">
                  <span>{meta?.lowLabel}</span>
                  <span>{meta?.highLabel}</span>
                </div>
                {/* Expandable justification */}
                <button
                  onClick={() => setExpandedId(expandedId === criterion.id ? null : criterion.id)}
                  className="text-xs text-gray-500 hover:text-gray-300 mt-1"
                >
                  {expandedId === criterion.id ? '▼' : '▶'} Justificativa da IA
                </button>
                {expandedId === criterion.id && (
                  <p className="text-xs text-gray-500 mt-1 pl-3 border-l border-gray-700">
                    {criterion.justification}
                  </p>
                )}
              </div>
            );
          })}
        </div>

        {/* Flags */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {result.redFlags.length > 0 && (
            <div className="border border-red-900/30 rounded p-3">
              <h4 className="text-xs text-red-500 font-bold mb-2">🚩 Red Flags</h4>
              <ul className="text-xs text-gray-400 space-y-1">
                {result.redFlags.map((flag, i) => (
                  <li key={i}>• {flag}</li>
                ))}
              </ul>
            </div>
          )}
          {result.greenFlags.length > 0 && (
            <div className="border border-green-900/30 rounded p-3">
              <h4 className="text-xs text-green-500 font-bold mb-2">✅ Green Flags</h4>
              <ul className="text-xs text-gray-400 space-y-1">
                {result.greenFlags.map((flag, i) => (
                  <li key={i}>• {flag}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <button
          onClick={handleConfirm}
          className="w-full bg-red-600 hover:bg-red-500 text-white font-bold py-3 rounded transition-all duration-200 hover:shadow-[0_0_20px_rgba(239,68,68,0.4)] tracking-wider text-sm uppercase"
        >
          [ GERAR CARD DE POKÉMON ]
        </button>
      </div>
    </div>
  );
}
