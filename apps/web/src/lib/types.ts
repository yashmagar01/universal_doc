import type { ReactNode } from "react";

/** shared UI data shapes used by M0 screens (wire shapes arrive from @templix/doc-schema in M1) */

export interface ProfileInfo {
  name: string;
  role: string;
  team: string;
  orgChip: string;
}

export interface ProviderState {
  /** configured provider id or null */
  id: "openai" | "anthropic" | "google" | "openai_compat" | null;
  label: string;
  connected: boolean;
}

export interface StatusBarContent {
  /** RAM readout — computed from /status in live mode */
  ram: string;
  parser: string;
  privacyMode: string;
  engineRight?: ReactNode;
  user: ProfileInfo;
}

export interface ActivityCount {
  templatesManaged: number;
  documentsCreated: number;
  storageUsed: string;
}
