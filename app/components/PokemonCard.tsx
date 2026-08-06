'use client';

import { forwardRef } from 'react';
import { AnalysisResult } from '../lib/types';
import { getBarColor, PLATFORM_ICONS, formatFollowers } from '../lib/constants';

interface PokemonCardProps {
  result: AnalysisResult;
}

const PokemonCard = forwardRef<HTMLDivElement, PokemonCardProps>(({ result }, ref) => {
  const { name, bio, photo, socials, criteria, guruPercentage, verdict } = result;
  const hp = 100 - guruPercentage;
  const cardNumber = String(Math.floor(Math.random() * 9999)).padStart(4, '0');

  return (
    <div
      ref={ref}
      className={`w-[380px] rounded-xl p-1 ${verdict.glowClass}`}
      style={{
        background: `linear-gradient(135deg, ${verdict.color}40, #1a1a1a, ${verdict.color}20)`,
      }}
    >
      <div className="bg-[#111] rounded-lg p-4 holographic relative overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2">
            <span className="text-lg">{verdict.emoji}</span>
            <h3 className="text-base font-bold text-white uppercase tracking-wider truncate max-w-[200px]">
              {name}
            </h3>
          </div>
          <div className="text-right">
            <span className="text-xs text-gray-500">HP</span>
            <span className="text-lg font-bold ml-1" style={{ color: hp > 50 ? '#22c55e' : hp > 25 ? '#eab308' : '#ef4444' }}>
              {hp}
            </span>
          </div>
        </div>

        {/* Type badge */}
        <div className="flex justify-between items-center mb-3">
          <span
            className="text-xs px-2 py-0.5 rounded-full font-bold"
            style={{ backgroundColor: verdict.color + '30', color: verdict.color }}
          >
            {verdict.emoji} {verdict.title}
          </span>
          <span className="text-xs text-gray-500">
            ~{formatFollowers(result.followersEstimate)} seguidores
          </span>
        </div>

        {/* Photo + Bio */}
        <div className="relative mb-3 rounded-lg overflow-hidden border border-gray-700/50">
          <div
            className="w-full h-40 flex items-center justify-center"
            style={{ background: `linear-gradient(180deg, ${verdict.color}15, #0a0a0a)` }}
          >
            {photo ? (
              <img src={photo} alt={name} className="w-28 h-28 rounded-full object-cover border-2" style={{ borderColor: verdict.color }} />
            ) : (
              <div className="w-28 h-28 rounded-full bg-gray-800 flex items-center justify-center text-5xl border-2" style={{ borderColor: verdict.color }}>
                👤
              </div>
            )}
          </div>
        </div>

        {/* Bio */}
        <p className="text-xs text-gray-400 mb-3 line-clamp-2 text-center italic">
          &ldquo;{bio}&rdquo;
        </p>

        {/* Social badges */}
        {socials.length > 0 && (
          <div className="flex flex-wrap gap-1 justify-center mb-3">
            {socials.map((s) => (
              <span key={s.platform} className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded">
                {PLATFORM_ICONS[s.platform]} {s.handle}
              </span>
            ))}
          </div>
        )}

        {/* Guru Percentage - BIG */}
        <div className="text-center mb-3 py-2 rounded-lg" style={{ backgroundColor: verdict.color + '10' }}>
          <div className="text-4xl font-bold" style={{ color: verdict.color }}>
            {guruPercentage}%
          </div>
          <div className="text-xs text-gray-400 uppercase tracking-wider">
            Chance de ser Guru
          </div>
        </div>

        {/* 8 Criteria bars */}
        <div className="space-y-1.5 mb-3">
          {criteria.map((c) => (
            <div key={c.id} className="flex items-center gap-2">
              <span className="text-[10px] text-gray-500 w-24 truncate text-right">{c.label}</span>
              <div className="flex-1 h-2 bg-gray-800 rounded overflow-hidden">
                <div
                  className={`h-full rounded ${getBarColor(c.score)}`}
                  style={{ width: `${c.score * 10}%` }}
                />
              </div>
              <span className="text-[10px] font-bold w-4 text-right" style={{ color: c.score <= 3 ? '#22c55e' : c.score <= 6 ? '#eab308' : '#ef4444' }}>
                {c.score}
              </span>
            </div>
          ))}
        </div>

        {/* Verdict text */}
        <div className="text-center border-t border-gray-800 pt-2 mb-2">
          <p className="text-xs text-gray-400 italic">
            {guruPercentage <= 15
              ? 'Empreendedor legítimo. Foca em entregar valor real.'
              : guruPercentage <= 30
              ? 'Tem base sólida, mas flerta com táticas de guru às vezes.'
              : guruPercentage <= 50
              ? 'Atenção! Sinais claros de guru em formação detectados.'
              : guruPercentage <= 70
              ? 'Guru certificado. Funil agressivo e promessas exageradas.'
              : 'Guru supremo. Mestre das promessas impossíveis e ostentação.'}
          </p>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center text-[9px] text-gray-600">
          <span>DETECTOR DE GURU v2.0</span>
          <span>#{cardNumber}/9999</span>
        </div>
      </div>
    </div>
  );
});

PokemonCard.displayName = 'PokemonCard';

export default PokemonCard;
