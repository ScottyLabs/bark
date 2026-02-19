"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/about", label: "About" },
  { href: "/events", label: "Events" },
  { href: "/gallery", label: "Gallery" },
  { href: "/contact", label: "Contact" },
];

function ChessIcon() {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {/* Knight piece silhouette */}
      <path
        d="M10 28h12v-2H10v2zm1-4h10l1-3h-12l1 3zm2-5h6l1-4c0-2-1-3-2-4l1-3h-2l-1 2c-1-1-2-1-3-1v-3h-2v4c-1 1-2 3-2 5l4 4z"
        fill="#1a1a2e"
      />
      <circle cx="14" cy="11" r="1" fill="white" />
    </svg>
  );
}

function HamburgerIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

export default function Navigation() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 backdrop-blur-[40px] bg-white/80 border-b border-border">
      <nav className="max-w-[1400px] mx-auto px-6 md:px-10 flex items-center justify-between h-16">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <ChessIcon />
          <div>
            <span className="text-lg font-bold font-display text-text-primary tracking-tight">
              CMU Chess Club
            </span>
          </div>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`
                  flex items-center gap-1 px-4 py-2 text-base font-medium rounded-base
                  transition-colors duration-150
                  ${
                    isActive
                      ? "bg-chess-dark/5 text-chess-dark border border-border"
                      : "text-text-secondary hover:bg-surface-tertiary hover:text-text-primary border border-transparent"
                  }
                `}
              >
                {link.label}
              </Link>
            );
          })}
        </div>

        {/* Join CTA (desktop) */}
        <div className="hidden md:block">
          <Link
            href="/contact"
            className="inline-flex items-center px-5 py-2 text-sm font-bold text-white bg-chess-dark rounded-pill transition-transform duration-150 hover:scale-105 active:scale-[1.02]"
          >
            Join Us
          </Link>
        </div>

        {/* Mobile menu toggle */}
        <button
          className="md:hidden p-2 text-text-primary"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label={mobileOpen ? "Close menu" : "Open menu"}
        >
          {mobileOpen ? <CloseIcon /> : <HamburgerIcon />}
        </button>
      </nav>

      {/* Mobile Nav */}
      {mobileOpen && (
        <div className="md:hidden border-t border-border bg-white/95 backdrop-blur-md">
          <div className="px-6 py-4 space-y-1">
            {NAV_LINKS.map((link) => {
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setMobileOpen(false)}
                  className={`
                    block px-4 py-3 text-base font-medium rounded-base transition-colors duration-150
                    ${
                      isActive
                        ? "bg-chess-dark/5 text-chess-dark"
                        : "text-text-secondary hover:bg-surface-tertiary"
                    }
                  `}
                >
                  {link.label}
                </Link>
              );
            })}
            <div className="pt-2">
              <Link
                href="/contact"
                onClick={() => setMobileOpen(false)}
                className="block text-center px-5 py-3 text-sm font-bold text-white bg-chess-dark rounded-pill"
              >
                Join Us
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
