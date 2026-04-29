'use client';

import { useState, useRef } from 'react';

interface InputScreenProps {
  onSubmit: (handle: string, photo: string | null) => void;
  onBack: () => void;
}

export default function InputScreen({ onSubmit, onBack }: InputScreenProps) {
  const [handle, setHandle] = useState('');
  const [photo, setPhoto] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handlePhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => setPhoto(ev.target?.result as string);
    reader.readAsDataURL(file);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (handle.trim()) {
      onSubmit(handle.trim(), photo);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4">
      <div className="fade-in w-full max-w-md">
        <button onClick={onBack} className="text-gray-500 hover:text-gray-300 text-sm mb-6">
          ← Voltar
        </button>

        <div className="text-4xl mb-4 text-center">🕵️</div>
        <h2 className="text-xl font-bold text-green-500 mb-2 text-center tracking-wider">
          IDENTIFICAR SUSPEITO
        </h2>
        <p className="text-sm text-gray-500 mb-8 text-center">
          Digite o @ ou nome completo do alvo
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="text-xs text-green-500/60 block mb-2">{`// HANDLE OU NOME`}</label>
            <input
              type="text"
              value={handle}
              onChange={(e) => setHandle(e.target.value)}
              placeholder="@exemplo ou Nome Completo"
              className="w-full bg-black border border-green-500/30 rounded px-4 py-3 text-green-400 placeholder-gray-600 focus:border-green-500 focus:outline-none focus:shadow-[0_0_10px_rgba(34,197,94,0.2)] transition-all"
              autoFocus
            />
          </div>

          <div>
            <label className="text-xs text-green-500/60 block mb-2">{`// FOTO DO SUSPEITO (OPCIONAL)`}</label>
            <input
              type="file"
              accept="image/*"
              ref={fileInputRef}
              onChange={handlePhotoUpload}
              className="hidden"
            />
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="border border-dashed border-gray-600 hover:border-green-500/50 rounded px-4 py-3 text-sm text-gray-500 hover:text-gray-300 transition-all flex-1"
              >
                {photo ? '✅ Foto carregada' : '📷 Fazer upload de foto'}
              </button>
              {photo && (
                <button
                  type="button"
                  onClick={() => setPhoto(null)}
                  className="text-red-500 text-xs hover:text-red-400"
                >
                  Remover
                </button>
              )}
            </div>
            {photo && (
              <div className="mt-3 flex justify-center">
                <img src={photo} alt="Preview" className="w-20 h-20 rounded-full object-cover border-2 border-green-500/30" />
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={!handle.trim()}
            className="w-full bg-red-600 hover:bg-red-500 disabled:bg-gray-700 disabled:text-gray-500 text-white font-bold py-3 rounded transition-all duration-200 hover:shadow-[0_0_20px_rgba(239,68,68,0.4)] tracking-wider text-sm uppercase"
          >
            [ INICIAR ANÁLISE ]
          </button>
        </form>

        <div className="mt-6 border border-gray-800 rounded p-3">
          <p className="text-xs text-gray-600 text-center">
            💡 Funciona com Instagram, YouTube, Twitter/X, TikTok e LinkedIn
          </p>
        </div>
      </div>
    </div>
  );
}
