import type { RankingEntry } from "./ranking.types";

export const sortByScore = (entries: RankingEntry[]) =>
  [...entries].sort((a, b) => b.score - a.score);

export const getMedal = (position: number) =>
  ({ 1: "🥇", 2: "🥈", 3: "🥉" }[position] ?? null);
