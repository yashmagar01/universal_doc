import type { ReactNode } from "react";
import { Link } from "react-router";
import { Icon, type IconName } from "./Icon";
import { Tag } from "./Tag";
import { Tooltip } from "./Tooltip";
import { IconButton } from "./IconButton";
import { cn } from "../cn";

export const TOP_NAV = [
  { key: "home", label: "Home", href: "/", icon: "home" as IconName },
  { key: "templates", label: "Templates", href: "/templates", icon: "grid_view" as IconName },
  { key: "documents", label: "Documents", href: "/documents", icon: "description" as IconName },
  { key: "models", label: "Models", href: "/settings/ai-models", icon: "memory" as IconName },
  { key: "privacy", label: "Privacy", href: "/settings/privacy", icon: "shield" as IconName },
] as const;

export type TopNavKey = (typeof TOP_NAV)[number]["key"];

export function Logo() {
  return (
    <span className="flex items-center gap-2 select-none" data-qa="logo">
      <span className="flex size-8 items-center justify-center rounded-(--radius-input) bg-brand text-[20px] leading-none font-semibold text-white">
        <Icon name="layers" />
      </span>
      <span className="text-headline-md">Templix</span>
    </span>
  );
}

export function ProfileChip({ name, role }: { name: string; role: string }) {
  const initials = name
    .split(/\s+/)
    .map((p) => p[0] ?? "")
    .join("")
    .slice(0, 2)
    .toUpperCase();
  return (
    <button
      type="button"
      className="flex items-center gap-2 rounded-pill py-1 pr-1 pl-2 hover:bg-black/4"
      data-qa="profile-chip"
      aria-label={name ? undefined : "Account menu"}
    >
      <span
        aria-hidden
        className="flex size-8 items-center justify-center rounded-full bg-brand text-label-md text-white"
      >
        {initials}
      </span>
      <span className="hidden text-left leading-tight lg:block">
        <span className="block text-label-md text-ink">{name}</span>
        <span className="block text-body-sm text-ink-2">{role}</span>
      </span>
      <Icon name="expand_more" className="text-ink-2" />
    </button>
  );
}

/** App shell top bar (Home, lists, Settings) — design.md §4 */
export function TopBar({
  active,
  query,
  onQueryChange,
  unread = false,
  userName,
  userRole,
  children,
}: {
  active: TopNavKey;
  query: string;
  onQueryChange: (q: string) => void;
  unread?: boolean;
  userName: string;
  userRole: string;
  /** right-side items after nav (page-level actions) */
  children?: ReactNode;
}) {
  return (
    <header data-qa="top-bar" className="sticky top-0 z-40 bg-card shadow-[0_1px_0_var(--color-border)]">
      <div className="mx-auto flex h-14 max-w-[1128px] items-center gap-3 px-6">
        <Logo />
        <Tooltip content="Templix runs on this computer. Your files, templates and keys are stored here.">
          <Tag tone="neutral">LOCAL APP</Tag>
        </Tooltip>
        <div className="relative mx-1 hidden md:block">
          <Icon name="search" className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-ink-2" />
          <input
            type="search"
            value={query}
            onChange={(e) => onQueryChange(e.target.value)}
            aria-label="Search templates, documents, styles"
            placeholder="Search templates, documents, styles…"
            className="h-[34px] w-60 rounded-(--radius-input) bg-search-bg pl-9 text-body-md text-ink placeholder:text-ink-2 focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>
        <nav aria-label="Primary" data-qa="nav-tabs" className="flex h-full flex-1 items-stretch justify-end gap-1">
          {TOP_NAV.map((n) => (
            <Link
              key={n.key}
              to={n.href}
              aria-current={active === n.key ? "page" : undefined}
              className={cn(
                "flex h-full flex-col items-center justify-center gap-0.5 border-b-2 px-3 text-label-sm select-none",
                active === n.key ? "border-brand text-ink" : "border-transparent text-ink-2 hover:text-ink",
              )}
            >
              <Icon name={n.icon} fill={active === n.key} className={active === n.key ? "text-brand" : "text-ink-2"} />
              <span className="whitespace-nowrap">{n.label}</span>
            </Link>
          ))}
        </nav>
        <div className="relative">
          <IconButton icon="notifications" label="Notifications" />
          {unread && <span className="pointer-events-none absolute top-1.5 right-2 size-2 rounded-full bg-brand" aria-hidden />}
        </div>
        {children}
        <ProfileChip name={userName} role={userRole} />
      </div>
    </header>
  );
}

/** Workspace shell top bar (Analysis, Mode, editors) — compact, no app nav */
export function WorkspaceTopBar({
  back,
  file,
  fileMeta,
  status,
  actions,
  userName = "Yash",
  userRole = "Editor",
}: {
  back: ReactNode;
  file: string;
  fileMeta?: ReactNode;
  status?: ReactNode;
  actions?: ReactNode;
  userName?: string;
  userRole?: string;
}) {
  return (
    <header data-qa="workspace-top-bar" className="sticky top-0 z-40 bg-card shadow-[0_1px_0_var(--color-border)]">
      <div className="mx-auto flex h-14 items-center gap-3 px-6">
        <Logo />
        <Tooltip content="Templix runs on this computer. Your files, templates and keys are stored here.">
          <Tag tone="neutral">LOCAL APP</Tag>
        </Tooltip>
        <span className="mx-1 h-6 w-px bg-divider" />
        {back}
        <FilePill name={file} meta={fileMeta} className="min-w-0 flex-1" />
        {status}
        <span className="mx-1 h-6 w-px bg-divider" />
        {actions}
        <ProfileChip name={userName} role={userRole} />
      </div>
    </header>
  );
}

export function FilePill({
  name,
  meta,
  className,
}: {
  name: string;
  meta?: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "flex h-10 items-center gap-2 rounded-(--radius-card) bg-card px-3 shadow-l1",
        className,
      )}
    >
      <Icon name="description" className="shrink-0 text-ink-2" />
      <span className="truncate text-body-md text-ink" title={name}>
        {name}
      </span>
      {meta != null && <span className="shrink-0 text-body-sm whitespace-nowrap text-ink-2">{meta}</span>}
    </span>
  );
}
