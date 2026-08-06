import { SocialProfile } from '../types';

export async function scrapeInstagram(username: string): Promise<SocialProfile | null> {
  const apiKey = process.env.RAPIDAPI_KEY;
  if (!apiKey) return null;

  try {
    const res = await fetch(
      `https://instagram-scraper-api2.p.rapidapi.com/v1/info?username_or_id_or_url=${encodeURIComponent(username)}`,
      {
        headers: {
          'X-RapidAPI-Key': apiKey,
          'X-RapidAPI-Host': 'instagram-scraper-api2.p.rapidapi.com',
        },
        signal: AbortSignal.timeout(15000),
      }
    );

    if (!res.ok) return null;

    const data = await res.json();
    const info = data.data || data;

    return {
      platform: 'instagram',
      handle: info.username || username,
      followers: info.follower_count || info.edge_followed_by?.count || 0,
      bio: info.biography || info.bio || '',
      profilePic: info.profile_pic_url_hd || info.profile_pic_url || null,
      recentContent: [], // Could parse recent posts if available
    };
  } catch {
    return null;
  }
}
