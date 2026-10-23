/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** "1" renders demo fixtures instead of the live API (also forceable with ?fixtures=1) */
  readonly VITE_FIXTURES?: string;
  /** dev/e2e convenience: session token without the one-time URL */
  readonly VITE_TEMPLIX_TOKEN?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
