import type { RankingProps, ScoreType } from "../types/ranking.types";
import { sortByScore } from "../utils/ranking.utils";
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
}: RankingProps) {
  const sorted = sortByScore(entries);
  const scoreLabel = SCORE_LABELS[scoreType];

  return (
    <div className={styles.wrapper}>
      <div className={styles.container}>
        {title && <h2 className={styles.title}>{title}</h2>}

        <ol className={styles.list}>
          {sorted.map((entry, index) => (
            <RankingItem
              key={entry.id}
              entry={entry}
              position={index + 1}
              scoreLabel={scoreLabel}
            />
          ))}
        </ol>
      </div>
    </div>
  );
}