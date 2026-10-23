# Licensing note — OQ-1 / D-007 (provisional; PyMuPDF is in use)

**Status:** Provisional — recorded per PLAN.md owner condition 2 (2026-10-18). Decision belongs to Yash;
this note lays out what the decision means so it can be confirmed or changed with full information.

## Decision on the table

Use **PyMuPDF** for the native extraction pass and license Templix under **AGPL-3.0** (D-007, OQ-1
default). PyMuPDF is dual-licensed: AGPL-3.0 (free) or a paid commercial licence from Artifex.

## Distribution model

- Templix is a **local-first desktop application**: React SPA + FastAPI bound to `127.0.0.1` + SQLite.
  Users run it on their own machine; there is no Templix-operated server.
- Distributing Templix (source or binaries) under AGPL-3.0 makes the **whole combined work** subject to
  AGPL: recipients get the source, may modify and redistribute, and must pass the same rights on.
  PyMuPDF under AGPL is compatible with that — no conflict while everything stays AGPL.
- **AGPL §13 (network use):** if a *modified* Templix were offered to others as a network service, that
  service must offer those users the source. Plain local use by one user on their own machine is not
  affected; a hosted/multi-tenant Templix (not planned) would trigger it.

## Commercial-use considerations

- **Personal/commercial end use is unrestricted** for users: AGPL does not limit what files they process
  or what they produce with Templix.
- **Relicensing later:** if Templix must become permissive-licensed or proprietary, two options —
  (a) buy Artifex commercial PyMuPDF licences and relicense our own code, or (b) swap the extractor
  behind the `NativeExtractor` port (D-007) to `pypdfium2` (BSD-3-Clause) + `pdfminer.six` (MIT).
  All PyMuPDF imports are confined to `apps/server/templix/ingest/native/`, so (b) stays a bounded change.
- **Obligations on us when distributing:** ship `LICENSE` (AGPL-3.0), `THIRD_PARTY_NOTICES.md`
  (NFR-LIC-01), and the PyMuPDF AGPL notice; keep the licence allow-list in
  `docs/dependencies.md §7` enforced at dependency-add time.

## Unresolved concerns (transparent record)

1. **OQ-1 not yet confirmed by Yash** — AGPL-3.0 remains a provisional default, not a settled decision.
2. **Distribution intent unknown** — whether Templix will ever be offered as a hosted service (AGPL §13
  exposure) or sold commercially is undecided.
3. **PyMuPDF licence cost** — commercial licensing pricing is unexamined; option (b) above is the
  fallback if AGPL is rejected.
4. **`pymupdf` is now used, not just declared.** The adapter in
   `apps/server/templix/ingest/native/pymupdf_native.py` imports it and renders the 150 dpi reference
   raster. The AGPL assumption therefore applies to the current working tree, while OQ-1 remains
   unconfirmed. No distribution should ship until the owner records the decision.
5. **`THIRD_PARTY_NOTICES.md` and `README.md` now exist.** The About dialog (NFR-LIC-01) is still
   missing; it belongs to the M7 release work.

## If OQ-1 is rejected

1. Replace `pymupdf` with `pypdfium2` + `pdfminer.six` in `pyproject.toml` and `docs/dependencies.md §9`.
2. Choose a project licence (MIT/BSD/Apache or closed source) and update `LICENSE`, D-007, NFR-LIC-01.
3. The `NativeExtractor` port keeps the rest of M2 unchanged — only the adapter file swaps.
