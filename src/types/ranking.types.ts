export interface RankingEntry {
  id: string | number;
  label: string;
  score: number;
  avatar?: string;
}

export interface RankingProps {
  entries: RankingEntry[];
  title?: string;
  scoreLabel?: string;
}
