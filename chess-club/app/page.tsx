import Link from "next/link";

const FEATURES = [
  {
    icon: "🏆",
    title: "Competitive Play",
    description:
      "Compete in USCF-rated tournaments, intercollegiate championships, and our in-house ladder system.",
  },
  {
    icon: "📚",
    title: "Learn & Improve",
    description:
      "Weekly workshops covering openings, tactics, endgames, and strategy for players of all levels.",
  },
  {
    icon: "🤝",
    title: "Community",
    description:
      "Join a welcoming community of 80+ members who share a passion for the royal game.",
  },
  {
    icon: "🎯",
    title: "All Skill Levels",
    description:
      "Whether you just learned the rules or you're a titled player, there's a place for you here.",
  },
];

const UPCOMING_EVENTS = [
  {
    date: "Feb 20",
    day: "Thu",
    title: "Weekly Blitz Night",
    time: "7:00 PM - 9:00 PM",
    location: "Gates Hillman 4307",
  },
  {
    date: "Feb 22",
    day: "Sat",
    title: "Spring Open Tournament",
    time: "10:00 AM - 5:00 PM",
    location: "Cohon University Center",
  },
  {
    date: "Feb 27",
    day: "Thu",
    title: "Beginner Workshop: Openings 101",
    time: "6:00 PM - 7:30 PM",
    location: "Gates Hillman 4307",
  },
];

const STATS = [
  { value: "80+", label: "Active Members" },
  { value: "20+", label: "Events Per Semester" },
  { value: "15+", label: "Tournament Players" },
  { value: "2005", label: "Founded" },
];

export default function HomePage() {
  return (
    <>
      {/* Hero Section */}
      <section className="hero-pattern py-24 md:py-32">
        <div className="section-container">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-chess-dark/5 rounded-pill text-sm font-medium text-chess-dark mb-6">
              <span>♟</span>
              <span>Carnegie Mellon University</span>
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold font-display text-text-primary tracking-tight leading-tight mb-6">
              Where Strategy
              <br />
              Meets Community
            </h1>
            <p className="text-lg md:text-xl text-text-secondary leading-relaxed mb-10 max-w-2xl">
              The CMU Chess Club is a student organization bringing together chess
              enthusiasts of all levels. From casual games to competitive
              tournaments, we make every move count.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href="/contact" className="btn-primary">
                Join the Club
              </Link>
              <Link href="/events" className="btn-outlined">
                View Events
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="bg-chess-dark py-10">
        <div className="section-container">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {STATS.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-3xl md:text-4xl font-bold font-display text-white mb-1">
                  {stat.value}
                </p>
                <p className="text-sm text-gray-400 font-medium">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 md:py-24">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold font-display text-text-primary mb-4">
              Why Join CMU Chess Club?
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              More than just a club &mdash; we&apos;re a community of thinkers,
              competitors, and friends.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {FEATURES.map((feature) => (
              <div key={feature.title} className="card p-6 text-center">
                <span className="text-4xl mb-4 block" role="img" aria-label={feature.title}>
                  {feature.icon}
                </span>
                <h3 className="text-lg font-bold font-display text-text-primary mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Upcoming Events Preview */}
      <section className="py-20 md:py-24 bg-surface-secondary">
        <div className="section-container">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-10 gap-4">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold font-display text-text-primary mb-2">
                Upcoming Events
              </h2>
              <p className="text-lg text-text-secondary">
                Don&apos;t miss what&apos;s happening next.
              </p>
            </div>
            <Link
              href="/events"
              className="text-sm font-bold text-chess-dark hover:underline"
            >
              View All Events &rarr;
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {UPCOMING_EVENTS.map((event) => (
              <div key={event.title} className="card p-6">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-14 h-14 bg-chess-dark rounded-xl flex flex-col items-center justify-center text-white">
                    <span className="text-xs font-bold uppercase leading-none">
                      {event.day}
                    </span>
                    <span className="text-lg font-bold leading-none mt-0.5">
                      {event.date.split(" ")[1]}
                    </span>
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-base font-bold font-display text-text-primary mb-1">
                      {event.title}
                    </h3>
                    <p className="text-sm text-text-secondary mb-1">
                      {event.time}
                    </p>
                    <p className="text-sm text-text-tertiary">
                      {event.location}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 md:py-24">
        <div className="section-container text-center">
          <h2 className="text-3xl md:text-4xl font-bold font-display text-text-primary mb-4">
            Ready to Make Your Move?
          </h2>
          <p className="text-lg text-text-secondary max-w-xl mx-auto mb-8">
            Join the CMU Chess Club today and be part of a vibrant community of
            chess players on campus.
          </p>
          <Link href="/contact" className="btn-primary">
            Get Involved
          </Link>
        </div>
      </section>
    </>
  );
}
