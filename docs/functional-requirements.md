# Templix — Functional Requirements

Version 0.1 · Companion docs: `system-architecture.md` (§ refs), `design.md` (screen specs),
`non-functional-requirements.md` (`NFR-*`), `decisions.md` (`D-*`).

**How to read.** Each row is one testable requirement.
- **Pri:** `M` Must (v1 is not shippable without it) · `S` Should · `C` Could · `W` Won't (v1).
- **Phase:** `P1` MVP · `P2` · `P3` (see architecture §16).
- Acceptance criteria are written so an automated or manual test can decide pass/fail.
- "The system" = SPA + local server. Mock numbers in the Stitch screens are **examples**; every number the
  UI shows must be computed (D-023).

Glossary: **Template**, **Content**, **Document**, **Slot**, **Section**, **Component**, **Repeater**, **Layer**
(= node) are defined in architecture §5. **Reference** = the uploaded source file.

---

## 1. Home & library (`FR-HOME`) — screen *Desktop Home*

| ID | Requirement | Pri | Ph | Acceptance |
|---|---|---|---|---|
| FR-HOME-01 | Left-rail profile card shows a locally stored display name, team name and a role chip (editable in Settings → General), plus live counts: templates, documents, disk used by `TEMPLIX_HOME`. | M | P1 | Counts equal DB/disk truth after create/delete; editing name in Settings updates the card without reload. |
| FR-HOME-02 | A drop zone accepts drag-and-drop or *Browse files* for PDF (≤ 50 MB). DOCX is accepted only when D-021 is enabled. | M | P1 | A valid PDF starts ingestion; `.png`, >50 MB, encrypted, or corrupt files are rejected with a specific message (see FR-ING-01); keyboard users can open the file dialog with Enter/Space. |
| FR-HOME-03 | *Try sample newsletter PDF* ingests a bundled synthetic sample. | S | P1 | Click → template appears in the library in the same flow as an upload, with no network access. |
| FR-HOME-04 | **Active Templates** grid shows a count and filter chips (All · Newsletters · Reports · Flyers & Posters). Each template has a `kind` tag (inferred, user-editable). Top-bar search filters templates and documents by name/kind. | M | P1 | Selecting a chip filters instantly; count label reflects the filter; search is case-insensitive and debounced ≤ 150 ms. |
| FR-HOME-05 | Template card shows page-1 thumbnail, name (truncated with tooltip), "N layers extracted · P pages · Last used …", a status tag (*Template ready* / *Needs review* / *Processing n %* / *Failed*) and actions: **Create new document** + **Edit** (→ analysis); *Needs review* shows **Review & adjust** + **Layers**. | M | P1 | Status is derived from stored template state; clicking *Create new document* routes to the mode picker with that template; *Failed* shows a retry/delete menu. |
| FR-HOME-06 | Card ⋯ menu: rename, change kind, duplicate, delete (with confirm and a count of dependent documents). | M | P1 | Delete is blocked or cascades only after explicit confirmation text; duplicate creates an independent copy. |
| FR-HOME-07 | **Recent documents** lists the last 5 documents with title, relative time, status chip (*In Progress (AI Assist)* / *In Progress (Manual)* / *Completed*), and a download icon when an export exists. Clicking opens in the last-used mode. | M | P1 | Order is by `updated_at`; *View all* opens the Documents page (FR-SYS-07). |
| FR-HOME-08 | Left-rail shortcuts: **My Drafts** (count), **Imported Brand Assets** (fonts/logos/images library), **Saved Style Rules** (rule presets). | S | P1/P2 | Drafts opens Documents filtered to drafts; the other two are P2 and hidden until implemented (no dead links). |
| FR-HOME-09 | **Workspace Settings** card shows the active AI engine (provider · model) with a status dot and an on/off toggle for AI features. | M | P1 | Toggle off hides AI Assist options app-wide; the dot reflects the last connection test; link goes to Settings → AI Models. |
| FR-HOME-10 | Right-rail **privacy card** is dynamic (D-012): lists what stays on the device and what is sent when AI is used, and names the active provider. | M | P1 | With no provider: "No data leaves this device". With a cloud provider configured: states that AI Assist sends slot text to that provider and links to the ledger. Never shows "100 % on-device". |
| FR-HOME-11 | A static tip card explains AI Assist vs Manual Edit. | C | P1 | Dismissible; dismissal remembered. |
| FR-HOME-12 | First-run empty state when no templates exist (guides to upload or sample). | M | P1 | Library area shows illustration-free empty state with the two CTAs. |
| FR-HOME-13 | Footer links: About, Accessibility statement, Privacy (local), app version. | S | P1 | Each opens a dialog/page; version matches `package.json`/server version. |

