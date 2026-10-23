import { useEffect, useState } from "react";
import { ensureSession, getStatus, type StatusResponse } from "./api";

/** Footer facts from the local server; null until the first response (never fixture data). */
export function useLiveStatus(): StatusResponse | null {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  useEffect(() => {
    let alive = true;
    ensureSession()
      .then(getStatus)
      .then((body) => {
        if (alive) setStatus(body);
      })
      .catch(() => {
        /* the screen's own error state covers an unreachable server */
      });
    return () => {
      alive = false;
    };
  }, []);
  return status;
}
