# 🏆 tsukikage

> **月影** — *moonlight* in Japanese. A sleek, fully customizable React ranking component library.

[![npm version](https://img.shields.io/badge/version-0.0.0-violet?style=flat-square)](https://www.npmjs.com/)
[![license](https://img.shields.io/badge/license-MIT-blueviolet?style=flat-square)](./LICENSE)
[![react](https://img.shields.io/badge/react-19%2B-61DAFB?style=flat-square&logo=react)](https://react.dev/)
[![typescript](https://img.shields.io/badge/TypeScript-ready-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org/)

---

## ✨ What is tsukikage?

**tsukikage** is a React component library for building beautiful, flexible ranking lists. Drop it into your project, pass your data, and get a fully styled, animated leaderboard — with total control over how it looks and behaves.

Whether you're building a game leaderboard, a points-based system, a productivity tracker, or any competitive UI, tsukikage gives you the tools to make it shine. 🌙

---

## 🚀 Getting Started

> 🚧 **This library is currently in active development.** The API may change before the first stable release.

### Installation *(coming soon)*

```bash
npm install tsukikage
```

### Usage

```tsx
import { Ranking } from 'tsukikage'

const entries = [
  { id: 1, label: "Hector",      score: 9840 },
  { id: 2, label: "Alex Poatan", score: 7200 },
  { id: 3, label: "Jon Jones",   score: 6800 },
]

function App() {
  return (
    <Ranking
      entries={entries}
      title="Leaderboard"
      scoreType={1}
      highlightFn={(entry) => entry.score > 9000}
    />
  )
}
```

---

## 🧩 Components

### `<Ranking />`

The main component. Accepts a list of entries and renders a sorted, styled ranking list.

| Prop          | Type                                          | Default | Description                                                     |
|---------------|-----------------------------------------------|---------|-----------------------------------------------------------------|
| `entries`     | `RankingEntry[]`                              | —       | **Required.** Array of items to rank.                           |
| `title`       | `string`                                      | —       | Optional heading displayed above the list.                      |
| `scoreType`   | `1 \| 2 \| 3`                                | `1`     | Controls the score unit label: `pts`, `xp`, or `coins`.        |
| `highlightFn` | `(entry, index) => boolean`                   | —       | Function that determines which entries get a highlight effect.  |

### `RankingEntry` type

```ts
interface RankingEntry {
  id: string | number   // Unique identifier
  label: string         // Display name
  score: number         // Numeric score (used for sorting)
  avatar?: string       // Optional image URL
}
```

---

## 🎨 Visual Features

- 🥇🥈🥉 **Medal badges** for the top 3 positions
- ✨ **Highlight animations** — shine effect, scale, and glow for featured entries
- 🖼️ **Avatar support** — image or auto-generated initials fallback
- 🏷️ **Score labels** — pts / xp / coins (more coming soon)
- 📐 **Smooth hover interactions** — lift, scale, shadow transitions
- 🎞️ **CSS-only animations** — no JavaScript animation dependencies

---

## 🛣️ Roadmap

Here's what's planned for tsukikage:

- [ ] 🎭 Multiple visual themes (dark, neon, minimal, glass, etc.)
- [ ] 🔦 More highlight types (pulse, border glow, badge, crown)
- [ ] 🔢 Custom score formatters
- [ ] 🏷️ Custom score unit labels (beyond `pts`, `xp`, `coins`)
- [ ] 🔄 Animated re-ranking (score changes with smooth transitions)
- [ ] 📱 Mobile-first responsive variants
- [ ] ♿ Full accessibility (ARIA roles, keyboard navigation)
- [ ] 🌐 npm package release
- [ ] 📖 Storybook documentation site

---

## 🗂️ Project Structure

```
src/
├── components/
│   ├── Ranking.tsx        # Main ranking component
│   └── RankingItem.tsx    # Individual row component
├── css/
│   └── Ranking.module.css # Scoped styles with animations
├── types/
│   └── ranking.types.ts   # TypeScript interfaces & types
├── utils/
│   └── ranking.utils.ts   # Sorting helpers & medal logic
└── main.tsx               # App entry point
```

---

## 🛠️ Development

This project uses **Vite** + **React 19** + **TypeScript**.

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build
npm run build

# Lint
npm run lint
```

---

## 🤝 Contributing

Contributions, ideas, and feedback are very welcome! This is an early-stage project and the API is still being shaped. Feel free to open an issue or submit a PR.

---

## 📄 License

MIT © tsukikage contributors

---

<p align="center">
  Made with 🌙 and <strong>React</strong>
</p>
