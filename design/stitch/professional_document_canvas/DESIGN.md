---
name: Professional Document Canvas
colors:
  surface: '#faf9f6'
  surface-dim: '#dbdad7'
  surface-bright: '#faf9f6'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f3f0'
  surface-container: '#efeeeb'
  surface-container-high: '#e9e8e5'
  surface-container-highest: '#e3e2df'
  on-surface: '#1b1c1a'
  on-surface-variant: '#414752'
  inverse-surface: '#2f312f'
  inverse-on-surface: '#f2f1ee'
  outline: '#727783'
  outline-variant: '#c1c6d4'
  surface-tint: '#005eb5'
  primary: '#004e99'
  on-primary: '#ffffff'
  primary-container: '#0a66c2'
  on-primary-container: '#dbe6ff'
  inverse-primary: '#a8c8ff'
  secondary: '#565f67'
  on-secondary: '#ffffff'
  secondary-container: '#d8e1ea'
  on-secondary-container: '#5b646b'
  tertiary: '#005b31'
  on-tertiary: '#ffffff'
  tertiary-container: '#057642'
  on-tertiary-container: '#9afab9'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#a8c8ff'
  on-primary-fixed: '#001b3d'
  on-primary-fixed-variant: '#00468a'
  secondary-fixed: '#dbe4ec'
  secondary-fixed-dim: '#bec8d0'
  on-secondary-fixed: '#141d23'
  on-secondary-fixed-variant: '#3f484f'
  tertiary-fixed: '#97f7b6'
  tertiary-fixed-dim: '#7cda9b'
  on-tertiary-fixed: '#00210e'
  on-tertiary-fixed-variant: '#00522c'
  background: '#faf9f6'
  on-background: '#1b1c1a'
  surface-variant: '#e3e2df'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.01em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-sm: 1rem
  margin: 1.5rem
  margin-mobile: 0.75rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system delivers a calm, familiar, and highly dependable desktop-first productivity environment. Tailored for office professionals, students, and knowledge workers recreating and digitizing physical documents locally, the aesthetic prioritizes trust, immediate legibility, and zero visual intimidation.

The style is grounded in **Corporate / Modern** desktop web patterns, directly evoking the reassuring familiarity of structured professional platforms like LinkedIn. Key brand principles:

- **Familiarity & Trust:** Uses proven enterprise web mechanics—such as anchored white cards on an oatmeal background, crisp single-pixel delimiters, and clean pill actions—to make complex document recreation feel as straightforward as browsing an activity feed.
- **Local-First Reassurance:** Communicates local persistence, data ownership, and reliability through continuous subtle status indicators, crisp state transitions, and structured feedback.
- **Distraction-Free Focus:** High contrast between text and canvas, balanced secondary metadata, and deliberate absence of loud or non-functional decorative gradients ensure maximum efficiency over extended sessions.

## Colors

The system uses a strict light mode palette engineered for high readability and sustained work sessions:

- **Canvas & Surface:**
  - `Canvas Background`: `#F3F2EF` (Warm, soft light gray that reduces optical glare during long reading sessions).
  - `Card / Surface`: `#FFFFFF` (Crisp, high-contrast surface for document previews, workspace tools, and panels).
  - `Border / Delimiter`: `#E0DFDC` (1px clean mechanical boundary separating cards, dividers, and table headers).
  - `Subtle Divider`: `#EBEAE7` (Muted inner row separator for low-priority structure).

- **Brand & Interactive:**
  - `Primary Interactive`: `#0A66C2` (Professional executive blue; used for primary actions, active indicators, and links).
  - `Primary Hover`: `#004182` (Deep navy blue for clear hover and pressed affordances).
  - `Primary Container / Tint`: `#EBF4FD` (Soft blue wash for active row selections, badges, and contextual message containers).

- **Typography & Content:**
  - `Text Primary`: `#191919` (High-contrast near-black for headings, body text, and input content).
  - `Text Secondary`: `#666666` (Muted charcoal slate for timestamps, helper text, subtitles, and inactive nav icons).
  - `Text Disabled`: `#A0A09E` (Accessible inactive state indicators).

- **Status & Semantics:**
  - `Success`: `#057642` text/border on `#E6F4EA` background (Document sync, complete local export, valid markup).
  - `Warning`: `#B24020` text/border on `#FDF2E9` background (Unsaved local buffers, low storage, format discrepancies).
  - `Error`: `#CC1016` text/border on `#FCE8E6` background (Parsing failures, invalid OCR uploads).

## Typography

The typography scale utilizes **Inter** throughout all tiers to guarantee high tabular precision, exceptional screen rendering, and strict optical balance.

- **Scale & Rhythm:** The foundation is anchored around a 14px base (`body-md`) with 20px line-height, optimized for dense multi-field document interfaces and metadata parsing.
- **Headings:** Headings are restrained, never exceeding 24px (`headline-xl`), reinforcing a pragmatic desktop tool rather than a consumer marketing site. Semibold weights (`600`) establish immediate visual hierarchy without overpowering workspace real estate.
- **Microcopy:** System labels, badges, and top-bar tab descriptions rely on `label-sm` (11px) and `label-md` (12px), maintaining clarity via slight positive letter spacing.

## Layout & Spacing

The layout is built around a standard desktop-centric 3-column feed grid set within a maximum container width of `1128px`:

- **Desktop (1024px and above):**
  - **Left Rail (225px fixed):** Local library status, current document outline, recent templates, storage meter.
  - **Main Canvas (540px flexible min-width to 560px):** Active document recreation workbench, editor feed, source-to-recreation inspection panel.
  - **Right Rail (300px fixed):** Contextual tool recommendations, OCR confidence score, formatting guides, and quick export presets.
  - **Gutter:** Fixed `24px` (`gutter`) between all three columns.
  - **Margin:** Outer boundary margin `24px` centered automatically.

