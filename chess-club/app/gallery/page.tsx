import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Gallery",
};

interface GalleryItem {
  id: number;
  title: string;
  description: string;
  date: string;
  category: string;
  placeholder: string; // Color placeholder since we don't have actual images
}

const GALLERY_ITEMS: GalleryItem[] = [
  {
    id: 1,
    title: "Spring Championship 2025",
    description: "Our biggest tournament of the spring semester with over 40 participants.",
    date: "March 2025",
    category: "Tournaments",
    placeholder: "#1a1a2e",
  },
  {
    id: 2,
    title: "CMU vs. Pitt Match",
    description: "Annual intercollegiate match against our cross-town rivals.",
    date: "February 2025",
    category: "Competitions",
    placeholder: "#16213e",
  },
  {
    id: 3,
    title: "Beginner Workshop Series",
    description: "Teaching chess fundamentals to newcomers in our popular workshop series.",
    date: "January 2025",
    category: "Workshops",
    placeholder: "#0f3460",
  },
  {
    id: 4,
    title: "Bughouse Night",
    description: "Teams of two battling it out in fast-paced bughouse chess.",
    date: "December 2024",
    category: "Social",
    placeholder: "#2d1b69",
  },
  {
    id: 5,
    title: "Fall Open Tournament",
    description: "USCF-rated tournament kicking off the fall semester.",
    date: "September 2024",
    category: "Tournaments",
    placeholder: "#1a1a2e",
  },
  {
    id: 6,
    title: "Activities Fair",
    description: "Recruiting new members at the CMU student activities fair.",
    date: "August 2024",
    category: "Community",
    placeholder: "#0f3460",
  },
  {
    id: 7,
    title: "Simultaneous Exhibition",
    description: "Our club president taking on 15 challengers at once.",
    date: "April 2024",
    category: "Special Events",
    placeholder: "#16213e",
  },
  {
    id: 8,
    title: "End-of-Year Banquet",
    description: "Celebrating the year's achievements with food, awards, and casual games.",
    date: "April 2024",
    category: "Social",
    placeholder: "#2d1b69",
  },
  {
    id: 9,
    title: "Pan-American Championship",
    description: "Representing CMU at the intercollegiate championship in Washington, D.C.",
    date: "January 2024",
    category: "Competitions",
    placeholder: "#1a1a2e",
  },
];

const CATEGORIES = [
  "All",
  "Tournaments",
  "Competitions",
  "Workshops",
  "Social",
  "Community",
  "Special Events",
];

export default function GalleryPage() {
  return (
    <>
      {/* Hero */}
      <section className="py-20 md:py-24 hero-pattern">
        <div className="section-container">
          <div className="max-w-3xl">
            <h1 className="text-4xl md:text-5xl font-bold font-display text-text-primary tracking-tight mb-6">
              Gallery
            </h1>
            <p className="text-lg md:text-xl text-text-secondary leading-relaxed">
              Highlights from our tournaments, events, and community gatherings.
            </p>
          </div>
        </div>
      </section>

      {/* Category Pills */}
      <section className="py-6 border-b border-border sticky top-16 bg-white/90 backdrop-blur-md z-40">
        <div className="section-container">
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map((category, index) => (
              <span
                key={category}
                className={`
                  inline-flex items-center px-5 py-2 rounded-pill text-sm font-medium
                  transition-colors duration-150 cursor-pointer
                  ${
                    index === 0
                      ? "bg-chess-dark text-white"
                      : "bg-surface-tertiary text-text-secondary hover:bg-surface-secondary border border-border"
                  }
                `}
              >
                {category}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Gallery Grid */}
      <section className="py-16 md:py-20">
        <div className="section-container">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {GALLERY_ITEMS.map((item) => (
              <div key={item.id} className="card overflow-hidden group cursor-pointer">
                {/* Image placeholder */}
                <div
                  className="aspect-[4/3] relative overflow-hidden"
                  style={{ backgroundColor: item.placeholder }}
                >
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center text-white/80">
                      <span className="text-5xl block mb-2">&#9822;</span>
                      <span className="text-xs font-medium uppercase tracking-wider">
                        {item.category}
                      </span>
                    </div>
                  </div>
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-200" />
                </div>
                {/* Content */}
                <div className="p-5">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-chess-accent uppercase tracking-wider">
                      {item.category}
                    </span>
                    <span className="text-xs text-text-tertiary">{item.date}</span>
                  </div>
                  <h3 className="text-base font-bold font-display text-text-primary mb-1">
                    {item.title}
                  </h3>
                  <p className="text-sm text-text-secondary leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Photo submission CTA */}
      <section className="py-16 md:py-20 bg-surface-secondary">
        <div className="section-container text-center">
          <h2 className="text-2xl font-bold font-display text-text-primary mb-3">
            Have Photos to Share?
          </h2>
          <p className="text-lg text-text-secondary max-w-xl mx-auto mb-6">
            If you have photos from any of our events, we&apos;d love to feature
            them in our gallery.
          </p>
          <a
            href="mailto:chess@andrew.cmu.edu?subject=Gallery%20Photo%20Submission"
            className="btn-primary"
          >
            Submit Photos
          </a>
        </div>
      </section>
    </>
  );
}
