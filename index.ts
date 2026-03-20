// Components
export { Ranking } from "./src/components/Ranking";
export { RankingItem } from "./src/components/RankingItem";

// Types — re-exported so consumers get full TypeScript support
export type {
  RankingEntry,
  RankingProps,
  RankingItemProps,
  ScoreType,
} from "./src/types/ranking.types";

// Utils — optional, export only if you want consumers to use them
export { getMedal, sortByScore, createSorter } from "./src/utils/ranking.utils";
