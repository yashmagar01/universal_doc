import { forwardRef } from "react";
import { cn } from "../cn";

export type IconName =
  | "home"
  | "grid_view"
  | "description"
  | "memory"
  | "shield"
  | "notifications"
  | "search"
  | "layers"
  | "palette"
  | "rule"
  | "visibility"
  | "lock"
  | "lock_open"
  | "expand_more"
  | "chevron_right"
  | "fit_screen"
  | "add"
  | "remove"
  | "undo"
  | "redo"
  | "save"
  | "download"
  | "picture_as_pdf"
  | "auto_awesome"
  | "tune"
  | "check_circle"
  | "verified_user"
  | "warning"
  | "info"
  | "image"
  | "edit"
  | "history"
  | "grid_4x4"
  | "event"
  | "link"
  | "arrow_back"
  | "arrow_forward"
  | "upload_file"
  | "refresh"
  | "settings"
  | "key"
  | "menu"
  | "close"
  | "send"
  | "attach_file"
  | "brightness_1"
  | "list"
  | "lightbulb"
  | "expand_less"
  | "crop_free"
  | "grid_on"
  | "contrast"
  | "folder_outlined"
  | "smart_toy"
  | "doc_edit"
  | "auto_fix_high"
  | "more_vert"
  | "manage_accounts"
  | "visibility_off"
  | "swap_horiz";

export const Icon = forwardRef<
  HTMLSpanElement,
  {
    name: IconName;
    className?: string;
    fill?: boolean;
    /** accessible label; omit for decorative icons */
    label?: string;
  }
>(function Icon({ name, className, fill, label }, ref) {
  return (
    <span
      ref={ref}
      className={cn("material-symbols-outlined select-none text-[20px] leading-none", className)}
      style={fill ? { fontVariationSettings: "'FILL' 1" } : undefined}
      translate="no"
      aria-hidden={label ? undefined : true}
      aria-label={label}
      role={label ? "img" : undefined}
    >
      {name}
    </span>
  );
});
