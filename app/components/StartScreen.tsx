'use client';

interface StartScreenProps {
  onStart: () => void;
}

export default function StartScreen({ onStart }: StartScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 text-center">
      <div className="fade-in">
        <div className="text-6xl mb-6">🔍</div>
        <h1 className="text-3xl sm:text-4xl font-bold text-green-500 mb-2 tracking-wider">
          DETECTOR DE GURU
        </h1>
        <h2 className="text-lg sm:text-xl text-green-400/70 mb-8 tracking-wide">
          DE INTERNET
        </h2>
        <div className="text-sm text-gray-500 mb-8 max-w-md mx-auto space-y-2">
          <p className="cursor-blink">
            {`>`} Sistema de análise avançada de perfis públicos
          </p>
          <p className="text-gray-600">
            Descubra o quão guru é qualquer pessoa da internet
          </p>
        </div>
        <div className="border border-green-500/30 rounded p-4 mb-8 max-w-sm mx-auto">
          <div className="text-xs text-green-500/60 mb-2">{`// FUNCIONALIDADES`}</div>
          <ul className="text-xs text-gray-400 space-y-1 text-left">
            <li>→ Análise de redes sociais</li>
            <li>→ Detecção de gatilhos mentais</li>
            <li>→ Medidor de ostentação</li>
            <li>→ Card de Pokémon compartilhável</li>
          </ul>
        </div>
        <button
          onClick={onStart}
          className="bg-green-500 hover:bg-green-400 text-black font-bold py-3 px-8 rounded transition-all duration-200 hover:shadow-[0_0_20px_rgba(34,197,94,0.4)] tracking-wider text-sm uppercase"
        >
          [ INICIAR INVESTIGAÇÃO ]
        </button>
        <p className="text-xs text-gray-600 mt-6">
          v2.0.1 — Classificado: USO RECREATIVO
        </p>
      </div>
    </div>
  );
}
