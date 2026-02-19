import Link from "next/link";

const FOOTER_LINKS = [
  {
    heading: "Navigate",
    links: [
      { label: "Home", href: "/" },
      { label: "About", href: "/about" },
      { label: "Events", href: "/events" },
      { label: "Gallery", href: "/gallery" },
      { label: "Contact", href: "/contact" },
    ],
  },
  {
    heading: "Connect",
    links: [
      { label: "Email Us", href: "mailto:chess@andrew.cmu.edu" },
      { label: "Instagram", href: "https://instagram.com/cmuchess" },
      { label: "Discord", href: "#" },
    ],
  },
  {
    heading: "CMU",
    links: [
      { label: "Carnegie Mellon", href: "https://www.cmu.edu" },
      { label: "Student Activities", href: "https://www.cmu.edu/student-activities/" },
      { label: "ScottyLabs", href: "https://scottylabs.org" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="bg-chess-dark text-white">
      {/* Gradient border */}
      <div className="h-1 gradient-border" />

      <div className="section-container py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
          {/* Brand column */}
          <div>
            <h3 className="text-xl font-bold font-display mb-3">CMU Chess Club</h3>
            <p className="text-sm text-gray-400 leading-relaxed">
              Bringing together chess enthusiasts at Carnegie Mellon University since 2005.
              All skill levels welcome.
            </p>
          </div>

          {/* Link columns */}
          {FOOTER_LINKS.map((group) => (
            <div key={group.heading}>
              <h4 className="text-sm font-bold uppercase tracking-wider text-gray-400 mb-4">
                {group.heading}
              </h4>
              <ul className="space-y-2">
                {group.links.map((link) => (
                  <li key={link.label}>
                    {link.href.startsWith("/") ? (
                      <Link
                        href={link.href}
                        className="text-sm text-gray-300 hover:text-white transition-colors duration-150"
                      >
                        {link.label}
                      </Link>
                    ) : (
                      <a
                        href={link.href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-gray-300 hover:text-white transition-colors duration-150"
                      >
                        {link.label}
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="border-t border-gray-700 mt-10 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-500">
            &copy; {new Date().getFullYear()} CMU Chess Club. All rights reserved.
          </p>
          <p className="text-xs text-gray-500">
            Built by{" "}
            <a
              href="https://scottylabs.org"
              target="_blank"
              rel="noopener noreferrer"
              className="text-chess-accent hover:underline font-medium"
            >
              ScottyLabs
            </a>{" "}
            at Carnegie Mellon University
          </p>
        </div>
      </div>
    </footer>
  );
}
