# Uber UI Reference DESIGN.md

> Auto-generated design system — reverse-engineered via static analysis by skillui.
> Frameworks: None detected
> Colors: 20 · Fonts: 2 · Components: 8
> Icon library: not detected · State: not detected
> Primary theme: light · Dark mode toggle: no · Motion: subtle

## Visual Reference

**Match this design exactly** — study colors, fonts, spacing, and component shapes before writing any UI code.

![Uber UI Reference Homepage](../screenshots/homepage.png)

---

## 1. Visual Theme & Atmosphere

This is a **light-themed** interface with a neutral, approachable feel. The light background emphasizes content clarity. Typography pairs **UberMoveText** for display/headings with **UberMove** for body text, creating clear visual hierarchy through type contrast. Spacing follows a **4px base grid** (compact density), with scale: 2, 4, 6, 8, 10, 12, 14, 16px. Motion is subtle — smooth transitions (150-300ms) ease state changes without drawing attention.

---

## 2. Color Palette & Roles

| Token | Hex | Role | Use |
|---|---|---|---|
| base-background-material-primary | `#ffffff` | background | Page background, darkest surface |
| surface | `#f6f6f6` | surface | Card and panel backgrounds |
| base-background-statelayer-hover | `#111111` | text-primary | Headings and body text |
| base-border-inverse-subtle | `#525252` | text-muted | Captions, placeholders, secondary info |
| border | `#333333` | border | Dividers, card borders, outlines |
| base-error-background-disabled | `#fee6e1` | danger | Error states, destructive actions |
| info | `#0000ee` | info | Informational highlights |
| base-background-overlay-art | `#000000` | unknown | Palette color |
| base-border-subtle | `#c4c4c4` | unknown | Palette color |
| base-background-disabled | `#e0e0e0` | unknown | Palette color |
| base-info-border-subtle | `#777777` | unknown | Palette color |
| base-background-track | `#6b6b6b` | unknown | Palette color |
| base-border-inverse-subtle | `#b7b7b7` | unknown | Palette color |
| base-background-track | `#5f5f5f` | unknown | Palette color |
| base-background-inverse-statelayer-hover | `#ececec` | unknown | Palette color |
| unknown | `#068bee` | unknown | Palette color |
| base-background-disabled | `#474747` | unknown | Palette color |
| base-background-material-primary | `#272727` | unknown | Palette color |
| unknown | `#276ef1` | unknown | Palette color |
| base-error-background-statelayer-hover | `#31110b` | unknown | Palette color |

### CSS Variable Tokens

```css
--base-red-background-material-bold-stop-0: #f43b00;
--base-red-background-material-bold-stop-100: #e42500;
--base-orange-background-material-bold-stop-0: #fc993c;
--base-orange-background-material-bold-stop-100: #fb762e;
--base-yellow-background-material-bold-stop-0: #f7e431;
--base-yellow-background-material-bold-stop-100: #f1d223;
--base-green-background-material-bold-stop-0: #0ca555;
--base-green-background-material-bold-stop-100: #098042;
--base-blue-background-material-bold-stop-0: #1697e7;
--base-blue-background-material-bold-stop-100: #1175dd;
--base-crimson-background-material-bold-stop-0: #e0336c;
--base-crimson-background-material-bold-stop-100: #d32753;
--base-background-base: var(--base-neutral-99);
--base-background-primary: var(--base-neutral-100);
--base-background-secondary: var(--base-neutral-98);
--base-background-tertiary: var(--base-neutral-96);
--base-background-disabled: rgba(224,224,224,0.6);
--base-background-always-dark: var(--base-neutral-0);
--base-background-always-light: var(--base-neutral-100);
--base-background-track: rgba(107,107,107,0.06);
```


---

## 3. Typography Rules

**Font Stack:**
- **UberMove** — Heading 1, Heading 2, Heading 3
- **UberMoveText** — Body, Caption

**Font Sources:**

```css
@font-face {
  font-family: "Book";
  src: url("https://www.uber.com/_static/c7d2487e86a01259.woff2") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "Medium";
  src: url("https://www.uber.com/_static/373acd359b809a36.woff2") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "NarrowBook";
  src: url("https://www.uber.com/_static/4092f014767a0c42.woff2") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "NarrowMedium";
  src: url("https://www.uber.com/_static/d03e099b908c23f5.woff2") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "NarrowNews";
  src: url("https://www.uber.com/_static/3ead8fe086dcc03b.woff2") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "NarrowThin";
  src: url("https://www.uber.com/_static/22ff2ed7e89a1893.woff2") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "News";
  src: url("https://www.uber.com/_static/eaaab0415f3c894a.woff2") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "Thin";
  src: url("https://www.uber.com/_static/4971a684a2006b0b.woff2") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "UberMove";
  src: url("https://tb-static.uber.com/prod/uber-static/UberMove-Regular.woff2") format("woff2");
  font-weight: 400;
}
@font-face {
  font-family: "UberMoveText";
  src: url("https://tb-static.uber.com/prod/uber-static/UberMoveText-Regular.woff2") format("woff2");
  font-weight: 400;
}
```

| Role | Font | Size | Weight |
|---|---|---|---|
| Heading 1 | UberMove | 88px | 700 |
| Heading 2 | UberMove | 58px | 700 |
| Heading 3 | UberMove | 52px | 700 |
| Body | UberMoveText | 16px | 400 |
| Caption | UberMoveText | 14px | 400 |

