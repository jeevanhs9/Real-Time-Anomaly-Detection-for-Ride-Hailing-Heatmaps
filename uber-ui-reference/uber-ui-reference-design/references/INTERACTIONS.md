# Interaction Reference

> Micro-interactions extracted from live DOM. Recreate these exactly for authentic feel.

## Coverage

| Component Type | Count | States Captured |
|----------------|-------|----------------|
| Button | 3 | default, hover, focus |
| Role Button | 1 | default, hover, focus |
| Link | 3 | default, hover, focus |
| Input | 2 | default, hover, focus |

## Transition System

These transition declarations were extracted from interactive elements:

```css
transition: background 0.2s cubic-bezier(0, 0, 1, 1);
transition: all;
transition: backgroundSize 0.5s cubic-bezier(0.22, 1, 0.36, 1);
```

Apply these to all interactive elements. Never invent new durations or easings.

## Button Interactions

### Button 1 — `About`

**States:**

- Default: `../screens/states/button-1-default.png`
- Hover: `../screens/states/button-1-hover.png`
- Focus: `../screens/states/button-1-focus.png`

**On hover:**

```css
/* box-shadow: none → */ box-shadow: rgba(236, 236, 236, 0.15) 999px 999px 0px 0px inset;
```

**On focus:**

```css
/* box-shadow: none → */ box-shadow: rgb(252, 252, 252) 0px 0px 0px 2px inset, rgb(39, 110, 241) 0px 0px 0px 2px;
```

**Transition:** `background 0.2s cubic-bezier(0, 0, 1, 1)`

### Button 2 — `EN`

**States:**

- Default: `../screens/states/button-2-default.png`
- Hover: `../screens/states/button-2-hover.png`
- Focus: `../screens/states/button-2-focus.png`

**On hover:**

```css
/* box-shadow: none → */ box-shadow: rgba(236, 236, 236, 0.15) 999px 999px 0px 0px inset;
```

**On focus:**

```css
/* box-shadow: none → */ box-shadow: rgb(252, 252, 252) 0px 0px 0px 2px inset, rgb(39, 110, 241) 0px 0px 0px 2px;
```

**Transition:** `background 0.2s cubic-bezier(0, 0, 1, 1)`

### Button 3 — `Sign up`

**States:**

- Default: `../screens/states/button-3-default.png`
- Hover: `../screens/states/button-3-hover.png`
- Focus: `../screens/states/button-3-focus.png`

**On hover:**

```css
/* background-color: rgb(255, 255, 255) → */ background-color: rgb(226, 226, 226);
/* box-shadow: none → */ box-shadow: rgba(236, 236, 236, 0.15) 999px 999px 0px 0px inset;
```

**On focus:**

```css
/* background-color: rgb(255, 255, 255) → */ background-color: rgb(226, 226, 226);
/* box-shadow: none → */ box-shadow: rgb(252, 252, 252) 0px 0px 0px 2px inset, rgb(39, 110, 241) 0px 0px 0px 2px;
```

**Transition:** `background 0.2s cubic-bezier(0, 0, 1, 1)`

## Role Button Interactions

### Role Button 1 — `Auto-fill my location`

**States:**

- Default: `../screens/states/role-button-1-default.png`
- Hover: `../screens/states/role-button-1-hover.png`
- Focus: `../screens/states/role-button-1-focus.png`

**On focus:**

```css
/* outline: 3px none rgb(17, 17, 17) → */ outline: 5px auto rgb(16, 16, 16);
/* outline-color: rgb(17, 17, 17) → */ outline-color: rgb(16, 16, 16);
```

**Transition:** `all`

## Link Interactions

### Link 1 — `Uber`

**States:**

- Default: `../screens/states/link-1-default.png`
- Hover: `../screens/states/link-1-hover.png`
- Focus: `../screens/states/link-1-focus.png`

**On focus:**

```css
/* outline: 3px none rgb(255, 255, 255) → */ outline: 3px solid rgb(39, 110, 241);
/* outline-color: rgb(255, 255, 255) → */ outline-color: rgb(39, 110, 241);
```

**Transition:** `backgroundSize 0.5s cubic-bezier(0.22, 1, 0.36, 1)`

### Link 2 — `Ride`

**States:**

- Default: `../screens/states/link-2-default.png`
- Hover: `../screens/states/link-2-hover.png`
- Focus: `../screens/states/link-2-focus.png`

**On hover:**

```css
/* box-shadow: none → */ box-shadow: rgba(236, 236, 236, 0.15) 999px 999px 0px 0px inset;
```

**On focus:**

```css
/* box-shadow: none → */ box-shadow: rgb(252, 252, 252) 0px 0px 0px 2px inset, rgb(39, 110, 241) 0px 0px 0px 2px;
```

**Transition:** `background 0.2s cubic-bezier(0, 0, 1, 1)`

### Link 3 — `Drive`

**States:**

- Default: `../screens/states/link-3-default.png`
- Hover: `../screens/states/link-3-hover.png`
- Focus: `../screens/states/link-3-focus.png`

**On hover:**

```css
/* box-shadow: none → */ box-shadow: rgba(236, 236, 236, 0.15) 999px 999px 0px 0px inset;
```

**On focus:**

```css
/* box-shadow: none → */ box-shadow: rgb(252, 252, 252) 0px 0px 0px 2px inset, rgb(39, 110, 241) 0px 0px 0px 2px;
```

**Transition:** `background 0.2s cubic-bezier(0, 0, 1, 1)`

## Input Interactions

### Input 1 — `Pickup location needs to be filled in`

**States:**

- Default: `../screens/states/input-1-default.png`
- Hover: `../screens/states/input-1-hover.png`
- Focus: `../screens/states/input-1-focus.png`

**Transition:** `all`

_No visible style changes detected for this element._

### Input 2 — `Dropoff location needs to be filled in`

**States:**

- Default: `../screens/states/input-2-default.png`
- Hover: `../screens/states/input-2-hover.png`
- Focus: `../screens/states/input-2-focus.png`

**Transition:** `all`

_No visible style changes detected for this element._

## Interaction Rules

- Hover effects include **color transitions** — use the extracted values, not approximations
- Focus states use **outline** (not box-shadow) — always match the extracted focus ring
- Transition durations in use: `0.2s`, `0.5s`
- Always respect `prefers-reduced-motion` — set all transitions to `0s` when enabled

