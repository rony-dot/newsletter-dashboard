import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Detector de Guru de Internet",
  description: "Descubra o quão guru é qualquer perfil da internet. Análise completa com card de Pokémon compartilhável.",
  openGraph: {
    title: "Detector de Guru de Internet",
    description: "Descubra o quão guru é qualquer perfil da internet.",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Detector de Guru de Internet",
    description: "Descubra o quão guru é qualquer perfil da internet.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR">
      <body className="antialiased min-h-screen bg-[#0a0a0a] text-[#ededed]">
        <div className="scan-lines" />
        {children}
        <footer className="text-center text-xs text-gray-600 py-4 px-4">
          Essa é uma brincadeira. Nenhum guru foi ferido durante essa análise.
        </footer>
      </body>
    </html>
  );
}
