import type { RankingProps, ScoreType } from "../types/ranking.types";
import { sortByScore } from "../utils/ranking.utils";
// @ts-ignore: CSS module without type declarations
import styles from "../css/Ranking.module.css";
import { RankingItem } from "./RankingItem";

const SCORE_LABELS: Record<ScoreType, string> = {
  1: "pts",
  2: "xp",
  3: "coins",
};

export function Ranking({
  entries,
  title,
  scoreType = 1,
  highlightFn,
  limit,
}: RankingProps) {
  const sorted = sortByScore(entries);

  const visibleEntries = limit
    ? sorted.slice(0, limit)
    : sorted;

  const scoreLabel = SCORE_LABELS[scoreType];

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>
        {title && <h2 className={styles.title}>{title}</h2>}

        <ol className={styles.list}>
          {visibleEntries.map((entry, index) => {
            const isHighlighted = highlightFn
              ? highlightFn(entry, index)
              : false;

            return (
              <RankingItem
                key={entry.id}
                entry={entry}
                position={index + 1}
                scoreLabel={scoreLabel}
                isHighlighted={isHighlighted}
              />
            );
          })}
        </ol>
      </div>
    </div>
  );
}