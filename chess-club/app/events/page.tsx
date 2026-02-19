import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Events",
};

interface Event {
  id: number;
  date: string;
  day: string;
  month: string;
  title: string;
  time: string;
  location: string;
  type: "tournament" | "casual" | "workshop" | "social";
  description: string;
}

const EVENTS: Event[] = [
  {
    id: 1,
    date: "20",
    day: "Thursday",
    month: "Feb",
    title: "Weekly Blitz Night",
    time: "7:00 PM - 9:00 PM",
    location: "Gates Hillman 4307",
    type: "casual",
    description:
      "Our popular weekly blitz session. 3+2 and 5+0 time controls. Casual and fun atmosphere with snacks provided.",
  },
  {
    id: 2,
    date: "22",
    day: "Saturday",
    month: "Feb",
    title: "Spring Open Tournament",
    time: "10:00 AM - 5:00 PM",
    location: "Cohon University Center, Peter/Wright/McKenna",
    type: "tournament",
    description:
      "USCF-rated 4-round Swiss tournament. Open to all CMU students, faculty, and staff. Registration fee: $10 for members, $15 for non-members.",
  },
  {
    id: 3,
    date: "27",
    day: "Thursday",
    month: "Feb",
    title: "Beginner Workshop: Openings 101",
    time: "6:00 PM - 7:30 PM",
    location: "Gates Hillman 4307",
    type: "workshop",
    description:
      "Learn the fundamental principles of chess openings. Perfect for beginners and intermediate players looking to build a solid foundation.",
  },
  {
    id: 4,
    date: "01",
    day: "Saturday",
    month: "Mar",
    title: "Bughouse & Variants Night",
    time: "7:00 PM - 10:00 PM",
    location: "Cohon University Center, Rangos Ballroom",
    type: "social",
    description:
      "A fun evening of chess variants! Bughouse, crazyhouse, 960, and more. Teams of two. Pizza provided.",
  },
  {
    id: 5,
    date: "06",
    day: "Thursday",
    month: "Mar",
    title: "Workshop: Tactical Patterns",
    time: "6:00 PM - 7:30 PM",
    location: "Gates Hillman 4307",
    type: "workshop",
    description:
      "Master essential tactical motifs: forks, pins, skewers, and discovered attacks. Practice with puzzles and exercises.",
  },
  {
    id: 6,
    date: "08",
    day: "Saturday",
    month: "Mar",
    title: "CMU vs. Pitt Intercollegiate Match",
    time: "12:00 PM - 6:00 PM",
    location: "Cohon University Center",
    type: "tournament",
    description:
      "Annual intercollegiate match against the University of Pittsburgh. 8-board classical format. Come support the team!",
  },
  {
    id: 7,
    date: "15",
    day: "Saturday",
    month: "Mar",
    title: "Simultaneous Exhibition",
    time: "2:00 PM - 5:00 PM",
    location: "Gates Hillman Commons",
    type: "social",
    description:
      "Our top-rated players take on all challengers simultaneously. A great chance to test yourself against stronger opponents.",
  },
  {
    id: 8,
    date: "22",
    day: "Saturday",
    month: "Mar",
    title: "Spring Championship",
    time: "9:00 AM - 6:00 PM",
    location: "Cohon University Center, Peter/Wright/McKenna",
    type: "tournament",
    description:
      "The main event of the semester! 5-round USCF-rated Swiss tournament with trophies and prizes. Open and U1400 sections.",
  },
];

const TYPE_STYLES = {
  tournament: {
    bg: "bg-red-50",
    text: "text-red-700",
    border: "border-red-200",
    label: "Tournament",
  },
  casual: {
    bg: "bg-blue-50",
    text: "text-blue-700",
    border: "border-blue-200",
    label: "Casual Play",
  },
  workshop: {
    bg: "bg-amber-50",
    text: "text-amber-700",
    border: "border-amber-200",
    label: "Workshop",
  },
  social: {
    bg: "bg-emerald-50",
    text: "text-emerald-700",
    border: "border-emerald-200",
    label: "Social",
  },
};

