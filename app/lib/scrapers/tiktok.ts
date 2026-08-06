import { SocialProfile } from '../types';

export async function scrapeTikTok(username: string): Promise<SocialProfile | null> {
  const apiKey = process.env.RAPIDAPI_KEY;
  if (!apiKey) return null;

  try {
    const res = await fetch(
      `https://tiktok-scraper7.p.rapidapi.com/user/info?unique_id=${encodeURIComponent(username)}`,
      {
        headers: {
          'X-RapidAPI-Key': apiKey,
          'X-RapidAPI-Host': 'tiktok-scraper7.p.rapidapi.com',
        },
        signal: AbortSignal.timeout(15000),
      }
    );

    if (!res.ok) return null;

    const data = await res.json();
    const user = data.data?.user || data.user || data;

    return {
      platform: 'tiktok',
      handle: user.uniqueId || user.unique_id || username,
      followers: user.followerCount || user.fans || 0,
      bio: user.signature || user.bio || '',
      profilePic: user.avatarLarger || user.avatar || null,
      recentContent: [],
    };
  } catch {
    return null;
  }
}