**Typographic Rules:**
- Limit to 2 font families max per screen
- Use **UberMove** for body/UI text, **UberMoveText** for display/headings
- Maintain consistent hierarchy: no more than 3-4 font sizes per screen
- Headings use bold (600-700), body uses regular (400)
- Line height: 1.5 for body text, 1.2 for headings
- Use color and opacity for secondary hierarchy, not additional font sizes


---

## 4. Component Stylings

### Layout (1)

**Footer** — `html`

### Navigation (1)

**Navigation** — `html`

### Data Display (1)

**Badge** — `html`

### Data Input (1)

**Button** — `html`
- Animation: 

### Overlay (1)

**Modal** — `html`

### Media (3)

**Image** — `html`

**Icon** — `html`

**Map/Canvas** — `html`



---

## 5. Layout Principles

- **Base spacing unit:** 4px
- **Spacing scale:** 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24
- **Border radius:** 0px 0px 8px 8px, 4px, 6px, 8px, 8px 8px 0px 0px, 12px, 16px, 100%, 999px, 1000px
- **Max content width:** 1136px

**Spacing as Meaning:**
| Spacing | Use |
|---|---|
| 4-8px | Tight: related items within a group |
| 12-16px | Medium: between groups |
| 24-32px | Wide: between sections |
| 48px+ | Vast: major section breaks |


---

## 6. Depth & Elevation

### Flat — subtle depth hints

- `inset 0 0 0 1px var(--action-button-border)`
- `inset 0 0 0 2px #FCFCFC,0 0 0 2px #276EF1`

### Floating — dropdowns, popovers, modals

- `0 4px 16px hsla(0,0%,0%,0.16)`
- `0px 4px 16px rgba(0,0,0,0.12)`
- `rgba(0,0,0,0.08) 0px -8px 20px 0px`

### Overlay — full-screen overlays, top-level dialogs

- `inset 999px 999px 0px rgba(236,236,236,0.15)`
- `inset 999px 999px 0px rgba(236,236,236,0.2)`
- `inset 999px 999px 0px rgba(17,17,17,0.06)`

### Z-Index Scale

`0, 1, 2, 1000, 2001, 2002, 3000, 2147483647`



---

## 7. Animation & Motion

This project uses **subtle motion**. Transitions smooth state changes without demanding attention.

### CSS Animations

- `@keyframes action-button-module__action-button-spin___GydB6`
- `@keyframes animation-dkKkL`

### Animated Components

- **Button**: 

### Motion Guidelines

- Duration: 150-300ms for micro-interactions, 300-500ms for page transitions
- Easing: `ease-out` for enters, `ease-in` for exits
- Always respect `prefers-reduced-motion`


---

## 8. Do's and Don'ts

### Do's

- Use `#ffffff` as the primary page background
- Pair **UberMove** (body) with **UberMoveText** (display) — these are the only allowed fonts
- Follow the **4px** spacing grid for all margins, padding, and gaps
- Use the defined shadow tokens for elevation — see Section 6
- Use border-radius from the scale: 0px 0px 8px 8px, 4px, 6px, 8px, 8px 8px 0px 0px
- Reuse existing components from Section 4 before creating new ones

### Don'ts

- Don't introduce colors outside this palette — extend the design tokens first
- Don't introduce additional font families beyond UberMove and UberMoveText
- Don't use arbitrary spacing values — stick to multiples of 4px
- Don't create custom box-shadow values outside the system tokens
- Don't use arbitrary border-radius values — pick from the defined scale
- Don't duplicate component patterns — check Section 4 first
- Don't use backdrop-blur or blur effects

### Anti-Patterns (detected from codebase)

- No blur or backdrop-blur effects
- No zebra striping on tables/lists


---

## 9. Responsive Behavior

| Name | Value | Source |
|---|---|---|
| xs | 320px | css |
| sm | 600px | css |
| md | 767px | css |
| md | 768px | css |
| lg | 1023px | css |
| lg | 1024px | css |
| xl | 1119px | css |
| xl | 1120px | css |
| xl | 1136px | css |

**Approach:** Use `@media (min-width: ...)` queries matching the breakpoints above.


---

## 10. Agent Prompt Guide

Use these as starting points when building new UI:

### Build a Card

```
Background: #f6f6f6
Border: 1px solid #333333
Radius: 12px
Padding: 16px
Font: UberMove
Use shadow tokens from Section 6.
```

### Build a Button

```
Primary: bg var(--accent), text white
Ghost: bg transparent, border #333333
Padding: 8px 16px
Radius: 12px
Hover: opacity 0.9 or lighter shade
Focus: ring with var(--accent)
```

### Build a Page Layout

```
Background: #ffffff
Max-width: 1136px, centered
Grid: 4px base
Responsive: mobile-first, breakpoints from Section 9
```

### Build a Stats Card

```
Surface: #f6f6f6
Label: #525252 (muted, 12px, uppercase)
Value: #111111 (primary, 24-32px, bold)
Status: use success/warning/danger from Section 2
```

### Build a Form

```
Input bg: #ffffff
Input border: 1px solid #333333
Focus: border-color var(--accent)
Label: #525252 12px
Spacing: 16px between fields
Radius: 12px
```

### General Component

```
1. Read DESIGN.md Sections 2-6 for tokens
2. Colors: only from palette
3. Font: UberMove, type scale from Section 3
4. Spacing: 4px grid
5. Components: match patterns from Section 4
6. Elevation: shadow tokens
```