function EventTypeBadge({ type }: { type: Event["type"] }) {
  const style = TYPE_STYLES[type];
  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-pill text-xs font-bold ${style.bg} ${style.text} border ${style.border}`}
    >
      {style.label}
    </span>
  );
}

const RECURRING_EVENTS = [
  {
    title: "Weekly Blitz Night",
    schedule: "Every Thursday, 7:00 - 9:00 PM",
    location: "Gates Hillman 4307",
    description: "Drop-in blitz chess with various time controls. All welcome.",
  },
  {
    title: "Saturday Open Play",
    schedule: "Every Saturday, 2:00 - 5:00 PM",
    location: "Cohon University Center",
    description: "Casual longer games, analysis, and hanging out.",
  },
  {
    title: "Online Arena",
    schedule: "Every Sunday, 8:00 PM",
    location: "Lichess.org (CMU Chess Club team)",
    description: "Weekly online arena tournament. 3+0 blitz format.",
  },
];

export default function EventsPage() {
  return (
    <>
      {/* Hero */}
      <section className="py-20 md:py-24 hero-pattern">
        <div className="section-container">
          <div className="max-w-3xl">
            <h1 className="text-4xl md:text-5xl font-bold font-display text-text-primary tracking-tight mb-6">
              Events
            </h1>
            <p className="text-lg md:text-xl text-text-secondary leading-relaxed">
              From weekly casual games to USCF-rated tournaments, there&apos;s always
              something happening at the CMU Chess Club.
            </p>
          </div>
        </div>
      </section>

      {/* Recurring Events */}
      <section className="py-16 md:py-20 bg-surface-secondary">
        <div className="section-container">
          <h2 className="text-2xl font-bold font-display text-text-primary mb-8">
            Recurring Events
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {RECURRING_EVENTS.map((event) => (
              <div key={event.title} className="card p-6">
                <div className="w-10 h-10 rounded-xl bg-chess-dark/10 flex items-center justify-center mb-4">
                  <span className="text-lg">🔄</span>
                </div>
                <h3 className="text-base font-bold font-display text-text-primary mb-1">
                  {event.title}
                </h3>
                <p className="text-sm font-medium text-chess-accent mb-1">
                  {event.schedule}
                </p>
                <p className="text-xs text-text-tertiary mb-3">
                  {event.location}
                </p>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {event.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Upcoming Events */}
      <section className="py-16 md:py-20">
        <div className="section-container">
          <h2 className="text-2xl font-bold font-display text-text-primary mb-8">
            Spring 2025 Schedule
          </h2>
          <div className="space-y-4">
            {EVENTS.map((event) => (
              <div key={event.id} className="card overflow-hidden">
                <div className="flex flex-col md:flex-row">
                  {/* Date block */}
                  <div className="flex-shrink-0 w-full md:w-28 bg-chess-dark text-white p-4 md:p-6 flex md:flex-col items-center justify-center gap-2 md:gap-0">
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
                      {event.month}
                    </span>
                    <span className="text-3xl md:text-4xl font-bold font-display leading-none">
                      {event.date}
                    </span>
                    <span className="text-xs text-gray-400">{event.day}</span>
                  </div>
                  {/* Content */}
                  <div className="flex-1 p-4 md:p-6">
                    <div className="flex flex-wrap items-center gap-3 mb-2">
                      <h3 className="text-lg font-bold font-display text-text-primary">
                        {event.title}
                      </h3>
                      <EventTypeBadge type={event.type} />
                    </div>
                    <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-text-tertiary mb-3">
                      <span className="flex items-center gap-1">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-text-tertiary">
                          <circle cx="12" cy="12" r="10" />
                          <polyline points="12 6 12 12 16 14" />
                        </svg>
                        {event.time}
                      </span>
                      <span className="flex items-center gap-1">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-text-tertiary">
                          <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                          <circle cx="12" cy="10" r="3" />
                        </svg>
                        {event.location}
                      </span>
                    </div>
                    <p className="text-sm text-text-secondary leading-relaxed">
                      {event.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Calendar CTA */}
      <section className="py-16 md:py-20 bg-surface-secondary">
        <div className="section-container text-center">
          <h2 className="text-2xl font-bold font-display text-text-primary mb-3">
            Never Miss an Event
          </h2>
          <p className="text-lg text-text-secondary max-w-xl mx-auto mb-6">
            Subscribe to our calendar or follow us on social media to stay updated
            on all upcoming events.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <a
              href="mailto:chess@andrew.cmu.edu?subject=Calendar%20Subscribe"
              className="btn-primary"
            >
              Subscribe via Email
            </a>
            <a
              href="https://instagram.com/cmuchess"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-outlined"
            >
              Follow on Instagram
            </a>
          </div>
        </div>
      </section>
    </>
  );
}
