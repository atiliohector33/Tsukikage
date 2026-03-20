// Components
export { Ranking } from "./components/Ranking";
export { RankingItem } from "./components/RankingItem";

// Types — re-exported so consumers get full TypeScript support
export type {
  RankingEntry,
  RankingProps,
  RankingItemProps,
  ScoreType,
} from "./types/ranking.types";

// Utils — optional, export only if you want consumers to use them
export { getMedal, sortByScore, createSorter } from "./utils/ranking.utils";
