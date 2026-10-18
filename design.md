# Templix — Design Specification

Version 0.1 · Source of truth for visuals: the Stitch export in `design/stitch/` (six `screen.png` +
`code.html`, plus `professional_document_canvas/DESIGN.md`). This document **translates** that export into
buildable rules and **corrects** the places where the mock-ups are wrong or dishonest for the product we are
building (see §12). Companion docs: `functional-requirements.md` (FR ids), `non-functional-requirements.md`
(NFR ids), `system-architecture.md`, `decisions.md` (D-019).

**How to use with the Stitch files.** `screen.png` = visual target. `code.html` = reference markup (Tailwind
v3 CDN, Inter + Material Symbols from Google CDN, hard-coded demo data). **Do not copy `code.html` into the
app.** Re-implement each screen as typed React components using the tokens below, self-hosted fonts/icons,
and real data. Keep the markup's structure and class intent where they help.

---

## 1. Brand and principles

Calm, familiar, professional — "LinkedIn-like": white cards on a warm grey canvas, 1-px borders, pill actions,
Inter, one confident blue. **Light theme only** (D-020): no dark theme, no `dark:` classes, no theme toggle.

1. **Trust through truth.** Status, scores and privacy statements are computed and specific (D-012, D-023).
2. **Design is locked, content is free.** Locked/fixed/editable states are always visible and consistent.
3. **Dense but legible.** Desktop-first productivity UI; 14-px base; no decorative gradients or illustrations.
4. **Everything reachable by keyboard**, every state labelled (not colour-only).
5. **Quiet motion.** 150 ms transitions; respect `prefers-reduced-motion`.

## 2. Design tokens

### 2.1 Colour (canonical)

