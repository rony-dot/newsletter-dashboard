import { Verdict } from './types';

export const CRITERIA = [
  { id: 'empresa', label: 'Empresa Real', lowLabel: 'Empresa consolidada', highLabel: 'Nunca teve empresa' },
  { id: 'receita', label: 'Origem da Receita', lowLabel: 'Negócio/produto real', highLabel: '100% curso sobre curso' },
  { id: 'ostentacao', label: 'Ostentação', lowLabel: 'Zero, foca no conteúdo', highLabel: 'Lambo + Dubai + Rolex' },
  { id: 'promessas', label: 'Promessas', lowLabel: 'Compartilha aprendizados', highLabel: '"De 0 a 100k/mês"' },
  { id: 'prova_social', label: 'Prova Social', lowLabel: 'Cases reais com contexto', highLabel: 'Prints de faturamento' },
  { id: 'linguagem', label: 'Linguagem', lowLabel: 'Técnica e profunda', highLabel: 'Gatilhos mentais non-stop' },
  { id: 'vulnerabilidade', label: 'Vulnerabilidade', lowLabel: 'Admite erros', highLabel: 'Fracasso vira pitch' },
  { id: 'modelo', label: 'Modelo de Negócio', lowLabel: 'Conteúdo gratuito', highLabel: 'Escada infinita high ticket' },
] as const;

export function getVerdict(percentage: number): Verdict {
  if (percentage <= 15) {
    return { title: 'Empreendedor Raiz', emoji: '🌳', color: '#22c55e', glowClass: 'glow-green', borderColor: 'border-green-500' };
  }
  if (percentage <= 30) {
    return { title: 'Empreendedor Híbrido', emoji: '⚡', color: '#eab308', glowClass: 'glow-yellow', borderColor: 'border-yellow-500' };
  }
  if (percentage <= 50) {
    return { title: 'Guru em Formação', emoji: '🔮', color: '#f97316', glowClass: 'glow-orange', borderColor: 'border-orange-500' };
  }
  if (percentage <= 70) {
    return { title: 'Guru Certificado', emoji: '🐍', color: '#ef4444', glowClass: 'glow-red', borderColor: 'border-red-500' };
  }
  return { title: 'Guru Supremo', emoji: '💀', color: '#b91c1c', glowClass: 'glow-darkred', borderColor: 'border-red-800' };
}

export function calculateGuruPercentage(scores: { score: number }[]): number {
  if (scores.length === 0) return 0;
  const avg = scores.reduce((sum, s) => sum + s.score, 0) / scores.length;
  return Math.round(avg * 10);
}

export function getBarColor(score: number): string {
  if (score <= 3) return 'bg-green-500';
  if (score <= 6) return 'bg-yellow-500';
  return 'bg-red-500';
}

export function formatFollowers(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return n.toString();
}

export const LOADING_PHASES = [
  'Vasculhando redes sociais...',
  'Analisando conteúdo publicado...',
  'Verificando empresa no CNPJ...',
  'Calculando nível de ostentação...',
  'Detectando gatilhos mentais...',
  'Medindo promessas impossíveis...',
  'Consultando base de dados de gurus...',
  'Compilando dossiê final...',
];

export const PLATFORM_ICONS: Record<string, string> = {
  instagram: '📸',
  youtube: '📺',
  twitter: '🐦',
  tiktok: '🎵',
  linkedin: '💼',
};

export const PLATFORM_COLORS: Record<string, string> = {
  instagram: 'bg-pink-600',
  youtube: 'bg-red-600',
  twitter: 'bg-blue-500',
  tiktok: 'bg-purple-600',
  linkedin: 'bg-blue-700',
};
