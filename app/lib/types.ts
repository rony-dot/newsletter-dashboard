export interface SocialProfile {
  platform: 'instagram' | 'youtube' | 'twitter' | 'tiktok' | 'linkedin';
  handle: string;
  followers?: number;
  bio?: string;
  profilePic?: string;
  recentContent?: string[];
}

export interface CriterionScore {
  id: string;
  label: string;
  score: number;
  justification: string;
}

export interface AnalysisResult {
  name: string;
  bio: string;
  photo: string | null;
  socials: SocialProfile[];
  followersEstimate: number;
  criteria: CriterionScore[];
  redFlags: string[];
  greenFlags: string[];
  guruPercentage: number;
  verdict: Verdict;
}

export interface Verdict {
  title: string;
  emoji: string;
  color: string;
  glowClass: string;
  borderColor: string;
}

export type AppStep = 'start' | 'input' | 'loading' | 'adjust' | 'result';