## 2. Reference study / ingestion (`FR-ING`)

| ID | Requirement | Pri | Ph | Acceptance |
|---|---|---|---|---|
| FR-ING-01 | Validate uploads: magic bytes `%PDF`, size ≤ 50 MB, pages ≤ 50 (soft limit with override), not encrypted, not corrupt. | M | P1 | Each failure returns a distinct error code and human hint; no partial template is created. |
| FR-ING-02 | Parsing runs in an isolated subprocess with CPU, memory and wall-clock limits; crashes or timeouts fail the job cleanly. | M | P1 | A deliberately malformed fixture does not take down the server; job state = `failed` with reason. |
| FR-ING-03 | Ingestion is a job with stage events (*Reading document → Detecting layers → Inferring styles → Building slots → Scoring fidelity*), percent, and **Cancel**. | M | P1 | Events stream over SSE; cancel stops work within 2 s and removes the partial template. |
| FR-ING-04 | Native extraction captures: text spans (font, size, colour, flags, bbox), images (bbox, dpi, mask), vector paths (fill, stroke, width, dash, opacity, clip), page size/rotation/background. | M | P1 | On the fixture corpus, ≥ 99 % of characters in the PDF text layer appear in some `text` node (Unicode-normalised). |
| FR-ING-05 | Assign roles via heuristics: title, heading1/2, body, byline, caption, quote, header, footer, pagenum, label, rule, box, photo, logo. | M | P1 | On labelled fixtures, role accuracy ≥ 85 % for text nodes (tracked, not blocking release). |
| FR-ING-06 | Compute reading order and group into sections/cards/sidebars. | M | P1 | Each page's nodes belong to exactly one group tree; reading order is total and stable. |
| FR-ING-07 | Detect multi-column body text and represent as `flow` nodes with column count/gap/rule. | M | P1 | A 2-column fixture yields one `flow` node with `columns=2` and correct gap (± 1 pt). |
| FR-ING-08 | Detect running headers/footers/page numbers across pages and mark them shared. | M | P1 | A 2-page fixture's footer is one shared slot bound to both pages' nodes. |
| FR-ING-09 | Infer style tokens: colour palette (ΔE merge), text styles, margins/gutters, baseline grid. | M | P1 | Tokens exist and every text node references a text style; palette ≤ 12 colours after merge on fixtures. |
| FR-ING-10 | Create slots with constraints measured from the original (lines, chars-per-line, maxChars, aspect, minDpi) and `fit` policy. | M | P1 | For each editable text node, replacing text with the original string yields **no** violations; a string 30 % longer raises one. |
| FR-ING-11 | Resolve fonts with the cascade in D-018 and create review items for unresolved/ low-certainty fonts. | M | P1 | Each node has `fontResolution{requested,resolved,source,certainty}`; a PDF using a font we do not have yields a review item. |
| FR-ING-12 | Compute per-node and template **confidence** and the review queue (architecture §6.4). | M | P1 | Banner numbers are derived from stored data; changing a node's confidence in a test changes the banner. |
| FR-ING-13 | Run validators: contrast (WCAG 4.5:1 body / 3:1 large), clipped text, overlapping text, low-dpi images, irregular tables. | S | P1 | Each validator has a fixture that triggers it and one that does not. |
| FR-ING-14 | Compute the **round-trip fidelity score** (SSIM, pixel diff, text IoU) per page and overall, plus a diff heatmap image. | M | P1 | Score reproducible within ±0.002 across runs; heatmap viewable on the analysis screen. |
| FR-ING-15 | Optional **VLM labeling**: send page raster + native box ids to the user's vision model to label roles/groups (consent required). | S | P2 | Without consent nothing is sent; with consent, response is schema-validated and only labels existing nodes. |
| FR-ING-16 | Scanned/no-text-layer pages route through an OCR adapter and are flagged "Reconstructed from image". | S | P2 | A scanned fixture produces editable text nodes and a *Needs review* status. |
| FR-ING-17 | DOCX input normalised to PDF through LibreOffice when installed. | S | P2 | With LibreOffice absent the DOCX option is disabled with an explanation. |
| FR-ING-18 | Devanagari and other complex scripts extract and re-render correctly (shaping, conjuncts, matras). | S | P2 | A Marathi/Hindi fixture round-trips with fidelity ≥ 0.93 and zero missing glyphs. |
| FR-ING-19 | Auto-detect repeated structures and propose components/repeaters. | S | P2 | A fixture with 3 similar article cards yields one component + repeater proposal. |
| FR-ING-20 | Basic table detection (regular grids) producing `table` nodes. | S | P2 | Regular 3×4 table fixture detected; irregular ones flagged read-only. |
| FR-ING-21 | Re-run ingestion with another engine/option and keep the earlier template version. | C | P2 | New run creates `version+1`; old remains restorable. |
| FR-ING-22 | Combine several references into one master template with variants and mined rules. | C | P3 | Out of v1 scope; placeholder only. |

