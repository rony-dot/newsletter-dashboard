import Anthropic from '@anthropic-ai/sdk';
import { SocialProfile, CriterionScore, AnalysisResult } from './types';
import { CRITERIA, getVerdict, calculateGuruPercentage } from './constants';

interface DossierData {
  handle: string;
  socials: SocialProfile[];
}

const SYSTEM_PROMPT = `Você é um analista especializado em identificar "gurus de internet".
Recebeu um dossiê com dados reais de redes sociais de uma pessoa.
Analise os dados e avalie em 8 critérios (0=empreendedor legítimo, 10=guru total):

1. empresa: Tem empresa real com funcionários? Verifique no LinkedIn e bio
2. receita: Receita vem de negócio real ou infoproduto? Analise os produtos mencionados
3. ostentacao: Nível de ostentação. Analise fotos, locais, menções a luxo nos posts
4. promessas: Tipo de promessa nos títulos de vídeos e posts
5. prova_social: Tipo de prova social usada (cases reais vs prints genéricos)
6. linguagem: Frequência de gatilhos mentais nos títulos e legendas
7. vulnerabilidade: Presença de posts admitindo erros/fracassos vs só sucesso
8. modelo: Modelo de negócio (conteúdo gratuito vs funil agressivo vs escada infinita)

Analise os títulos dos vídeos, legendas dos posts, bio, e tipo de conteúdo.
Procure por padrões como:
- Títulos com números exagerados ("6 em 7", "100k em 30 dias")
- Gatilhos de escassez ("últimas vagas", "só hoje")
- Ostentação visual (carros, viagens, lifestyle)
- Funil de vendas agressivo (isca → webinar → high ticket → mastermind)
- Falta de empresa real no histórico

Retorne APENAS JSON válido (sem markdown, sem code blocks) no seguinte formato:
{
  "name": "Nome da pessoa",
  "bio": "Bio resumida em 1 frase",
  "criteria": [
    {"id": "empresa", "label": "Empresa Real", "score": 5, "justification": "..."},
    {"id": "receita", "label": "Origem da Receita", "score": 5, "justification": "..."},
    {"id": "ostentacao", "label": "Ostentação", "score": 5, "justification": "..."},
    {"id": "promessas", "label": "Promessas", "score": 5, "justification": "..."},
    {"id": "prova_social", "label": "Prova Social", "score": 5, "justification": "..."},
    {"id": "linguagem", "label": "Linguagem", "score": 5, "justification": "..."},
    {"id": "vulnerabilidade", "label": "Vulnerabilidade", "score": 5, "justification": "..."},
    {"id": "modelo", "label": "Modelo de Negócio", "score": 5, "justification": "..."}
  ],
  "redFlags": ["flag1", "flag2"],
  "greenFlags": ["flag1", "flag2"]
}`;

function compileDossier(data: DossierData): string {
  let dossier = `# Dossiê: ${data.handle}\n\n`;

  for (const social of data.socials) {
    dossier += `## ${social.platform.toUpperCase()} (@${social.handle})\n`;
    if (social.followers) dossier += `- Seguidores: ${social.followers}\n`;
    if (social.bio) dossier += `- Bio: ${social.bio}\n`;
    if (social.recentContent && social.recentContent.length > 0) {
      dossier += `- Conteúdo recente:\n`;
      social.recentContent.forEach((c) => {
        dossier += `  - "${c}"\n`;
      });
    }
    dossier += '\n';
  }

  if (data.socials.length === 0) {
    dossier += 'Nenhum dado de redes sociais disponível. Analise com base no handle/nome fornecido.\n';
    dossier += 'Use seu conhecimento geral sobre essa pessoa (se conhecida) para fazer a análise.\n';
  }

  return dossier;
}

export async function analyzeWithClaude(data: DossierData): Promise<AnalysisResult> {
  const apiKey = process.env.ANTHROPIC_API_KEY;

  if (!apiKey) {
    // Return mock data when no API key
    return generateMockResult(data);
  }

  const client = new Anthropic({ apiKey });
  const dossier = compileDossier(data);

  try {
    const message = await client.messages.create({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 2000,
      system: SYSTEM_PROMPT,
      messages: [
        {
          role: 'user',
          content: `Analise o seguinte dossiê e retorne o JSON de avaliação:\n\n${dossier}`,
        },
      ],
    });

    const textContent = message.content.find((c) => c.type === 'text');
    const text = textContent?.text || '';

    // Parse JSON from response, handling potential markdown wrapping
    let jsonStr = text;
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      jsonStr = jsonMatch[0];
    }

    const parsed = JSON.parse(jsonStr);

    const criteria: CriterionScore[] = CRITERIA.map((c) => {
      const found = parsed.criteria?.find((pc: { id: string }) => pc.id === c.id);
      return {
        id: c.id,
        label: c.label,
        score: found?.score ?? 5,
        justification: found?.justification ?? 'Sem dados suficientes para avaliação.',
      };
    });

    const guruPercentage = calculateGuruPercentage(criteria);

    // Find best photo from socials
    const photo = data.socials.find((s) => s.profilePic)?.profilePic || null;

    // Estimate total followers
    const followersEstimate = data.socials.reduce((sum, s) => sum + (s.followers || 0), 0);

    return {
      name: parsed.name || data.handle,
      bio: parsed.bio || data.socials.find((s) => s.bio)?.bio || 'Perfil analisado',
      photo,
      socials: data.socials,
      followersEstimate,
      criteria,
      redFlags: parsed.redFlags || [],
      greenFlags: parsed.greenFlags || [],
      guruPercentage,
      verdict: getVerdict(guruPercentage),
    };
  } catch (error) {
    console.error('Claude analysis error:', error);
    return generateMockResult(data);
  }
}

function generateMockResult(data: DossierData): AnalysisResult {
  const criteria: CriterionScore[] = CRITERIA.map((c) => ({
    id: c.id,
    label: c.label,
    score: Math.floor(Math.random() * 8) + 1,
    justification: `Análise baseada em padrões detectados para o critério "${c.label}". Configure ANTHROPIC_API_KEY para análise real com IA.`,
  }));

  const guruPercentage = calculateGuruPercentage(criteria);
  const photo = data.socials.find((s) => s.profilePic)?.profilePic || null;
  const followersEstimate = data.socials.reduce((sum, s) => sum + (s.followers || 0), 0);

  return {
    name: data.handle.replace('@', ''),
    bio: data.socials.find((s) => s.bio)?.bio || 'Perfil em análise — dados simulados',
    photo,
    socials: data.socials,
    followersEstimate: followersEstimate || Math.floor(Math.random() * 500000),
    criteria,
    redFlags: [
      'Análise simulada — configure API keys para dados reais',
      'Possíveis gatilhos mentais detectados',
    ],
    greenFlags: [
      'Modo demo ativo',
    ],
    guruPercentage,
    verdict: getVerdict(guruPercentage),
  };
}
