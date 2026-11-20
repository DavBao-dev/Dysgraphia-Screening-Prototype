// Small inline icons (stroke style, 24x24). Decorative by default.
import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function Base({ children, className = "h-5 w-5", ...rest }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
      {...rest}
    >
      {children}
    </svg>
  );
}

export function PenIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </Base>
  );
}

export function VideoIcon(p: IconProps) {
  return (
    <Base {...p}>
      <rect x="2" y="6" width="14" height="12" rx="2" />
      <path d="m22 8-6 4 6 4V8Z" />
    </Base>
  );
}

export function ImageIcon(p: IconProps) {
  return (
    <Base {...p}>
      <rect x="3" y="3" width="18" height="18" rx="2" />
      <circle cx="9" cy="9" r="2" />
      <path d="m21 15-3.1-3.1a2 2 0 0 0-2.8 0L6 21" />
    </Base>
  );
}

export function ChartIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="M3 3v18h18" />
      <path d="m7 15 4-4 3 3 5-6" />
    </Base>
  );
}

export function CheckIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="M20 6 9 17l-5-5" />
    </Base>
  );
}

export function CheckCircleIcon(p: IconProps) {
  return (
    <Base {...p}>
      <circle cx="12" cy="12" r="10" />
      <path d="m9 12 2 2 4-4" />
    </Base>
  );
}

export function EyeIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
    </Base>
  );
}

export function InfoIcon(p: IconProps) {
  return (
    <Base {...p}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4M12 8h.01" />
    </Base>
  );
}

export function ArrowRightIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="M5 12h14M13 6l6 6-6 6" />
    </Base>
  );
}

export function ArrowLeftIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="M19 12H5M11 18l-6-6 6-6" />
    </Base>
  );
}

export function PrinterIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="M6 9V2h12v7" />
      <rect x="6" y="14" width="12" height="8" rx="1" />
      <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
    </Base>
  );
}

export function ShieldIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z" />
    </Base>
  );
}

export function UsersIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8" />
    </Base>
  );
}

export function ClockIcon(p: IconProps) {
  return (
    <Base {...p}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 6v6l4 2" />
    </Base>
  );
}

export function UploadIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <path d="M17 8l-5-5-5 5M12 3v12" />
    </Base>
  );
}

export function FileIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
      <path d="M14 2v6h6" />
    </Base>
  );
}

export function ChevronDownIcon(p: IconProps) {
  return (
    <Base {...p}>
      <path d="m6 9 6 6 6-6" />
    </Base>
  );
}