## 3. Template analysis & layer editing (`FR-TPL`) — screen *Document Layer Analysis*

| ID | Requirement | Pri | Ph | Acceptance |
|---|---|---|---|---|
| FR-TPL-01 | Analysis screen header: back to Templates, file chip (name · pages · layers), **Export Template** (package) and **Proceed to Edit** (→ mode picker). Partial results appear while ingestion is still running. | M | P1 | Proceed is enabled when no *blocking* review items remain or the user confirms an override. Export Template is hidden until P3. |
| FR-TPL-02 | Confidence banner: "Analysis N % confident — K items need your review (…)", **Review items** (steps through the queue, focusing each layer) and **Accept all detected** (accepts suggestions ≥ 0.8). | M | P1 | Pressing *Review items* moves selection to the next item and scrolls both canvas and tree; *Accept all* is one undoable transaction. |
| FR-TPL-03 | Pages panel: thumbnails (grid/list toggle), per-page layer count and confidence chip, active highlight, orientation/size readout. | M | P1 | Selecting a thumbnail changes the canvas page; counts match the tree. |
| FR-TPL-04 | Canvas toolbar: zoom −/+/percentage input, **Fit to screen**, **Toggle overlays**, legend (Headings · Text · Review). | M | P1 | Zoom 25–400 %; Fit recomputes on window resize; overlay toggle persists per session. |
| FR-TPL-05 | Overlays draw each layer's bbox colour-coded by role class with a label chip `[Role] Name • WxH (x,y)` on hover/selection; clicking selects the layer and syncs the tree and inspector. | M | P1 | Hit-testing respects z-order; selecting in tree highlights on canvas and vice-versa. |
| FR-TPL-06 | **Layers tab**: filter box, **Collapse all**, tree of pages → groups → layers with: visibility (eye), lock (padlock), **Edit/Fixed toggle** (editable slot vs fixed), *Slot* tag, review rows highlighted with **Inspect**. | M | P1 | Toggle changes `editable`; fixed layers disappear from the editor sidebar; filter matches name/role. |
| FR-TPL-07 | **Selected layer inspector**: role chip, font, size, colour (with swatch), line height/tracking, position/size (x, y, w, h), margin offsets, and a "Format locked" explanation. Numeric fields editable; font/colour pickers (S). | M | P1 | Edits are patches (undoable); changing x/y/w/h moves the overlay immediately and re-renders the page. |
| FR-TPL-08 | Direct manipulation: drag to move, 8 handles to resize, arrow-key nudge (1 pt; Shift 10 pt), snap to margins/columns/other edges with modifier to disable. | M | P1 | Pointer and keyboard paths both work; snapping within 4 px threshold. |
| FR-TPL-09 | Structure edits: change role, merge/split text layers, group/ungroup, delete false positives, mark layer as background. | M | P1 | Each action is a patch and appears in undo history; merge preserves reading order. |
| FR-TPL-10 | **Styles tab**: edit colour tokens and text styles; show "used by N layers"; changing a token updates all dependents. | S | P1 | Updating `ink` colour re-renders every dependent text layer. |
| FR-TPL-11 | **Rules tab** with a red dot when violations exist; list/add/edit/disable rules (kinds in architecture §5.5); rule scope picker. | M | P1 | Adding `maxChars=60` on `role:heading1` immediately flags violating slots. |
| FR-TPL-12 | **Save as Template** persists a new template version and returns to the library; **Open in AI Assist Editor** creates a document and opens AI mode. | M | P1 | Version increments only when changes exist; AI button is disabled with tooltip if no provider is configured. |
| FR-TPL-13 | **Make repeatable**: select a group → create a component with slots; define a repeater (container, direction, gap, min/max). | M | P1 | A user can turn one article card into a repeater and add instances in the editor (FR-MAN-09). |
| FR-TPL-14 | Cross-page text flow (continued story on next page). | C | P3 | Not in v1. |
| FR-TPL-15 | Template version history with diff and restore. | S | P2 | Restoring creates a new version equal to the old. |
| FR-TPL-16 | Add a reference page to an existing template ("Upload additional page"). | C | P2 | Ingested page appended; confidence recomputed. |
| FR-TPL-17 | Fidelity panel: overall + per-page score, band label, **diff heatmap** toggle on canvas. | M | P1 | Heatmap highlights regions where the render differs; score updates after layer edits via *Re-score*. |
| FR-TPL-18 | Split viewer (Stitch DESIGN.md "Document Recreation Split-Viewer"): original PDF (pdf.js) beside the reconstruction with a draggable divider and synchronized scroll/zoom. | S | P1 | Dragging the 4-px bar resizes panes; zoom/scroll stay in sync; keyboard resizable. |

