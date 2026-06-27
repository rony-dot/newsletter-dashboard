import { NextRequest, NextResponse } from 'next/server';
import { SocialProfile } from '../../lib/types';
import { scrapeInstagram } from '../../lib/scrapers/instagram';
import { scrapeYouTube } from '../../lib/scrapers/youtube';
import { scrapeTwitter } from '../../lib/scrapers/twitter';
import { scrapeTikTok } from '../../lib/scrapers/tiktok';
import { scrapeLinkedIn } from '../../lib/scrapers/linkedin';
import { analyzeWithClaude } from '../../lib/analyzer';

// Simple in-memory cache
const cache = new Map<string, { data: unknown; timestamp: number }>();
const CACHE_TTL = 10 * 60 * 1000; // 10 minutes

function normalizeHandle(input: string): { handle: string; isUrl: boolean } {
  let handle = input.trim();

  // Remove URL prefixes
  const urlPatterns = [
    /https?:\/\/(www\.)?instagram\.com\//,
    /https?:\/\/(www\.)?youtube\.com\/(c\/|channel\/|@)?/,
    /https?:\/\/(www\.)?(twitter|x)\.com\//,
    /https?:\/\/(www\.)?tiktok\.com\/@?/,
    /https?:\/\/(www\.)?linkedin\.com\/in\//,
  ];

  let isUrl = false;
  for (const pattern of urlPatterns) {
    if (pattern.test(handle)) {
      handle = handle.replace(pattern, '');
      isUrl = true;
      break;
    }
  }

  // Remove trailing slashes and query params
  handle = handle.split('?')[0].split('/')[0];

  // Remove @ prefix
  handle = handle.replace(/^@/, '');

  return { handle, isUrl };
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const rawHandle = body.handle as string;

    if (!rawHandle || rawHandle.trim().length === 0) {
      return NextResponse.json({ error: 'Handle é obrigatório' }, { status: 400 });
    }

    const { handle } = normalizeHandle(rawHandle);

    // Check cache
    const cacheKey = handle.toLowerCase();
    const cached = cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
      return NextResponse.json(cached.data);
    }

    // Scrape all platforms in parallel with 45s total timeout
    const scrapeResults = await Promise.allSettled([
      scrapeInstagram(handle),
      scrapeYouTube(handle),
      scrapeTwitter(handle),
      scrapeTikTok(handle),
      scrapeLinkedIn(handle),
    ]);

    // Collect successful results
    const socials: SocialProfile[] = scrapeResults
      .map((r) => (r.status === 'fulfilled' ? r.value : null))
      .filter((r): r is SocialProfile => r !== null);

    // Analyze with Claude
    const result = await analyzeWithClaude({ handle, socials });

    // Cache result
    cache.set(cacheKey, { data: result, timestamp: Date.now() });

    // Clean old cache entries periodically
    if (cache.size > 100) {
      const now = Date.now();
      Array.from(cache.entries()).forEach(([key, val]) => {
        if (now - val.timestamp > CACHE_TTL) cache.delete(key);
      });
    }

    return NextResponse.json(result);
  } catch (error) {
    console.error('Analyze API error:', error);
    return NextResponse.json(
      { error: 'Erro interno na análise' },
      { status: 500 }
    );
  }
}
