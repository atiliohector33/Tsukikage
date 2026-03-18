import type { RankingEntry } from "../types/ranking.types";

const MEDALS: Record<number, string> = {
  1: "🥇",
  2: "🥈",
  3: "🥉",
};

export const getMedal = (position: number): string | null => {
  return MEDALS[position] ?? null;
};

type SortOptions = {
  secondaryKey?: keyof RankingEntry;
};

export const sortByScore = (
  entries: RankingEntry[],
  options?: SortOptions
): RankingEntry[] => {
  const { secondaryKey } = options || {};

  return [...entries].sort((a, b) => {
    const scoreDiff = b.score - a.score;

    if (scoreDiff !== 0) return scoreDiff;

    if (secondaryKey) {
      const aValue = a[secondaryKey];
      const bValue = b[secondaryKey];

      if (aValue != null && bValue != null) {
        return String(aValue).localeCompare(String(bValue));
      }
    }

    return 0;
  });
};

export const createSorter =
  <T>(compareFn: (a: T, b: T) => number) =>
  (list: T[]): T[] =>
    [...list].sort(compareFn);