- **Tablet (768px – 1023px):**
  - Collapses to a 2-column layout. The left rail converts into a collapsable off-canvas drawer or top chip selector.
  - Right rail stacks beneath the main canvas, and column gutter reduces to `16px` (`gutter-sm`).

- **Mobile (< 768px):**
  - Single continuous stream. Cards span full width minus `12px` (`margin-mobile`) viewport padding.
  - The top navigation bar pins to the bottom screen edge for single-thumb tool swapping.

- **Padding Cadence:** Internal card padding standardizes to `space-md` (16px) for headers/footers and `space-lg` (24px) for expansive document work areas.

## Elevation & Depth

This design system avoids heavy shadows, instead using subtle, ambient drop shadows paired with crisp 1px borders to establish depth:

- **Flat Canvas:** The background (`#F3F2EF`) forms the zero-elevation base tier.
- **Card Base (Level 1):** Standard modules, document cards, and side panels sit at:
  - `box-shadow: 0px 0px 0px 1px #E0DFDC, 0px 1px 3px rgba(0, 0, 0, 0.08)`
  - The combination of a 1px boundary line and a diffused vertical drop keeps cards crisp and tactile without visual weight.
- **Interactive Hover (Level 2):** When a card or list item is hovered or dragged:
  - `box-shadow: 0px 0px 0px 1px #CDCAC5, 0px 4px 12px rgba(0, 0, 0, 0.12)`
  - Transition duration: `150ms ease-in-out`.
- **Modals, Floating Toolbars, and Dropdowns (Level 3):**
  - `box-shadow: 0px 0px 0px 1px #E0DFDC, 0px 8px 24px rgba(0, 0, 0, 0.15)`
  - Floating element backdrops use a subtle semi-opaque scrim (`rgba(0, 0, 0, 0.6)`).

## Shapes

The design system pairs structured rectilinear containers with soft, human-friendly interaction points:

- **Containers & Panels:** Cards, editor boxes, dialogs, and panels use an `8px` corner radius (`0.5rem`). This retains structural integrity for columnar desktop alignment.
- **Inputs & Dropdowns:** Text boxes and selectors use a consistent `4px` corner radius to evoke standard office productivity tools.
- **Interactive Buttons & Badges:** Primary and secondary buttons, status tags, and chips use a continuous full-pill shape (`9999px` / `rounded-full`), mirroring modern social web interfaces and inviting touch/click engagement.

## Components

### Top Navigation Bar
- Fixed top bar at 56px height with `#FFFFFF` background, bottom border `1px solid #E0DFDC`.
- **Search:** Subtle inset input with `#EDF3F8` background, 34px height, `#666666` placeholder, and search icon prefix.
- **Navigation Tabs:** Grouped vertically (icon centered above `label-sm` text). Inactive state in `#666666`. Active state features `#191919` text, `#0A66C2` icon, and a prominent 2px solid `#0A66C2` bottom border underline running flush with the bottom edge.

### Buttons
- **Primary:** Full pill shape (`rounded-full`), background `#0A66C2`, text `#FFFFFF` (14px Semibold). Padding `6px 16px`. Hover state `#004182`.
- **Secondary / Outlined:** Full pill shape, border `1px solid #0A66C2`, transparent background, text `#0A66C2`. Hover state: background `#EBF4FD` with `1.5px` border width.
- **Tertiary / Ghost:** Full pill shape, transparent background, text `#666666`. Hover state: background `rgba(0, 0, 0, 0.04)`, text `#191919`.
- **Icon Actions:** 36x36px circular ghost button with `#666666` SVG icon, `#0000000A` circle hover fill.

### Cards & Feed Items
- Background `#FFFFFF`, border `1px solid #E0DFDC`, border radius `8px`.
- Card header contains author/source avatar (40x40px rounded-full), document title (`headline-md`), and status microcopy (`body-sm`).
- Top-right corner hosts contextual menu triggers (3 horizontal dots).
- Card footer contains border-top `1px solid #EBEAE7` with 1-click action buttons (e.g., "Duplicate", "Edit Recreation", "Export Local").

### Chips & Badges
- **Status Tags:** Height 24px, pill-shaped, padding `2px 10px`, typography `label-sm`.
  - Synced: Background `#E6F4EA`, text `#057642`.
  - Pending/Local: Background `#EBF4FD`, text `#0A66C2`.
  - Flagged: Background `#FDF2E9`, text `#B24020`.
- **Filter Chips:** Height 32px, pill-shaped, border `1px solid #666666`, background `#FFFFFF`, text `#666666`. Active state: background `#057642` or `#0A66C2` with white text and no border.

### Form Inputs & Checkboxes
- **Input Fields:** Height 36px, background `#FFFFFF`, border `1px solid #666666`, border radius `4px`, padding `0 12px`. Focus state: border `2px solid #0A66C2`, box-shadow `none`.
- **Checkboxes:** 18x18px square with `2px` rounded corners. Inactive: border `1.5px solid #666666`. Active: background `#0A66C2`, checkmark `#FFFFFF`.
- **Radio Buttons:** 18x18px circle. Active: `#0A66C2` ring with 6px concentric `#0A66C2` center dot.

### Document Recreation Split-Viewer
- A dedicated dual-pane card component with an original scanned source image on the left and live editable target markup on the right.
- Separated by an adjustable 4px vertical drag bar (`#E0DFDC`) featuring an active `#0A66C2` indicator line on interaction.