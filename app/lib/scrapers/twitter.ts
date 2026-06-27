import { SocialProfile } from '../types';

export async function scrapeTwitter(username: string): Promise<SocialProfile | null> {
  const apiKey = process.env.RAPIDAPI_KEY;
  if (!apiKey) return null;

  try {
    const res = await fetch(
      `https://twitter-api45.p.rapidapi.com/screenname.php?screenname=${encodeURIComponent(username)}`,
      {
        headers: {
          'X-RapidAPI-Key': apiKey,
          'X-RapidAPI-Host': 'twitter-api45.p.rapidapi.com',
        },
        signal: AbortSignal.timeout(15000),
      }
    );

    if (!res.ok) return null;

    const data = await res.json();

    return {
      platform: 'twitter',
      handle: data.screen_name || data.username || username,
      followers: data.followers_count || data.sub_count || 0,
      bio: data.description || data.desc || '',
      profilePic: data.profile_image_url_https || data.avatar || null,
      recentContent: [],
    };
  } catch {
    return null;
  }
}
