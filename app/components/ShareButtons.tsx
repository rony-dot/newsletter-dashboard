'use client';

interface ShareButtonsProps {
  onCapture: () => Promise<Blob | null>;
  name: string;
  percentage: number;
}

export default function ShareButtons({ onCapture, name, percentage }: ShareButtonsProps) {
  const shareText = `🔍 ${name} tem ${percentage}% de chance de ser Guru de Internet! Descubra o seu: `;
  const shareUrl = typeof window !== 'undefined' ? window.location.origin : '';

  const handleShare = async () => {
    const blob = await onCapture();
    if (!blob) return;

    if (navigator.share) {
      try {
        const file = new File([blob], 'guru-card.png', { type: 'image/png' });
        await navigator.share({
          title: 'Detector de Guru de Internet',
          text: shareText,
          files: [file],
        });
        return;
      } catch {
        // User cancelled or API not supported for files
      }
    }

    // Fallback: download
    downloadImage(blob);
  };

  const downloadImage = (blob: Blob) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `guru-card-${name.toLowerCase().replace(/\s+/g, '-')}.png`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDownload = async () => {
    const blob = await onCapture();
    if (blob) downloadImage(blob);
  };

  const encodedText = encodeURIComponent(shareText + shareUrl);

  return (
    <div className="space-y-3 w-full max-w-[380px]">
      {/* Main share button */}
      <button
        onClick={handleShare}
        className="w-full bg-green-500 hover:bg-green-400 text-black font-bold py-3 rounded transition-all duration-200 hover:shadow-[0_0_20px_rgba(34,197,94,0.4)] tracking-wider text-sm uppercase"
      >
        📤 COMPARTILHAR CARD
      </button>

      {/* Platform buttons */}
      <div className="grid grid-cols-2 gap-2">
        <a
          href={`https://wa.me/?text=${encodedText}`}
          target="_blank"
          rel="noopener noreferrer"
          className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 rounded text-xs text-center transition-all"
        >
          💬 WhatsApp
        </a>
        <a
          href={`https://x.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 rounded text-xs text-center transition-all"
        >
          🐦 X / Twitter
        </a>
        <a
          href={`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="bg-blue-700 hover:bg-blue-800 text-white font-bold py-2 rounded text-xs text-center transition-all"
        >
          💼 LinkedIn
        </a>
        <button
          onClick={handleDownload}
          className="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 rounded text-xs text-center transition-all"
        >
          📸 Salvar p/ Stories
        </button>
      </div>

      {/* Download button */}
      <button
        onClick={handleDownload}
        className="w-full border border-gray-700 hover:border-gray-500 text-gray-400 hover:text-white py-2 rounded text-xs transition-all"
      >
        ⬇️ Baixar imagem PNG
      </button>
    </div>
  );
}
