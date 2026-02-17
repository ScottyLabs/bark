import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contact",
};

const CONTACT_INFO = [
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
        <polyline points="22,6 12,13 2,6" />
      </svg>
    ),
    label: "Email",
    value: "chess@andrew.cmu.edu",
    href: "mailto:chess@andrew.cmu.edu",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
        <circle cx="12" cy="10" r="3" />
      </svg>
    ),
    label: "Meeting Location",
    value: "Gates Hillman 4307, CMU",
    href: "https://maps.google.com/?q=Gates+Hillman+Center+Carnegie+Mellon",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    ),
    label: "Regular Meetings",
    value: "Thursdays 7-9 PM, Saturdays 2-5 PM",
    href: undefined,
  },
];

const SOCIAL_LINKS = [
  {
    name: "Instagram",
    handle: "@cmuchess",
    url: "https://instagram.com/cmuchess",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
        <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
        <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
      </svg>
    ),
  },
  {
    name: "Discord",
    handle: "CMU Chess Club",
    url: "#",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03z" />
      </svg>
    ),
  },
  {
    name: "Lichess",
    handle: "CMU Chess Club",
    url: "https://lichess.org/team/cmu-chess-club",
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12.5 2C10 2 9 4 9 4s-1 1-2.5 2S4 9 4 9l4.5 1L7 14l3-1 1 5 2-3 2 3 1-5 3 1-1.5-4L22 9s-1-1.5-2.5-3S16 4 16 4s-1-2-3.5-2z" />
      </svg>
    ),
  },
];

const FAQ = [
  {
    question: "Do I need to know how to play chess to join?",
    answer:
      "Not at all! We welcome complete beginners and offer introductory workshops to teach you the basics. Many of our most active members started with no prior experience.",
  },
  {
    question: "Is there a membership fee?",
    answer:
      "Basic membership is free for all CMU students. Tournament participation may have a small entry fee ($5-$15) to cover USCF rating costs and prizes.",
  },
  {
    question: "Do I need to bring my own chess set?",
    answer:
      "No, we have plenty of sets, boards, and clocks available for all our events. Just show up!",
  },
  {
    question: "How competitive is the club?",
    answer:
      "We have players at all levels, from complete beginners to USCF-rated players above 2000. Our events range from casual play to serious rated tournaments, so there's something for everyone.",
  },
  {
    question: "Can I join mid-semester?",
    answer:
      "Absolutely! New members are welcome at any time. Just drop by any of our regular meetings or events.",
  },
  {
    question: "Do you participate in intercollegiate competitions?",
    answer:
      "Yes! We field teams for intercollegiate matches against other universities and have participated in the Pan-American Intercollegiate Team Chess Championship.",
  },
];

