export interface RankingEntry {
  id: string | number;
  label: string;
  score: number;
  avatar?: string;
}

export type ScoreType = 1 | 2 | 3;

export interface RankingProps {
  entries: RankingEntry[];
  title?: string;
  scoreType?: ScoreType;
  highlightFn?: (entry: RankingEntry, index: number) => boolean;
}

export type RankingItemProps = {
  entry: RankingEntry;
  position: number;
  scoreLabel: string;
  isHighlighted?: boolean;
};