Canvas and surfaces (resolves Stitch's inconsistent `#F4F3F0`/`#FAF9F6` usage — D-019):

| Token (CSS var `--color-*`) | Hex | Use |
|---|---|---|
| `canvas` | `#F3F2EF` | App background (every screen) |
| `card` | `#FFFFFF` | Cards, panels, bars, dialogs |
| `border` | `#E0DFDC` | 1-px card/input-container borders |
| `border-strong` | `#CDCAC5` | Hover border |
| `divider` | `#EBEAE7` | Inner row separators |
| `search-bg` | `#EDF3F8` | Top-bar search field |
| `ink` | `#191919` | Primary text (maps to Stitch `on-surface`) |
| `ink-2` | `#666666` | Secondary text, inactive icons |
| `ink-disabled` | `#A0A09E` | Disabled |
| `brand` | `#0A66C2` | Primary interactive (Stitch `primary-container`) |
| `brand-hover` | `#004182` | Hover/pressed |
| `brand-tint` | `#EBF4FD` | Selected rows, info banners, badges |
| `success` / `success-bg` | `#057642` / `#E6F4EA` | Ready, saved, passed |
| `warning` / `warning-bg` | `#B24020` / `#FDF2E9` | Needs review, near-limit |
| `error` / `error-bg` | `#CC1016` / `#FCE8E6` | Errors, blockers |
| `scrim` | `rgba(0,0,0,.6)` | Modal backdrop |

Compatibility set (keep so Stitch markup/names stay portable): `primary #004E99`, `on-primary #FFFFFF`,
`primary-container #0A66C2`, `on-primary-container #DBE6FF`, `primary-fixed #D6E3FF`, `inverse-primary #A8C8FF`,
`secondary #565F67`, `secondary-container #D8E1EA`, `tertiary #005B31`, `tertiary-container #057642`,
`error #BA1A1A`, `error-container #FFDAD6`, `surface #FAF9F6`, `surface-container-low #F4F3F0`,
`surface-container #EFEEEB`, `surface-container-high #E9E8E5`, `surface-container-highest #E3E2DF`,
`outline #727783`, `outline-variant #C1C6D4`, `on-surface-variant #414752`. **Rule:** components use the
semantic tokens above (`canvas`, `card`, `ink`, `brand`, …); compatibility names exist only for reference.

Overlay colours for the analysis canvas (§8.2):

| Role class | Token | Hex | Line style |
|---|---|---|---|
| Headings | `ov-heading` | `#0A66C2` | solid 1.5 px |
| Text | `ov-text` | `#057642` | solid 1.5 px |
| Image / vector | `ov-media` | `#0E7C86` | solid 1.5 px |
| Shape / rule | `ov-shape` | `#666666` | dashed |
| Review | `ov-review` | `#B24020` | **dashed** 1.5 px + warning icon in chip (not colour-only) |

All text/background pairs must satisfy NFR-A11Y-03; a unit test computes contrast for every declared pair.

### 2.2 Typography — Inter only

| Token | Size / line | Weight | Tracking | Use |
|---|---|---|---|---|
| `headline-xl` | 24 / 32 | 600 | −0.015em | Page titles (max size anywhere) |
| `headline-lg` | 20 / 28 | 600 | −0.01em | Card titles, dialog titles |
| `headline-md` | 16 / 24 | 600 | −0.005em | Card headers, template names |
| `body-lg` | 15 / 22 | 400 | 0 | Lead paragraphs |
| `body-md` | 14 / 20 | 400 | 0 | Default text |
| `body-sm` | 12 / 16 | 400 | 0 | Metadata, helper |
| `label-lg` | 14 / 20 | 600 | 0 | Buttons, tabs |
| `label-md` | 12 / 16 | 600 | 0 | Chips, field labels |
| `label-sm` | 11 / 14 | 500 | +0.01em | Nav labels, tags, status bar |

Monospace (`ui-monospace`, system stack) only for numeric readouts such as coordinates (`X:48 Y:64`) and
the footer version. Numbers in counters and metrics use `font-variant-numeric: tabular-nums`.

### 2.3 Spacing, radii, elevation, motion

- Spacing scale: `xs 4`, `sm 8`, `md 16`, `lg 24`, `xl 32` px; layout gutter 24 (`gutter`), compact gutter 16.
- Radii: containers/cards 8 px · inputs/selects 4 px · buttons, chips, badges, avatars **pill (9999 px)**.
- Elevation (never heavier):
  - L1 card: `0 0 0 1px #E0DFDC, 0 1px 3px rgba(0,0,0,.08)`
  - L2 hover/drag: `0 0 0 1px #CDCAC5, 0 4px 12px rgba(0,0,0,.12)`
  - L3 popovers/dialogs/floating toolbars: `0 0 0 1px #E0DFDC, 0 8px 24px rgba(0,0,0,.15)`
- Motion: `150ms ease-in-out` for hover/focus/colour; dialogs fade + 2 % scale in 120 ms; progress bars 300 ms.
  Under `prefers-reduced-motion: reduce` all transitions ≤ 1 ms and skeleton shimmer is static.
- Focus ring: `outline: 2px solid var(--color-brand); outline-offset: 2px` on every focusable element
  (`:focus-visible`), never removed.

### 2.4 Tailwind v4 theme (put in `packages/ui/src/theme.css`)

```css
@import "tailwindcss";

@theme {
  --font-sans: "Inter Variable", "Inter", system-ui, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;

  --color-canvas: #f3f2ef;   --color-card: #ffffff;
  --color-border: #e0dfdc;   --color-border-strong: #cdcac5;  --color-divider: #ebeae7;
  --color-search-bg: #edf3f8;
  --color-ink: #191919;      --color-ink-2: #666666;          --color-ink-disabled: #a0a09e;
  --color-brand: #0a66c2;    --color-brand-hover: #004182;    --color-brand-tint: #ebf4fd;
  --color-success: #057642;  --color-success-bg: #e6f4ea;
  --color-warning: #b24020;  --color-warning-bg: #fdf2e9;
  --color-error: #cc1016;    --color-error-bg: #fce8e6;
  --color-ov-heading: #0a66c2; --color-ov-text: #057642; --color-ov-media: #0e7c86;
  --color-ov-shape: #666666;   --color-ov-review: #b24020;
  /* + the compatibility set from §2.1 as --color-primary, --color-primary-container, … */

  --radius-input: 0.25rem;  --radius-card: 0.5rem;  --radius-pill: 9999px;

  --spacing-gutter: 1.5rem; --spacing-gutter-sm: 1rem;

  --shadow-l1: 0 0 0 1px #e0dfdc, 0 1px 3px rgb(0 0 0 / .08);
  --shadow-l2: 0 0 0 1px #cdcac5, 0 4px 12px rgb(0 0 0 / .12);
  --shadow-l3: 0 0 0 1px #e0dfdc, 0 8px 24px rgb(0 0 0 / .15);

  --text-headline-xl: 1.5rem;   --text-headline-xl--line-height: 2rem;
  --text-headline-lg: 1.25rem;  --text-headline-lg--line-height: 1.75rem;
  --text-headline-md: 1rem;     --text-headline-md--line-height: 1.5rem;
  --text-body-lg: .9375rem;     --text-body-lg--line-height: 1.375rem;
  --text-body-md: .875rem;      --text-body-md--line-height: 1.25rem;
  --text-body-sm: .75rem;       --text-body-sm--line-height: 1rem;
  --text-label-sm: .6875rem;    --text-label-sm--line-height: .875rem;
}

/* weight + tracking pairs (portable across v4 minors) */
@utility text-headline-xl { font-size: 1.5rem; line-height: 2rem; font-weight: 600; letter-spacing: -0.015em; }
@utility text-headline-lg { font-size: 1.25rem; line-height: 1.75rem; font-weight: 600; letter-spacing: -0.01em; }
@utility text-headline-md { font-size: 1rem; line-height: 1.5rem; font-weight: 600; letter-spacing: -0.005em; }
@utility text-label-lg { font-size: .875rem; line-height: 1.25rem; font-weight: 600; }
@utility text-label-md { font-size: .75rem; line-height: 1rem; font-weight: 600; }
@utility text-label-sm { font-size: .6875rem; line-height: .875rem; font-weight: 500; letter-spacing: .01em; }

@layer base {
  html { color-scheme: light; }
  body { background: var(--color-canvas); color: var(--color-ink); font: 400 .875rem/1.25rem var(--font-sans); }
  :focus-visible { outline: 2px solid var(--color-brand); outline-offset: 2px; }
}
```
(If the installed Tailwind version differs, keep the **token names and values**; adapt syntax.)

## 3. Iconography

Material Symbols **Outlined**, weight 400, optical size 20 (24 for large actions), `FILL 0` default and
`FILL 1` for active nav/selected states, self-hosted (D-018). Icon-only buttons are 36×36 circles with
`aria-label` and tooltip. Icon names used by the Stitch screens (keep): `home, grid_view, description, memory,
shield, notifications, search, layers, palette, rule, visibility, lock, lock_open, expand_more, chevron_right,
fit_screen, add, remove, undo, redo, save, download, picture_as_pdf, auto_awesome, tune, check_circle,
verified_user, warning, info, image, edit, history, grid_4x4, event, link, arrow_back, arrow_forward,
upload_file, refresh, settings, key`. (`mic` is **not** used, D-020.)

## 4. Components

Each component ships in `packages/ui` with Storybook-style examples (or a `/dev/ui` route) covering all states.

| Component | Spec |
|---|---|
| **TopBar (app shell)** | 56 px, `card`, bottom 1-px `border`; container ≤ 1128 px; logo tile 32 px (`brand`, white layers icon) + "Templix" `headline-md` + chip `LOCAL`(see §9: label is **"LOCAL APP"**); search 34 px `search-bg` pill-ish (radius 4), icon prefix, placeholder "Search templates, documents, styles…"; nav tabs (icon over `label-sm`; inactive `ink-2`; active `ink` + brand icon + 2-px brand underline flush with bar bottom); bell (36 px, dot when unread); profile chip (avatar 32 + name + role + caret). Tab labels: **Home · Templates · Documents · Models · Privacy**. |
| **TopBar (workspace shell)** | Same height; left: logo tile + "Templix" + chip, divider, back link/breadcrumb; center-left: **FileChip**; right: status pill(s), icon buttons, secondary + primary pill buttons, avatar. Items never wrap: `white-space: nowrap`, truncate with ellipsis + tooltip. |
| **StatusBar** | 32 px footer, `card`, top border; `label-sm`; left: green dot + "Engine ready", active AI engine, RAM; right: privacy mode, "No telemetry", links (Shortcuts, Docs, Help), version in mono. All values computed. |
| **Button** | Pill. Sizes: `sm` 28 px (padding 4/12, 12 px), `md` 32 px (6/16, 14 px semibold), `lg` 40 px, `xl` 48 px (mode picker). Variants: **primary** (`brand` bg, white text, hover `brand-hover`), **secondary** (1-px `brand` border, transparent, brand text, hover `brand-tint` + 1.5 px border), **tertiary/ghost** (`ink-2` → `ink`, hover `rgba(0,0,0,.04)`), **danger** (white bg, `error` border/text; confirm dialogs use solid error), **warning-solid** (`warning` bg, white — used for *Review & adjust*). States: hover, active (darker), focus-visible ring, disabled (`ink-disabled`, no pointer), loading (spinner left, label kept, `aria-busy`). |
| **IconButton** | 36 px circle, ghost, `ink-2` icon, hover fill `rgba(0,0,0,.04)`; toggled state uses `brand-tint` fill + brand icon. |
| **Chip / Tag** | Status tag 24 px pill, `label-sm`, padding 2/10: Ready/Synced (`success` on `success-bg`), Pending/Local/In-progress (`brand` on `brand-tint`), Needs review/Flagged (`warning` on `warning-bg`), Error (`error` on `error-bg`), Neutral (`ink-2` on `canvas`). Always includes text (and an icon for warning/error). Filter chip: 32 px pill, 1-px `ink-2` border, white; active = `brand` fill + white text, no border. |
| **Card** | `card` bg, L1 shadow, radius 8; header row (title `headline-md`, optional right action), body padding 16 (24 for work areas), footer with top `divider` and action buttons. Hover (only interactive cards) → L2. |
| **FileChip** | Pill with document icon, truncated file name (≤ 28 ch + tooltip), muted "· 2 pages · 24 layers". |
| **Input / Textarea / Select** | 36 px height (textarea auto min 80), white, 1-px `ink-2` border, radius 4, padding 0 12; hover border `ink`; **focus: 2-px `brand` border** (use `box-shadow: 0 0 0 1px brand` to avoid layout shift); error: `error` border + message with icon; disabled: `canvas` bg. Label above (`label-md`), helper below (`body-sm`, `ink-2`), counter right of label. |
| **Counter** | `body-sm` tabular; ok `ink-2`; near (≥ 90 %) `warning`; over `error` + bold; always paired with text ("Over by 3"), not colour alone. |
| **Switch** | 36×20 pill; off `border-strong`, on `brand` (green is reserved for statuses); label to the left or right; keyboard Space toggles; `role="switch"`. |
| **Checkbox / Radio** | 18 px; 1.5-px `ink-2` border; checked `brand` fill + white check / 6-px centre dot. |
| **Tabs** | Radix Tabs; label with icon + optional count badge; active = brand text + 2-px underline; tab panel scrolls independently. |
| **Accordion** | Radix; header 44 px: chevron, title `label-lg`, right-side state (`Complete` with check in `success`, `ACTIVE SYNC` tag, or "1 Article"); body padding 16; only one expanded unless "Expand all". |
| **Banner** | Full-width info (`brand-tint`), success (`success-bg`), warning (`warning-bg`), error (`error-bg`); icon + text + actions right; `role="status"`/`alert` accordingly. |
| **Dialog** | Radix Dialog, L3, radius 8, max-width 480/640, scrim `rgba(0,0,0,.6)`, title `headline-lg`, actions right-aligned (secondary then primary), focus trapped, Esc closes unless destructive in-progress. |
| **Toast** | Bottom-left stack, L3, 4 s (errors persist), `aria-live="polite"` (assertive for errors). |
| **Progress** | 6-px track `divider`, fill `brand`; label left, percent right (tabular). |
| **Tooltip** | Radix; dark `#191919` bg, white `label-sm`; 300 ms delay; also on keyboard focus. |
| **Template card** | See §8.1. Thumbnail is the real page-1 raster; status tag overlay top-right of thumbnail. |
| **Layer row** | 36 px; eye · lock · name · role-chip/state (`Edit` switch, `Fixed`, `Slot` tag); selected row `brand-tint` + 2-px left brand bar; review row `warning-bg` with warning icon and **Inspect** link. |
| **Overlay box** | Absolutely positioned over canvas, `pointer-events: none` except handles; label chip above top-left; 8 resize handles (8 px squares, `card` fill, 1.5-px role colour) only on the selected layer and only in Template-edit contexts. |
| **Split viewer** | `react-resizable-panels`; 4-px drag bar `border`, turns `brand` on hover/drag, `role="separator"` with arrow-key resizing (10 px steps). |
| **Floating canvas toolbar** | Pill, `card`, L3, centred at canvas bottom (16 px above status bar); zoom −/value/+, fit, page nav, grid toggle; canvas scroll area has `padding-bottom: 96px` so content is never covered. |
| **Diff card** | Card with title row (slot label + page, right-aligned counter chip), "ORIGINAL (PDF SOURCE)" block (`canvas` bg, struck-through text), "AI PROPOSAL (provider · model)" block (`success-bg`, 1-px `success` border), footer: target note + **Reject** (secondary) + **Accept** (primary). |
| **Chat bubble** | Assistant: avatar 28 px circle (`brand-tint`, sparkle icon), name label, bubble `canvas`→ white with `border`, radius 12 (top-left 4); user: right-aligned `brand-tint` bubble. Draft quote card inside a bubble uses `success-bg` + success border. |
| **Quick replies** | Row of outlined pill buttons under the last assistant message ("Keep as is", "Replace", "Skip"). |

## 5. Layout system

- **App shell:** TopBar (56) + page container `max-width 1128px`, margin `0 auto`, side margin 24, 12-column grid, gutter 24.
- **Workspace shell:** TopBar (56) + (optional banner row 48) + fixed-height app body (`100dvh − bars`) with independently scrolling panes; StatusBar (32).
- **Dotted canvas:** `radial-gradient(#D6D5D1 1px, transparent 1px)` at 16 px grid on `canvas` (editors only).
- **Page card on canvas:** white, L1, true page aspect (e.g. Letter 612×792 pt) scaled by zoom; centred with 24-px min margin.

## 6. Interaction patterns

- **Selection sync:** hover/selection in canvas ↔ tree/sidebar uses the same `selection` store; the target scrolls into view with `scroll-margin` of 80 px.
- **Autosave pill:** `Saving…` (spinner) → `Auto-saved locally` (green check) → `Save failed — retrying` (amber) ; aria-live polite.
- **Undo/redo:** toolbar + shortcuts; toast "Undid: Edit headline" with *Redo* link for 4 s.
- **Destructive actions** use a dialog with the object name; irreversible wipes require typing `DELETE`.
- **Long operations** (ingest, export) show a progress card with stage label, percent, **Cancel**, and are mirrored in the bell notifications.
- **Empty states:** one-line explanation + primary action; no illustrations.
- **Loading:** skeletons matching final geometry (cards, rows); never full-page spinners.

## 7. Responsive behaviour (D-020: desktop first)

| Width | Behaviour |
|---|---|
| ≥ 1280 | As specified (3-column app shell; 3-pane editors) |
| 1024–1279 | App shell stays 3-column with rails 225/300; editors: sidebars 320; AI right panel collapses into a tab beside chat ("Chat / Changes") |
| 768–1023 | Left rail becomes a drawer; right rail stacks under main; editors show canvas + one panel at a time with a segmented control |
| < 768 | Not supported; show a notice recommending a larger window (FR-SYS-09). Bottom-pinned nav from DESIGN.md is **not** built in v1 |

## 8. Screens

Common: every screen has loading, empty, error and "no provider" variants where relevant (§10). Numbers and
status strings are **bound to data** (list in each "Data" line). Routes use React Router.

### 8.1 Home — `templix_desktop_home` → route `/` (App shell) · FR-HOME-*

Grid: **left 3 cols / main 6 / right 3**.

- **Left rail**
  - *Profile card:* 56-px banner (`brand-tint` with subtle dot pattern), 72-px avatar (initials, `brand`), name (`headline-md`), team (`body-sm`), organisation chip (e.g. "Student Publishing Board" — user-editable text); rows: Templates managed (count, brand), Documents created (count, brand), Local storage (`ink`, "124 MB used" computed). Links: **My Drafts** (count chip), **Imported Brand Assets**, **Saved Style Rules** (the latter two hidden until P2).
  - *Workspace Settings card:* title + tune icon; *Active AI engine* mini-card: provider · model, status dot, **Switch** (AI features on/off); helper text (see §9 `home.engine.*`). Link "Manage models".
- **Main**
  - *Upload card:* title "Recreate an existing document", description, info icon (tooltip), dashed 2-px `brand` border drop zone (`brand-tint` bg), icon, "Drag & drop your reference document here", "Supports multi-page PDF (up to 50 MB)", buttons **Browse files** (primary) + **Try sample newsletter PDF** (secondary), footnote row with two items: *"Analysis runs on this device"* (shield icon) · *"Splits text, images, shapes, rules and spacing into layers"* (sparkle). During upload: file chip + progress + Cancel replaces buttons.
  - *Active Templates:* header "Active Templates" + inline count "(6 templates)" (baseline-aligned, never wraps) + filter chips (All · Newsletters · Reports · Flyers & Posters). 2-column grid of **TemplateCard**:
    thumbnail (16:10, real raster, 1-px border, `canvas` bg) with status tag top-right; name (`headline-md`, 1-line ellipsis + tooltip); meta `body-sm` "12 layers extracted · 2 pages · Last used 3 days ago"; footer buttons: ready → **Create new document** (primary, flex) + **Edit** (secondary); needs review → **Review & adjust** (warning-solid) + **Layers** (secondary outlined `ink`); processing → progress bar + Cancel; failed → error tag + **Retry** / ⋯ delete.
- **Right rail**
  - *Recent documents:* title + **View all**; items: title (link, 1-line), "Updated 2 hours ago", status chip, trailing arrow (open) or download icon (exported); `divider` between.
  - *Privacy card:* 4-px `brand` left accent, shield icon, title and body **from §9 `privacy.card.*`** (state-driven), computed status row (e.g. "No AI provider connected" / "Anthropic · connected"), link "How Templix handles your data →" → Settings → Privacy.
  - *Tip card:* lightbulb, "Tip: AI Assist vs Manual Edit" + two bullets (dismissible).
  - *Footer:* About · Accessibility · Privacy · "Templix v{version}".
- **Data:** `GET /templates`, `GET /documents?limit=5`, `GET /status`, `GET /providers`. **States:** first-run empty (no templates) shows only the upload card + onboarding hint.

### 8.2 Document Layer Analysis — `templix_document_layer_analysis` → `/templates/:id/analysis` (Workspace shell) · FR-ING-*, FR-TPL-*

- **Top bar:** logo "Tx" tile + "Templix" + `LOCAL APP` chip; `← Templates`; FileChip ("Campus_Monthly_Newsletter_Mar… · 2 pages · 24 layers"); bell; **Export Template** (secondary, hidden until P3); **Proceed to Edit →** (primary); avatar.
- **Banner (48 px, `brand-tint`):** sparkles/ring icon; bold "Analysis {n}% confident" + "— {k} items need your review ({breakdown})"; buttons **Review items** (primary sm, flag icon) and **Accept all detected** (secondary sm). All numbers from `analysis.confidence`, `reviewItems`.
- **Left column (≈ 220–260):** *Pages card* — title "Pages" + count chip, grid/list toggle; thumbnails (active has 2-px brand border and "Page 1 (Active)" label; shows layer count; confidence chip like "98%" on the thumbnail); dashed **Upload additional page** (P2, hidden in P1); "Orientation: Letter (Portrait)" row. *Data-flow card (success-bg):* lock icon; **"Analysis ran on this device"** / **"Page images were sent to {Provider}"** (computed) .
- **Center:** toolbar card (− 100% + · Fit to screen · ☑ Toggle overlays · legend dots Headings/Text/Review); page card with overlays; hint line "Click any layer in the canvas or inspector to edit detection bounds and layout lock rules." Optional **Fidelity** chip (score + heatmap toggle) in toolbar. Page uses **reference raster as underlay**? — **No:** show the *reconstruction* rendered by `render-core`; a toggle "Compare with original" switches to the split viewer (FR-TPL-18).
- **Right column (360 px):** card with tabs **Layers (18) · Styles · Rules ●**.
  - *Layers:* filter input + **Collapse all**; tree (Page n (k layers) with "ALL BOUNDED" success label → computed; groups "Header Container", "Main Content"; rows per §4 "Layer row"); review rows show **Inspect**.
  - *Selected layer inspector* (below tree, scrolls with panel): heading "SELECTED LAYER INSPECTOR" + role chip; layer name with role-colour dot; rows Font · Color (swatch + hex + name) · Metrics (line height, tracking) · Position / Size (mono `X:48 Y:64 · W:820 H:48`) · Margin Offset; **info box** "Format locked: …"; footer buttons **Save as Template** (primary, full width) and **Open in AI Assist Editor** (secondary, full width).
  - *Styles tab:* token groups (Colours, Text styles, Spacing) with usage counts. *Rules tab:* rule list with severity icons, add rule.
- **Canvas overlays:** per §2.1 colours; label chip text `[Heading 1] Title: Campus Chronicle • 820×48px (x:48, y:64)`; review layer shows icon + "Needs Review: Low Contrast" and a contrast ratio chip; selected layer: 8 handles.
- **Data:** `GET /templates/:id/analysis`, SSE `/jobs/:id/events` while ingesting (progress overlay card on canvas), fidelity from analysis. **States:** processing (skeleton canvas + progress card with stages), failed (error banner + Retry), blocking review items (Proceed disabled with tooltip, or confirm dialog).

### 8.3 Choose Creation Mode — `templix_choose_creation_mode` → `/templates/:id/mode` (Workspace shell compact) · FR-MODE-*

- Top bar: logo + chip; `← Back to Document Analysis`; FileChip with name, pages, layers.
- Centered column (max 1128): pill "● Step 2 of 3 · Creation Mode" (steps: **1 Analyse · 2 Choose mode · 3 Create & export**); H1 `headline-xl` "How do you want to create your new document?"; subtext (centered, `ink-2`) "Choose how you'd like to draft new content into your locked template structure. You can switch between modes at any time."
- Two equal cards (gap 24): each has icon in 56-px `brand-tint` circle, corner tag (Recommended / Precision), title + small tag (Fastest / Exact spec), description, two capability chips, divider, three check-list items, full-width `xl` primary button "Continue with AI Assist →" / "Continue with Manual Edit →".
  - **AI Assist chips:** "Bring your own API key" · "Local models: coming soon" (neutral, not green). **Checklist:** "Guided interview, section by section" · "Works with OpenAI, Anthropic, Google, or any OpenAI-compatible service" · "Every suggestion is checked against your template's text limits". If no provider: replace button with **Add an API key** (secondary) + helper text.
  - **Manual chips:** "Live preview" · "Full control". **Checklist:** "Side-by-side live canvas with instant re-render" · "Character counts, line limits and image crop for every field" · "Locked margins and baselines you cannot break".
- Privacy note card below (`success-bg`, shield): copy from §9 `privacy.mode.*`; link → Settings → Privacy. Page scrolls so nothing is clipped (Stitch cut the last line).

### 8.4 Manual Content Editor — `templix_manual_content_editor` → `/documents/:id/manual` (Workspace shell) · FR-MAN-*

- **Top bar:** logo; `← Back to Modes`; FileChip with "Draft" suffix (inline-rename on click); autosave pill; undo/redo IconButtons; **Save Draft** (secondary); **Export PDF** (primary, download icon); engine chip ("● Engine Active" → computed "Ready"); settings icon; avatar.
- **Canvas pane (flex-1):** info strip (above page): `Letter Format (8.5 × 11 in)` chip · `Fidelity {0.98}` with tooltip "How closely the template reproduces the original" · right: lock icon "Bounding-box locks active". Page card (≈ 660 px at 100 %). Selected element: 2-px brand outline + 8 handle **dots hidden** (no moving in this mode) + role chip `[Heading 1 · Lead Story]` top-left. Floating toolbar bottom-center (§4).
- **Sidebar (360 px):** header "Edit content" + chip "Editing Page 1" + **Expand all**; description; warning Banner(s) (e.g. *Line Length Warning* + **Auto-fit text** link) and success Banner ("5 design rules passed (margins, font hierarchy, contrast)") — both computed; accordion list:
  - *Cover & Masthead* — state "Complete".
  - *Lead Editorial Story* — "ACTIVE SYNC": **Story Headline** (input, counter `64/65`), **Author / Byline** (input), **Feature Image** (card: thumbnail, filename, size, **Replace image**, **Crop**, "Locked 16:9" tag), **Story Body Copy** (rich text with B / I / link toolbar; footer "✓ 182 / 200 words — Perfect fit · 2 Paragraphs").
  - *Articles & Highlights* — "1 Article": repeater list item (title, "Author: Marcus Chen · 48 words", edit pencil), **+ Add article**.
  - Sticky footer: **Section History** (ghost, history icon) + **Apply to All Pages** (primary pill).
- **Data/bindings:** sections/slots from template; values from content store; counters from slot constraints; banners from rules report. **States:** no required fields → "Complete"; rule error → red section state; export blockers shown on Export button badge.

### 8.5 AI Assist Editor — `templix_ai_assist_editor` → `/documents/:id/ai` (Workspace shell) · FR-AI-*

- **Top bar:** logo + chip; `← Back to Modes`; **Model pill** (provider logo-less icon · `claude-… / gpt-… / gemini-…` · latency "412 ms" · privacy badge "Sends text to Anthropic") with caret opening the model menu; FileChip + "✓ Saved"; undo/redo; **Save Draft**; **Export PDF**; avatar.
- **Left pane (360 px) — Interview:** header "AI Assist Interview" with sparkle, right "Step 3 of 7" chip; progress bar + "Lead Story Headline — 45% Complete" (computed from plan); date divider ("Today · This session"); messages (assistant name "Templix Assist"); quick-reply chips; composer (textarea "Type your answer, paste raw notes, or suggest changes…", attach icon, tune icon → model/temperature popover, round send button; **no mic**); status line under composer: "● Drafting with {Provider} · text of this section is sent to the provider" (during calls) / idle: "Ready".
- **Center pane — Live preview:** top chip "● [Drafting: Lead Story Headline · Live Preview Diff]" and "Slot height: 58px / 60px max" (computed); preview defaults to **Fit width** (never clipped); pending slot shows `success-bg` tint + tag "Active Slot (Diff Highlight)"; floating toolbar: zoom, Fit width, page nav "Page 1 of 2", ☑ **Highlight AI changes**, **Grid guides**.
- **Right pane (360 px) — Proposed Changes:** header "Proposed Changes" + chip "3 Pending · 1 Accepted"; **Apply all** (primary sm) + **Discard all** (ghost); success banner "All proposed text fits locked font sizes & line limits without overflow" (computed, otherwise warning list); diff cards (text, image before/after with auto-crop, date before→after); footer card **Layout Protection Guarantee** — "AI can change content only. Fonts, sizes, spacing and locked layers cannot be edited." (true by contract, §9.6).
- **Data:** AI session state, ledger-derived latency, rules/fit report; SSE token stream. **States:** no provider (empty state in left pane with CTA), consent pending (dialog §8.7), rate-limited/error (inline assistant message with Retry), streaming (typing indicator; **Stop** button replaces send).

### 8.6 Settings — `templix_settings_ai_models` → `/settings/:section` (App shell) · FR-SET-*

Sections: `general`, `ai-models` (this mock), `fonts`, `privacy`.

- **Header row:** breadcrumb "Settings › AI Models & Inference" and, right, a **status pill** computed ("● No provider connected" / "● {Provider} connected").
- **Left (3 cols):** *Configuration card* — "Configuration / Manage engine preferences"; menu **General · AI Models (badge = configured count) · Fonts · Privacy**; *Local runtime card* (replaces Ollama meters in v1): server status, **RAM** used, **Cache** size, **Purge cache** (secondary). *Storage card* (replaces the FERPA claim): "Your documents, templates and keys stay on this computer" + path.
- **Right (9 cols):**
  - *Title card:* "AI Models & Inference Settings"; description "Connect your own API keys. Choose the model Templix uses for AI Assist."; right pill: **"Bring your own key"** (neutral).
  - *Info box (`brand-tint`, info icon):* title **"Where your data goes"**, body from §9 `settings.dataBoundary`.
  - *Primary Active Engine* card: blue 2-px border, header strip text "PRIMARY ACTIVE ENGINE" + right "{n} ms"; shows the selected provider's configuration (same fields as provider cards) with **Test connection** and **Active Engine** (checked pill) buttons. If none configured: dashed card "Add a provider below to get started".
  - *Provider cards* (OpenAI, Anthropic, Google (Gemini), **OpenAI-compatible endpoint**, Ollama / Local): header row (icon tile, name, "Cloud API" tag, status tag), description, **API key** field (password input; eye icon only while a new key is being typed; helper "Stored in your operating system's keychain on this computer"), **Model** select (searchable; from provider list; "Enter model id manually"), for compatible: **Base URL** field + validation message; helper row (e.g. "Recommended for…" removed unless data-driven); actions: **Test connection**, **Save key / Update key**, **Remove key**; usage line "This period: 18.2k tokens · est. $0.14" from ledger. *Ollama card:* disabled, tag **"Coming soon"**, text "Run models on your own computer. Coming in a later release."
  - *Sticky save bar:* shield icon + "API keys are stored in your operating system's keychain and never synced"; **Revert changes** (ghost) + **Save Settings** (primary, check icon); disabled until dirty.
- **Fonts section:** table of resolved/installed fonts (family, style, source, used-by count, licence note), **Upload font** (dropzone), "Missing fonts" list with **Map…** / **Upload**; optional "Download from Google Fonts" with consent.
- **Privacy section:** (a) plain-language "What is stored and where" list; (b) **Data-flow ledger** table (time, provider, model, document, what was sent, tokens) with filter + **Export CSV**; (c) consent policy radio (*Ask every time per document* / *Remember per document*); (d) **Delete all data** (danger).
- **General section:** name, team, organisation label, kind defaults, units, filename pattern, spellcheck language; read-only data folder path; note "Light theme only".

### 8.7 Screens and dialogs not mocked (design with the same tokens)

| Item | Spec |
|---|---|
| **Templates page** `/templates` | App shell; header + search + filter chips + grid/table toggle; same TemplateCard; bulk select (P2). |
| **Documents page** `/documents` | Table (title, template, status chip, updated, mode, actions) + filters (All, Drafts, Completed); row opens last mode. |
| **Consent dialog** | Title "Send content to {Provider}?"; body lists exactly what will be sent ("The text of 3 fields (≈ 420 words)" / "Images of 2 pages"), model name, link "See what was sent before"; checkbox "Remember for this document"; buttons **Cancel** / **Send & continue**. Never pre-checked. |
| **Export dialog** | Summary of blockers/warnings with jump links; options (PDF/PNG, dpi); **Export anyway** only when errors exist (secondary danger) ; progress state; result with **Download** and file size. |
| **Onboarding** (first run) | 3 compact steps in a dialog: (1) What Templix does (2) Optional: add an API key (3) Try the sample or upload. Skippable. |
| **Shortcuts dialog** | Two-column list generated from the registry. |
| **About dialog** | Name, version, licence (AGPL-3.0), link to third-party notices. |
| **Notifications popover** | List of job events with status icons and links. |

## 9. Copy deck (exact strings, i18n keys)

State-driven privacy copy (D-012). `{P}` = provider display name.

| Key | Condition | String |
|---|---|---|
| `badge.local` | always | `LOCAL APP` (tooltip: "Templix runs on this computer. Your files, templates and keys are stored here.") |
| `privacy.card.none` | no provider | **Everything stays on this device** — "Templix hasn't been connected to any AI service. Analysis, editing and export all run on this computer." |
| `privacy.card.provider` | provider configured | **You're in control of what is shared** — "Analysis, manual editing and export run on this computer. If you use AI Assist, the text of the section you're working on is sent to {P}. Templix asks before the first send and keeps a log you can review." |
| `privacy.mode.manual` | manual mode | "Manual Edit runs entirely on this computer. Nothing is sent anywhere." |
| `privacy.mode.ai` | AI mode | "AI Assist sends the text of the section you're working on — not your whole document — to {P}. Your API key stays in this computer's keychain." |
| `privacy.vlm` | VLM labeling consent | "To label this document's layout, Templix will send images of {n} pages to {P} ({model})." |
| `indicator.none` | manual/native | "No data leaves this device" |
| `indicator.cloud` | AI w/ cloud | "Sends text to {P}" |
| `settings.dataBoundary` | always | "Templix stores your documents, templates and keys on this computer. Reading your reference files, editing and exporting happen here. When you use a cloud model, the text you ask it to work on is sent to that provider under their terms. Local models (such as Ollama) are planned for a later release." |
| `settings.keyNote` | always | "API keys are stored in your operating system's keychain and never synced." |
| `settings.ollama` | v1 | "Run models on your own computer. Coming in a later release." |
| `home.engine.none` | no provider | "No AI engine connected. Add an API key to use AI Assist." |
| `ai.protection` | AI editor | "AI can change content only. Fonts, sizes, spacing and locked layers can't be edited." |
| `ai.fit.ok` | computed ok | "All proposed text fits your template's limits without overflow." |
| `locked.tooltip` | locked layer | "Locked by template" |
| `fidelity.tooltip` | fidelity chip | "How closely Templix's reconstruction matches your original file (higher is better)." |

**Forbidden phrases** (lint list, NFR-PRIV-04): "100% on-device", "zero cloud", "no network calls" (when
cloud AI is configured), "FERPA", "GDPR compliant", "military-grade", "pixel-perfect" as a fixed claim.

## 10. States catalogue

Every data-bound region defines: **loading** (skeleton with final geometry), **empty** (one sentence + action),
**error** (cause + next step + Retry), **partial** (e.g. ingestion in progress), **no-provider**, **offline**
(banner "Can't reach {P}. You can keep editing manually."). Component tests assert each.

## 11. Voice and terminology

Plain, calm, specific; sentence case; no exclamation marks; no jargon.

| Use | Avoid |
|---|---|
| Template | master, skeleton |
| Layer (analysis screen only) | node, object |
| Field / Section (editors) | slot (except the `Slot` tag in Layers tab with tooltip "A place where new content can go") |
| Locked / Editable | immutable, frozen |
| Proposed changes | diffs, patches |
| API key, model | token (for credentials) |
| Review items | errors (unless blocking) |

## 12. Stitch defects and required corrections

| # | Where | Defect in the mock-up | Required correction |
|---|---|---|---|
| 1 | All | Canvas colour varies (`#F4F3F0`, `#FAF9F6`) | Single `canvas #F3F2EF` (D-019) |
| 2 | Home, Mode, AI, Analysis, Settings | Claims "100% On-Device", "Zero cloud upload", "Local Privacy Lock", "Offline Sandbox", "100% Privacy Guarantee" | State-driven copy (§9); never absolute |
| 3 | Settings | "FERPA / Student Privacy … leave this device" | Removed; replaced by storage card; no compliance claims |
| 4 | Home, Mode, AI, Settings | Local Ollama (Llama 3 8B) shown as default/active engine | Provider-driven; Ollama card disabled "Coming soon" (D-029) |
| 5 | Settings | Outdated model names (`gpt-4o`, `claude-3-5-sonnet-20241022`, `gemini-1.5-pro`) | Dynamic model lists (D-027) |
| 6 | Settings | "Keys encrypted in browser IndexedDB" | OS keyring via server (D-010) |
| 7 | Many | Hard-coded numbers: 92 % confident, 99.4 % pixel-matched, 98 % page, 218 MB RAM, 12 ms, $1.42, 124 MB | All computed (D-023, NFR-FID-07) |
| 8 | Home, Settings | Nav labels wrap ("Models & Local AI", "Help & Privacy") | "Models", "Privacy"; `nowrap` |
| 9 | Analysis, Mode, AI | Text wraps inside bars/chips ("Back to Document Analysis", "Bring your own API key", "Export Template") | Nowrap + ellipsis + min widths; shorten labels |
| 10 | AI | Preview clipped at left/right edge; floating toolbar overlaps page bottom | Default Fit-width; canvas bottom padding 96 px |
| 11 | Manual | Floating toolbar overlaps last content; clipped text at bottom of page card | Same fix; page card scrolls fully |
| 12 | Mode | Footer privacy note truncated at bottom | Page scroll + bottom margin 48 px |
| 13 | AI | Mic icon in composer | Removed (D-020) |
| 14 | Editors | `select-none` on `<body>` blocks text selection/copy in fields | Apply only to chrome (toolbars, handles) |
| 15 | All | Tailwind CDN, Google Fonts CDN, Material Symbols CDN at runtime | Bundled/self-hosted (D-018) |
| 16 | Home | Green switch for engine, blue switches elsewhere | One switch style (brand blue) |
| 17 | Analysis | Overlay legend relies on colour (green/red) | Add dashed style + icon + text in review chips |
| 18 | All | Icon-only buttons lack labels; no focus styles | `aria-label`, tooltips, focus ring (NFR-A11Y) |
| 19 | All | `dark:` variants in markup | Remove entirely |
| 20 | Settings | "Active Engine" pill/"Recommended for Privacy" tags imply local default | Computed tags only |
| 21 | Mode | "Step 2 of 3" undefined | Steps: Analyse → Choose mode → Create & export (stepper reused in editors' top bar as breadcrumb on hover, optional) |
| 22 | Home | Seed data (Sarah Lin, March 2025 Issue, Budget Summary…) | No seed data in production; dev-only fixtures behind a flag |
| 23 | AI | Assistant name "Templix Engine (Llama 3)" | "Templix Assist" + provider/model in the pill |
| 24 | Manual | "Target Accuracy: 99.4% pixel-matched" | "Fidelity {score}" computed from round-trip score with explanatory tooltip |
| 25 | All | Mixed top bars (full nav vs compact) | Intentional: **App shell** (Home, lists, Settings) vs **Workspace shell** (Analysis, Mode, editors); document in `ui` package |

## 13. Accessibility checklist (applies to every screen)

- Landmarks: `header`, `nav`, `main`, `aside`, `footer`; one `h1` per route.
- Tab order follows visual order; canvas overlays and layer tree are keyboard operable (arrow keys move selection in the tree; Enter inspects; `M` toggles move mode; arrows nudge).
- Icon-only controls have `aria-label`; toggles use `aria-pressed`/`role="switch"`.
- Live regions: autosave, counters crossing limits, toasts, job progress (polite), errors (assertive).
- Colour is never the only carrier of meaning (icons/text accompany status colours).
- Contrast verified by script on every token pair; focus ring visible on all backgrounds.
- Reduced motion honoured; zoom to 200 % supported.

## 14. Visual QA procedure (NFR-TEST-04)

Stitch screenshots were captured at different device-scale factors (≈ 1.2× for most screens: a 1128-px
container appears ≈ 1350 px wide in `screen.png`; the Settings export is smaller). Therefore:

1. Render each route at **1333 × 900 CSS px, DPR 1.2** with deterministic fixture data and the same viewport
   for all screens (Settings: 1111 × ~1333 at DPR 1).
2. Compare **landmark geometry**, not raw pixels: the bounding boxes of named regions (`data-qa="top-bar"`,
   `left-rail`, `main`, `right-rail`, `canvas`, `sidebar`, …) must match the Stitch layout within ±8 CSS px
   (positions) and ±4 % (sizes). Region lists per screen live in `e2e/parity/regions.ts`.
3. Produce side-by-side PNGs (`artifacts/parity/<screen>.png`: Stitch | ours | diff) for human review in
   every PR that touches UI; pixel-diff is **informational** (expect differences from real data/fonts).
4. A human sign-off checklist per screen (colours, radii, spacing, type, states, copy corrections from §12).
