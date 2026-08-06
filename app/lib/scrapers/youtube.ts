import { SocialProfile } from '../types';

export async function scrapeYouTube(query: string): Promise<SocialProfile | null> {
  const apiKey = process.env.YOUTUBE_API_KEY;
  if (!apiKey) return null;

  try {
    // Search for channel
    const searchRes = await fetch(
      `https://www.googleapis.com/youtube/v3/search?q=${encodeURIComponent(query)}&type=channel&maxResults=1&key=${apiKey}`,
      { signal: AbortSignal.timeout(10000) }
    );

    if (!searchRes.ok) return null;

    const searchData = await searchRes.json();
    const channel = searchData.items?.[0];
    if (!channel) return null;

    const channelId = channel.id?.channelId || channel.snippet?.channelId;

    // Get channel details
    const detailRes = await fetch(
      `https://www.googleapis.com/youtube/v3/channels?id=${channelId}&part=snippet,statistics&key=${apiKey}`,
      { signal: AbortSignal.timeout(10000) }
    );

    if (!detailRes.ok) return null;

    const detailData = await detailRes.json();
    const details = detailData.items?.[0];

    // Get recent videos
    const videosRes = await fetch(
      `https://www.googleapis.com/youtube/v3/search?channelId=${channelId}&order=date&maxResults=20&type=video&key=${apiKey}`,
      { signal: AbortSignal.timeout(10000) }
    );

    let videoTitles: string[] = [];
    if (videosRes.ok) {
      const videosData = await videosRes.json();
      videoTitles = (videosData.items || []).map((v: { snippet?: { title?: string } }) => v.snippet?.title || '').filter(Boolean);
    }

    return {
      platform: 'youtube',
      handle: details?.snippet?.customUrl || details?.snippet?.title || query,
      followers: parseInt(details?.statistics?.subscriberCount || '0', 10),
      bio: details?.snippet?.description || '',
      profilePic: details?.snippet?.thumbnails?.high?.url || null,
      recentContent: videoTitles,
    };
  } catch {
    return null;
  }
}
