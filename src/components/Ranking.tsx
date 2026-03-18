import type { RankingProps } from "../types/ranking.types";
import { sortByScore } from "../utils/ranking.utils";
import styles from "../css/Ranking.module.css";
import { RankingItem } from "./RankingItem";

export function Ranking({ entries, title, scoreLabel = "pts" }: RankingProps) {
  const sorted = sortByScore(entries);

  return (
    <div className={styles.wrapper}>
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
  );
}