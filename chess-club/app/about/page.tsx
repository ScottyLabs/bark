import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About",
};

const OFFICERS = [
  {
    name: "Alex Chen",
    role: "President",
    year: "Senior, CS",
    bio: "USCF rated 1950. Passionate about growing chess culture at CMU.",
  },
  {
    name: "Priya Sharma",
    role: "Vice President",
    year: "Junior, Math",
    bio: "Organizes tournaments and leads our beginner workshops.",
  },
  {
    name: "Marcus Williams",
    role: "Tournament Director",
    year: "Senior, ECE",
    bio: "USCF certified TD. Runs our rated events and intercollegiate matches.",
  },
  {
    name: "Sofia Rodriguez",
    role: "Treasurer",
    year: "Sophomore, Business",
    bio: "Manages club finances and coordinates with student government.",
  },
  {
    name: "James Park",
    role: "Social Chair",
    year: "Junior, IS",
    bio: "Plans casual events, game nights, and community outreach.",
  },
  {
    name: "Emma Liu",
    role: "Secretary",
    year: "Sophomore, CS",
    bio: "Handles communications, social media, and meeting notes.",
  },
];

const MILESTONES = [
  {
    year: "2005",
    title: "Club Founded",
    description: "Started by a group of five students who wanted a space to play chess on campus.",
  },
  {
    year: "2010",
    title: "First Tournament Win",
    description: "Won the Pittsburgh Intercollegiate Chess Championship for the first time.",
  },
  {
    year: "2015",
    title: "50 Members Milestone",
    description: "Grew to over 50 active members, expanding to two weekly meeting sessions.",
  },
  {
    year: "2019",
    title: "Pan-American Qualifiers",
    description: "Sent our first team to the Pan-American Intercollegiate Team Chess Championship.",
  },
  {
    year: "2023",
    title: "Online Expansion",
    description: "Launched online tournament series and Discord community reaching 200+ members.",
  },
  {
    year: "2025",
    title: "80+ Active Members",
    description: "Largest active membership in club history with regular rated events.",
  },
];

export default function AboutPage() {
  return (
    <>
      {/* Hero */}
      <section className="py-20 md:py-24 hero-pattern">
        <div className="section-container">
          <div className="max-w-3xl">
            <h1 className="text-4xl md:text-5xl font-bold font-display text-text-primary tracking-tight mb-6">
              About Our Club
            </h1>
            <p className="text-lg md:text-xl text-text-secondary leading-relaxed">
              The CMU Chess Club has been a home for chess enthusiasts at Carnegie
              Mellon since 2005. We foster a supportive environment where players
              of all levels can learn, compete, and connect.
            </p>
          </div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-16 md:py-20 bg-surface-secondary">
        <div className="section-container">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl font-bold font-display text-text-primary mb-6">
                Our Mission
              </h2>
              <div className="space-y-4 text-text-secondary leading-relaxed">
                <p>
                  We believe chess is more than a game &mdash; it&apos;s a tool for
                  developing critical thinking, patience, and strategic mindset. Our
                  mission is to make chess accessible and enjoyable for everyone in
                  the CMU community.
                </p>
                <p>
                  Whether you&apos;re a complete beginner curious about the game or an
                  experienced tournament player looking for competition, we provide
                  the resources, events, and community to support your chess journey.
                </p>
                <p>
                  We host weekly casual play sessions, structured workshops, USCF-rated
                  tournaments, and represent CMU at intercollegiate competitions across
                  the country.
                </p>
              </div>
            </div>
            <div className="card p-8 bg-chess-dark text-white">
              <h3 className="text-xl font-bold font-display mb-6">
                What We Offer
              </h3>
              <ul className="space-y-4">
                {[
                  "Weekly casual play sessions open to all skill levels",
                  "Structured beginner and intermediate workshops",
                  "USCF-rated in-house tournaments each semester",
                  "Intercollegiate team competitions",
                  "Online tournaments and community on Discord & Lichess",
                  "Chess equipment available for all members",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <span className="text-chess-gold mt-0.5 flex-shrink-0">&#10003;</span>
                    <span className="text-sm text-gray-300">{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Officers */}
      <section className="py-16 md:py-20">
        <div className="section-container">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold font-display text-text-primary mb-3">
              Executive Board
            </h2>
            <p className="text-lg text-text-secondary">
              Meet the team that keeps the club running.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {OFFICERS.map((officer) => (
              <div key={officer.name} className="card p-6">
                <div className="w-12 h-12 rounded-full bg-chess-dark flex items-center justify-center text-white font-bold font-display text-lg mb-4">
                  {officer.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </div>
                <h3 className="text-base font-bold font-display text-text-primary">
                  {officer.name}
                </h3>
                <p className="text-sm font-medium text-chess-accent mb-1">
                  {officer.role}
                </p>
                <p className="text-xs text-text-tertiary mb-2">{officer.year}</p>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {officer.bio}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Timeline */}
      <section className="py-16 md:py-20 bg-surface-secondary">
        <div className="section-container">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold font-display text-text-primary mb-3">
              Our History
            </h2>
            <p className="text-lg text-text-secondary">
              Key milestones in the CMU Chess Club story.
            </p>
          </div>
          <div className="max-w-2xl mx-auto">
            <div className="space-y-0">
              {MILESTONES.map((milestone, index) => (
                <div key={milestone.year} className="flex gap-6">
                  {/* Timeline line */}
                  <div className="flex flex-col items-center">
                    <div className="w-3 h-3 rounded-full bg-chess-dark flex-shrink-0 mt-1.5" />
                    {index < MILESTONES.length - 1 && (
                      <div className="w-0.5 bg-border flex-1 my-1" />
                    )}
                  </div>
                  {/* Content */}
                  <div className="pb-8">
                    <span className="text-xs font-bold text-chess-accent uppercase tracking-wider">
                      {milestone.year}
                    </span>
                    <h3 className="text-base font-bold font-display text-text-primary mt-1 mb-1">
                      {milestone.title}
                    </h3>
                    <p className="text-sm text-text-secondary leading-relaxed">
                      {milestone.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