## 4. Creation mode picker (`FR-MODE`) — screen *Choose Creation Mode*

| ID | Requirement | Pri | Ph | Acceptance |
|---|---|---|---|---|
| FR-MODE-01 | Shows step "Step 2 of 3 · Creation Mode", the document chip (name, pages, layers), back link to analysis, and two cards: **AI Assist** (Recommended · Fastest) and **Manual Edit** (Precision · Exact spec). | M | P1 | Back returns to analysis with state preserved. |
| FR-MODE-02 | AI Assist card lists capabilities truthfully: interview, **bring your own API key**, supported providers, fit checking. Ollama/local appears as "Coming soon" (D-029). | M | P1 | No claim of offline AI in v1. |
| FR-MODE-03 | If no provider is configured, AI Assist shows an inline **Add an API key** CTA (to Settings → AI Models) and is not selectable. | M | P1 | After saving a key and returning, the card becomes selectable without reload. |
| FR-MODE-04 | Privacy note below the cards is dynamic (D-012) and links to Settings → Privacy. | M | P1 | Text changes when provider state changes. |
| FR-MODE-05 | Choosing a mode creates (or reopens) the Document and routes to its editor; modes are switchable at any time with content preserved. | M | P1 | Switching Manual ↔ AI keeps unsaved edits and selection. |

## 5. Documents (`FR-DOC`)

| ID | Requirement | Pri | Ph | Acceptance |
|---|---|---|---|---|
| FR-DOC-01 | Create a Document from a Template with a default title ("<Template> — <date>"). | M | P1 | Document pins template version. |
| FR-DOC-02 | Autosave with visible state (*Saving…*/*Auto-saved locally*/*Save failed — retrying*). | M | P1 | Kill the browser tab mid-edit and reopen: ≤ 1 s of work lost; offline server → banner + retry. |
| FR-DOC-03 | **Save Draft** creates a labelled snapshot. | S | P1 | Snapshot appears in history. |
| FR-DOC-04 | Undo/Redo buttons and shortcuts; history survives mode switches within a session. | M | P1 | 100-step history; typing coalesced. |
| FR-DOC-05 | Inline rename; duplicate; delete with confirm. | M | P1 | Duplicate copies content and pins same template version. |
| FR-DOC-06 | **Section History**: per-section list of past values/snapshots with preview and restore. | S | P2 | Restore is a patch and is undoable. |
| FR-DOC-07 | Offer template upgrade when a newer version exists (diff summary). | S | P2 | Upgrade keeps compatible slot values; incompatible ones listed. |
| FR-DOC-08 | **Apply to All Pages**: for slots bound to multiple nodes (shared) edits propagate automatically; for page-local slots the button copies the section's values to equivalent slots on other pages after confirmation. | S | P2 | Shared slot edit changes all bound nodes in one transaction. |
| FR-DOC-09 | Documents page lists all documents with search, status filter, sort. | M | P1 | See FR-SYS-07. |

