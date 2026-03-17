import type { RankingProps } from "../types/ranking.types";
import { sortByScore, getMedal } from "../utils/ranking.utils";
import styles from "../css/Ranking.module.css";

export function Ranking({ entries, title, scoreLabel = "pts" }: RankingProps) {
  const sorted = sortByScore(entries);

  return (
    <div className={styles.wrapper}>
      {title && <h2 className={styles.title}>{title}</h2>}

      <ol className={styles.list}>
        {sorted.map((entry, index) => {
          const position = index + 1;
          const medal = getMedal(position);
          const initials = entry.label.slice(0, 2).toUpperCase();

          return (
            <li key={entry.id} className={styles.item}>
              <span className={styles.position}>
                {medal ?? `#${position}`}
              </span>

              <span className={styles.avatar}>
                {entry.avatar ? <img src={entry.avatar} alt={entry.label} /> : initials}
              </span>

              <span className={styles.label}>{entry.label}</span>

              <span className={styles.score}>
                {entry.score.toLocaleString("pt-BR")}
                <span className={styles.scoreUnit}>{scoreLabel}</span>
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