export default function ContactPage() {
  return (
    <>
      {/* Hero */}
      <section className="py-20 md:py-24 hero-pattern">
        <div className="section-container">
          <div className="max-w-3xl">
            <h1 className="text-4xl md:text-5xl font-bold font-display text-text-primary tracking-tight mb-6">
              Get in Touch
            </h1>
            <p className="text-lg md:text-xl text-text-secondary leading-relaxed">
              Interested in joining or have questions? We&apos;d love to hear from
              you. The easiest way to get started is to just show up to one of our
              meetings!
            </p>
          </div>
        </div>
      </section>

      {/* Contact Info + Form */}
      <section className="py-16 md:py-20">
        <div className="section-container">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-12">
            {/* Contact Info */}
            <div className="lg:col-span-2 space-y-8">
              <div>
                <h2 className="text-2xl font-bold font-display text-text-primary mb-6">
                  Contact Info
                </h2>
                <div className="space-y-5">
                  {CONTACT_INFO.map((info) => (
                    <div key={info.label} className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-xl bg-chess-dark/10 flex items-center justify-center flex-shrink-0 text-chess-dark">
                        {info.icon}
                      </div>
                      <div>
                        <p className="text-xs font-bold uppercase tracking-wider text-text-tertiary mb-0.5">
                          {info.label}
                        </p>
                        {info.href ? (
                          <a
                            href={info.href}
                            target={info.href.startsWith("http") ? "_blank" : undefined}
                            rel={info.href.startsWith("http") ? "noopener noreferrer" : undefined}
                            className="text-sm font-medium text-chess-dark hover:underline"
                          >
                            {info.value}
                          </a>
                        ) : (
                          <p className="text-sm font-medium text-text-primary">
                            {info.value}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Social Links */}
              <div>
                <h3 className="text-lg font-bold font-display text-text-primary mb-4">
                  Follow Us
                </h3>
                <div className="space-y-3">
                  {SOCIAL_LINKS.map((social) => (
                    <a
                      key={social.name}
                      href={social.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-3 px-4 py-3 rounded-xl border border-border hover:bg-surface-tertiary transition-colors duration-150 group"
                    >
                      <span className="text-text-secondary group-hover:text-chess-dark transition-colors">
                        {social.icon}
                      </span>
                      <div>
                        <p className="text-sm font-bold text-text-primary">
                          {social.name}
                        </p>
                        <p className="text-xs text-text-tertiary">
                          {social.handle}
                        </p>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            </div>

            {/* Contact Form */}
            <div className="lg:col-span-3">
              <div className="card p-6 md:p-8">
                <h2 className="text-2xl font-bold font-display text-text-primary mb-2">
                  Send Us a Message
                </h2>
                <p className="text-sm text-text-secondary mb-6">
                  Fill out the form below and we&apos;ll get back to you within 48 hours.
                </p>
                <form
                  action="mailto:chess@andrew.cmu.edu"
                  method="POST"
                  encType="text/plain"
                  className="space-y-5"
                >
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                    <div>
                      <label
                        htmlFor="name"
                        className="block text-sm font-medium text-text-primary mb-1.5"
                      >
                        Name
                      </label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        required
                        className="w-full px-4 py-3 rounded-base border border-border bg-white text-text-primary text-sm placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-chess-dark/20 focus:border-chess-dark transition-colors"
                        placeholder="Your name"
                      />
                    </div>
                    <div>
                      <label
                        htmlFor="email"
                        className="block text-sm font-medium text-text-primary mb-1.5"
                      >
                        Email
                      </label>
                      <input
                        type="email"
                        id="email"
                        name="email"
                        required
                        className="w-full px-4 py-3 rounded-base border border-border bg-white text-text-primary text-sm placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-chess-dark/20 focus:border-chess-dark transition-colors"
                        placeholder="you@andrew.cmu.edu"
                      />
                    </div>
                  </div>
                  <div>
                    <label
                      htmlFor="subject"
                      className="block text-sm font-medium text-text-primary mb-1.5"
                    >
                      Subject
                    </label>
                    <select
                      id="subject"
                      name="subject"
                      className="w-full px-4 py-3 rounded-base border border-border bg-white text-text-primary text-sm focus:outline-none focus:ring-2 focus:ring-chess-dark/20 focus:border-chess-dark transition-colors"
                    >
                      <option value="join">I want to join the club</option>
                      <option value="tournament">Tournament inquiry</option>
                      <option value="workshop">Workshop information</option>
                      <option value="collaboration">Collaboration / partnership</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label
                      htmlFor="message"
                      className="block text-sm font-medium text-text-primary mb-1.5"
                    >
                      Message
                    </label>
                    <textarea
                      id="message"
                      name="message"
                      rows={5}
                      required
                      className="w-full px-4 py-3 rounded-base border border-border bg-white text-text-primary text-sm placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-chess-dark/20 focus:border-chess-dark transition-colors resize-y"
                      placeholder="Tell us what you're interested in..."
                    />
                  </div>
                  <button type="submit" className="btn-primary w-full sm:w-auto">
                    Send Message
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 md:py-20 bg-surface-secondary">
        <div className="section-container">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold font-display text-text-primary mb-3">
              Frequently Asked Questions
            </h2>
            <p className="text-lg text-text-secondary">
              Quick answers to common questions about the club.
            </p>
          </div>
          <div className="max-w-3xl mx-auto space-y-4">
            {FAQ.map((item) => (
              <div key={item.question} className="card p-6">
                <h3 className="text-base font-bold font-display text-text-primary mb-2">
                  {item.question}
                </h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {item.answer}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Map / Directions */}
      <section className="py-16 md:py-20">
        <div className="section-container">
          <div className="card p-6 md:p-8 bg-chess-dark text-white text-center">
            <h2 className="text-2xl font-bold font-display mb-3">
              Come Visit Us
            </h2>
            <p className="text-gray-400 mb-2">
              Our primary meeting space is in the Gates Hillman Center, Room 4307.
            </p>
            <p className="text-sm text-gray-500 mb-6">
              5000 Forbes Ave, Pittsburgh, PA 15213
            </p>
            <a
              href="https://maps.google.com/?q=Gates+Hillman+Center+Carnegie+Mellon+University"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-bold text-chess-dark bg-white rounded-pill transition-transform duration-150 hover:scale-105"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                <circle cx="12" cy="10" r="3" />
              </svg>
              Get Directions
            </a>
          </div>
        </div>
      </section>
    </>
  );
}