## 6. Manual Edit mode (`FR-MAN`) — screen *Manual Content Editor*

| ID | Requirement | Pri | Ph | Acceptance |
|---|---|---|---|---|
| FR-MAN-01 | Layout: top bar (back to modes, file chip + status, auto-save pill, undo/redo, **Save Draft**, **Export PDF**, engine status, settings), canvas (dotted background, page card), 360-px right sidebar, footer status bar. | M | P1 | Matches `design.md §8.4` at 1600×1280 within visual-regression tolerance. |
| FR-MAN-02 | Sidebar is generated from sections/slots: header "Edit content · Editing Page N" with **Expand all**; accordion with per-section state (*Complete*, *Active sync*, "N Article(s)"). | M | P1 | A template with 3 sections yields 3 accordion items; state derived from required-slot completeness. |
| FR-MAN-03 | Field types: single-line text, multi-line text, **rich text** (bold, italic, link), date, choice, image slot (thumbnail, filename, size, **Replace image**, **Crop**), link. | M | P1 | Each kind validates against slot constraints; rich text outputs spans (D-028). |
| FR-MAN-04 | Counters: characters (e.g. `64/65`) for constrained text; words (`182 / 200 words — Perfect fit`) for body; colour states ok / near (≥ 90 %) / over. | M | P1 | Counter updates per keystroke; over-limit sets field error state and warning panel entry. |
| FR-MAN-05 | Live preview re-renders as the user types; typing lag p95 ≤ 100 ms (NFR-PERF-02). | M | P1 | Measured by e2e perf test on the fixture. |
| FR-MAN-06 | Two-way selection: click a preview element → select slot, scroll/focus its field; focus a field → blue outline + role tag chip (`[Heading 1 · Lead Story]`) on the element and auto-scroll the canvas. | M | P1 | Works for repeater instances too. |
| FR-MAN-07 | Warnings area: amber items with actions (e.g. **Auto-fit text**, **Jump**), and a green summary "N design rules passed (…)" — all computed by the rules engine. | M | P1 | Making headline 78 chars shows a *Line Length* warning; Auto-fit resolves it or explains why not. |
| FR-MAN-08 | Image replace: file chooser or drop; `cover/contain` per slot; crop dialog with locked aspect (e.g. 16:9); warns when effective dpi < threshold; keeps original in history. | M | P1 | Replacing with a 300×200 image in a 16:9 slot shows crop + dpi warning. |
| FR-MAN-09 | Repeaters: list instances (card with title/author/words), **Add**, **Duplicate**, **Delete**, drag-reorder, min/max enforced; overflow beyond container raises a violation. | M | P1 | Adding the 4th article when max=3 is disabled with tooltip; reflow keeps spacing. |
| FR-MAN-10 | Canvas controls (floating toolbar): zoom −/+/%, **Fit width**, page prev/next with "Page 1 of 2", thumbnails grid toggle, **Grid Guides** (margins, columns, baseline). Toolbar never covers content (canvas gets bottom padding). | M | P1 | Guides align with template tokens. |
| FR-MAN-11 | Page info strip: "Letter Format (8.5 × 11 in)", **Fidelity** chip (template's round-trip score with tooltip, not "pixel-matched" claim), "Bounding-box locks active". | S | P1 | Values from template data. |
| FR-MAN-12 | Locked elements cannot be moved/resized in this mode; attempts show a tooltip "Locked by template". | M | P1 | No drag handles exist in Manual mode. |
| FR-MAN-13 | Paste handling: strip unknown formatting; keep bold/italic/links; collapse excess whitespace; optional "paste as plain". | M | P1 | Pasting from Word keeps bold/italic only. |
| FR-MAN-14 | Native spellcheck enabled in text fields with the document language attribute. | S | P1 | `spellcheck=true`, `lang` set from document settings. |
| FR-MAN-15 | Keyboard shortcuts (Ctrl/⌘ Z, Shift+Z, S, E, +/−, 0, ←/→ for pages, ? for help). | S | P1 | Listed in the shortcuts dialog (FR-SYS-03). |
| FR-MAN-16 | Search/replace across content. | C | P3 | Not in v1. |

## 7. AI Assist mode (`FR-AI`) — screen *AI Assist Editor*

| ID | Requirement | Pri | Ph | Acceptance |
|---|---|---|---|---|
| FR-AI-01 | Three-pane layout: interview/chat (left, 360 px), live preview (center), **Proposed Changes** (right, 360 px); top bar with back, model pill, file chip + saved state, undo/redo, Save Draft, Export PDF. | M | P1 | Matches `design.md §8.5`; preview defaults to **Fit width** so it is never clipped. |
| FR-AI-02 | **Model pill**: shows provider · model, a **privacy badge** (*Sends text to <Provider>* or, later, *On device*), and latency from the last call; opens a menu to switch provider/model mid-session. | M | P1 | Switching affects next call only; the badge updates immediately. |
| FR-AI-03 | If no provider/key: empty state with **Add API key** CTA; Manual mode remains reachable. | M | P1 | No AI call is attempted. |
| FR-AI-04 | **Interview plan** is deterministic (architecture §9.3): header "Step n of N" and progress bar derived from the plan; each step asks Keep / Replace / Skip via quick-reply chips plus free text. | M | P1 | Plan length equals number of sections with editable slots; skipping advances without model calls. |
| FR-AI-05 | **Free-form edit commands** at any time ("shorten the headline", "change the deadline to May 2") are translated into patch ops via the same contract and shown as proposals. | M | P1 | A one-word change produces ≤ 1 op and ≤ 3 k input tokens (NFR-COST-01). |
| FR-AI-06 | Composer: multi-line input, send button, attach (text/markdown/PDF-text/DOCX-text, images as assets); mic is **not shown** (voice is W). | M | P1 | Attachments extracted server-side; images become assets available to image slots. |
| FR-AI-07 | Streaming assistant replies with a visible *Drafting: <slot> · Live Preview Diff* chip; **Stop** cancels the request. | M | P1 | Cancel stops billing-relevant streaming within 1 s of click. |
| FR-AI-08 | **Proposed Changes** panel: header counts ("3 Pending · 1 Accepted"), **Apply all**, **Discard all**; each card shows slot label + page, original (struck through) vs proposal (highlight), `62 / 65 max chars [Safe]`, target ("2 lines exact"), **Reject / Accept**. | M | P1 | Accept applies ops with `origin=ai` (undoable); Reject removes the card; counts update. |
| FR-AI-09 | Image proposals show **Before / After (auto-cropped)** using only assets supplied by the user; the AI never generates or fetches images. | M | P1 | Op referencing an unknown asset id is rejected server-side. |
| FR-AI-10 | Date/structured fields show before → after with strike-through. | S | P1 | Same card pattern as text. |
| FR-AI-11 | Live preview highlights pending changes (toggle **Highlight AI changes**) with an *Active Slot (Diff Highlight)* tag and a green diff tint. | M | P1 | Tint disappears on Accept/Reject. |
| FR-AI-12 | **Fit loop** runs automatically (architecture §9.5); the green banner "All proposed text fits locked font sizes & line limits without overflow" is computed; remaining violations are listed. | M | P1 | Forced overflow is repaired or reported after ≤ 2 repair calls. |
| FR-AI-13 | **Layout Protection** notice states what AI cannot do (edit locked layers, change fonts/geometry). True by contract (§9.6). | M | P1 | Server rejects any op outside `/content/**` in AI mode (test). |
| FR-AI-14 | **Consent dialog** before the first call per provider per document (what is sent, to whom, size estimate); *Remember for this document* option; ledger entry for every call. | M | P1 | No outbound request occurs before consent; ledger rows exist for each call. |
| FR-AI-15 | Session usage readout (input/output tokens, estimated cost if price known). | S | P1 | Matches ledger totals. |
| FR-AI-16 | Conversations persist per document and can be resumed. | S | P1 | Reload restores chat, plan position, pending proposals. |
| FR-AI-17 | Batch draft from one pasted brief across multiple sections. | S | P2 | Produces proposals for ≥ 2 sections from a single message. |
| FR-AI-18 | Editable tone/style guide per template feeding the digest. | S | P2 | Guide text appears in `style_guide` (§9.4). |
| FR-AI-19 | Voice input. | W | — | Not in v1 (D-020). |

## 8. Settings (`FR-SET`) — screen *Settings · AI Models & Inference*

| ID | Requirement | Pri | Ph | Acceptance |
|---|---|---|---|---|
| FR-SET-01 | Settings shell: breadcrumb, left menu **General · AI Models · Fonts · Privacy**, active item with badge (count of configured providers). | M | P1 | Deep-linkable routes `/settings/:section`. |
| FR-SET-02 | **General**: display name, team, kind defaults, units (pt/mm/in), default export filename pattern, language for spellcheck, storage location (read-only), **Light theme only** (no toggle). | M | P1 | Changes persist and reflect on Home. |
| FR-SET-03 | **AI Models** info box (dynamic, D-012) explaining that cloud providers receive selected content and that local models are coming. | M | P1 | Text is copy from `design.md §9`. |
| FR-SET-04 | Provider cards: **OpenAI**, **Anthropic**, **Google (Gemini)**, **OpenAI-compatible (custom endpoint)**, **Ollama / Local** (disabled, "Coming soon"). | M | P1 | Custom card takes base URL + key + model id; validated (T6). |
| FR-SET-05 | Per provider: key field (masked; eye toggle only while typing), model dropdown fed by *list models* with search + manual entry, status tag (*Not configured · Connected · Invalid key · Rate limited · Unreachable*), **Test connection** (shows latency), **Save/Update key**, **Remove key**. | M | P1 | Saved key never returns to the browser; test sends a minimal request; errors map to human messages. |
| FR-SET-06 | Per-provider usage (tokens, estimated spend this period) from the ledger and optional price override. | S | P1 | Numbers equal ledger sums. |
| FR-SET-07 | Primary engine selection ("Active Engine" card) and generation parameters (temperature, max output tokens, timeout). | M | P1 | Persisted; applied to next call. |
| FR-SET-08 | Sticky save bar: dirty detection, **Save Settings**, **Revert Changes**, and the truthful key-storage note ("Keys are stored in your operating system's keychain; never synced"). | M | P1 | Leaving with unsaved changes prompts. |
| FR-SET-09 | **Fonts**: list resolved/installed fonts with source & license note, upload TTF/OTF/WOFF2, map "PDF font name → installed font", optional Google Fonts download (with consent). | M | P1 | Uploaded font immediately affects templates that referenced it (re-render + re-score option). |
| FR-SET-10 | **Privacy**: data-flow ledger table (filter, CSV export), consent reset, per-provider remember policy, **Delete all data**, statement of what is stored where. No compliance/legal claims. | M | P1 | Ledger rows match calls; wipe removes DB+blobs (confirm by typing "DELETE"). |
| FR-SET-11 | Local runtime panel: server status, RAM used, cache size, **Purge cache**. (Ollama allocation widgets hidden until D-029.) | S | P1 | Values from `/status`. |
| FR-SET-12 | Ollama / LM Studio configuration. | W | — | Deferred to P3 (D-029). |

## 9. Rules (`FR-RUL`)

| ID | Requirement | Pri | Ph | Acceptance |
|---|---|---|---|---|
| FR-RUL-01 | Rule kinds: `maxChars`, `maxLines`, `minFontSize`, `allowedFonts`, `minContrast`, `safeMargin`, `requiredOnEveryPage`, `imageMinDpi`, `aspectLock`, `noOverflow`. | M | P1 | Each has unit tests with pass/fail cases. |
| FR-RUL-02 | Rules evaluate on every transaction and on load; results are attached to node/slot ids with severity and message. | M | P1 | Evaluation of a 2-page doc ≤ 50 ms for non-measuring rules. |
| FR-RUL-03 | Fix actions: **Auto-fit text** (shrink within minScale), **Jump to field**, **Shorten with AI** (needs provider). | M/S | P1 | Auto-fit is an undoable transaction. |
| FR-RUL-04 | `error` severity blocks export unless the user confirms an override (logged in the document). | M | P1 | Export button shows blocker count; override requires a click on "Export anyway". |
| FR-RUL-05 | Inferred rules are **proposed** at ingestion and enabled only after user acceptance. | M | P1 | New templates start with proposals marked *Suggested*. |
| FR-RUL-06 | Rule presets reusable across templates ("Saved Style Rules"). | S | P2 | Apply preset to template adds rules with ids remapped. |
| FR-RUL-07 | Mine rules from multiple references. | C | P3 | Out of v1. |

## 10. Export (`FR-EXP`)

| ID | Requirement | Pri | Ph | Acceptance |
|---|---|---|---|---|
| FR-EXP-01 | **Export PDF**: exact page size, selectable vector text, embedded fonts, images at source resolution, backgrounds printed. | M | P1 | `pdffonts` lists embedded fonts; text selectable; page boxes equal template size. |
| FR-EXP-02 | Pre-export dialog summarises errors/warnings with jump links; blockers per FR-RUL-04. | M | P1 | Dialog lists computed violations only. |
| FR-EXP-03 | Export runs as a job with progress; result downloadable; filename from pattern; previous exports listed on the document. | M | P1 | 2-page export ≤ 5 s on reference hardware (NFR-PERF-04). |
| FR-EXP-04 | PNG export per page (DPI selectable). | S | P1 | 144/300 dpi options. |
| FR-EXP-05 | PDF metadata (title, author, creator "Templix") filled from document/settings. | S | P1 | Visible in PDF properties. |
| FR-EXP-06 | Fidelity report export (template vs reference). | C | P2 | JSON/PNG bundle. |
| FR-EXP-07 | DOCX export (best-effort). | W/C | P3 | Not v1. |

## 11. System shell (`FR-SYS`)

| ID | Requirement | Pri | Ph | Acceptance |
|---|---|---|---|---|
| FR-SYS-01 | Top navigation: logo + "LOCAL" chip, search, tabs **Home · Templates · Documents · Models · Privacy**, notifications, profile menu. (Labels shortened vs Stitch to avoid wrapping.) | M | P1 | Active tab has 2-px primary underline; all tabs keyboard reachable. |
| FR-SYS-02 | Footer status bar content is computed: *Engine Ready*, active AI engine/model, RAM, parser version, privacy mode, "No telemetry", version. | M | P1 | Values from `/status`; never static strings for dynamic facts. |
| FR-SYS-03 | Keyboard-shortcuts dialog (`?`). | S | P1 | Lists all registered shortcuts from a single registry. |
| FR-SYS-04 | Notifications center for job completion/failure with deep links. | S | P1 | Bell dot shows unread; list is persisted locally. |
| FR-SYS-05 | Global error boundary + toast system; server errors show `hint`. | M | P1 | Forced failures render friendly messages, not stack traces. |
| FR-SYS-06 | First-run onboarding: optional provider setup → sample or upload. | S | P1 | Skippable; shown once. |
| FR-SYS-07 | **Templates** and **Documents** list pages (search, filters, sort, grid/table toggle) built from the same card components. | M | P1 | Reachable from top nav and "View all". |
| FR-SYS-08 | About dialog: version, licences (AGPL-3.0 notice, third-party list). | S | P1 | Generated from lockfiles at build time. |
| FR-SYS-09 | Responsive down to 1024 px width (collapse rails per `design.md §7`); below that a notice recommends a larger window. | S | P1 | No horizontal scrolling ≥ 1024 px. |

---

## 12. Traceability: screens → requirements

| Stitch screen (folder) | Route | Requirement groups |
|---|---|---|
| `templix_desktop_home` | `/` | FR-HOME-*, FR-SYS-01/02/07 |
| `templix_document_layer_analysis` | `/templates/:id/analysis` | FR-ING-*, FR-TPL-*, FR-RUL-*, FR-SYS-02 |
| `templix_choose_creation_mode` | `/templates/:id/mode` | FR-MODE-* |
| `templix_manual_content_editor` | `/documents/:id/manual` | FR-DOC-*, FR-MAN-*, FR-RUL-*, FR-EXP-* |
| `templix_ai_assist_editor` | `/documents/:id/ai` | FR-DOC-*, FR-AI-*, FR-RUL-*, FR-EXP-* |
| `templix_settings_ai_models` | `/settings/ai-models` (+ general, fonts, privacy) | FR-SET-*, FR-AI-14 |
| *(not mocked)* Templates / Documents lists, consent dialog, export dialog, onboarding, shortcuts, about | `/templates`, `/documents`, dialogs | FR-SYS-03…09, FR-EXP-02, FR-AI-14 |
