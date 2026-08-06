import { SocialProfile } from '../types';

export async function scrapeLinkedIn(name: string): Promise<SocialProfile | null> {
  const apiKey = process.env.RAPIDAPI_KEY;
  if (!apiKey) return null;

  try {
    const res = await fetch(
      `https://linkedin-api8.p.rapidapi.com/search-people?keywords=${encodeURIComponent(name)}&start=0`,
      {
        headers: {
          'X-RapidAPI-Key': apiKey,
          'X-RapidAPI-Host': 'linkedin-api8.p.rapidapi.com',
        },
        signal: AbortSignal.timeout(15000),
      }
    );

    if (!res.ok) return null;

    const data = await res.json();
    const person = data.items?.[0] || data[0];
    if (!person) return null;

    return {
      platform: 'linkedin',
      handle: person.publicIdentifier || person.username || name,
      followers: person.followerCount || 0,
      bio: person.headline || person.summary || '',
      profilePic: person.profilePicture || null,
      recentContent: [],
    };
  } catch {
    return null;
  }
}
