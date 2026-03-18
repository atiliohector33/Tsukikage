import type { RankingItemProps } from "../types/ranking.types";
import { getMedal } from "../utils/ranking.utils";
import styles from "../css/Ranking.module.css";

export function RankingItem({ entry, position, scoreLabel }: RankingItemProps) {
  const medal = getMedal(position);
  const initials = entry.label.slice(0, 2).toUpperCase();

  return (
    <li className={styles.item}>
      <span className={styles.position}>
        {medal ?? `#${position}`}
      </span>

      <span className={styles.avatar}>
        {entry.avatar ? (
          <img src={entry.avatar} alt={entry.label} />
        ) : (
          initials
        )}
      </span>

      <span className={styles.label}>{entry.label}</span>

      <span className={styles.score}>
        {entry.score.toLocaleString("en-US")}
        <span className={styles.scoreUnit}>{scoreLabel}</span>
      </span>
    </li>
  );
}