import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import SearchBar from "../components/SearchBar";
import CourseCard from "../components/CourseCard";
import type { CourseSearchResult } from "../types/course";
import { searchCourses } from "../api/courses";

const POPULAR_COURSES = ["CS 2210", "CS 3305", "CS 3350", "SE 2203", "MATH 2155"];

export default function Home() {
  const [results, setResults] = useState<CourseSearchResult[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const q = searchParams.get("q");
    if (q) {
      searchCourses(q).then((r) => {
        setResults(r);
        setHasSearched(true);
      });
    }
  }, [searchParams]);

  const handleResults = (r: CourseSearchResult[]) => {
    setResults(r);
    setHasSearched(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-western-purple text-white">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <span className="font-bold text-lg tracking-tight">CourseRank AI</span>
          <a href="/compare" className="text-sm text-purple-200 hover:text-white transition">
            Compare Courses →
          </a>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-western-purple text-white pb-16 pt-12">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h1 className="text-4xl font-extrabold tracking-tight mb-4">
            Understand any Western course <br className="hidden sm:block" />
            before you enroll.
          </h1>
          <p className="text-purple-200 text-lg mb-8">
            Grading breakdowns, difficulty scores, and student sentiment — all in one place.
          </p>
          <SearchBar onResults={handleResults} large />
        </div>
      </section>

      <main className="max-w-4xl mx-auto px-6 py-10">
        {/* Search results */}
        {hasSearched && (
          <section className="mb-10">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
              {results.length > 0 ? `${results.length} result${results.length !== 1 ? "s" : ""}` : "No results found"}
            </h2>
            {results.length > 0 ? (
              <div className="space-y-3">
                {results.map((c) => (
                  <CourseCard key={c.id} course={c} />
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-sm">
                Try a different course code or name — e.g. "CS 2210" or "Data Structures".
              </p>
            )}
          </section>
        )}

        {/* Popular courses */}
        {!hasSearched && (
          <section>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
              Popular searches
            </h2>
            <div className="flex flex-wrap gap-2">
              {POPULAR_COURSES.map((code) => (
                <button
                  key={code}
                  onClick={() => searchCourses(code).then((r) => { setResults(r); setHasSearched(true); })}
                  className="px-4 py-2 rounded-full border border-gray-300 text-sm font-medium hover:border-western-purple hover:text-western-purple transition bg-white"
                >
                  {code}
                </button>
              ))}
            </div>

            {/* How it works */}
            <div className="mt-14 grid grid-cols-1 sm:grid-cols-3 gap-6">
              {[
                { icon: "🔍", title: "Search a course", desc: "Enter any Western course code or name to pull up its intelligence report." },
                { icon: "📊", title: "See the full picture", desc: "Grading breakdown, difficulty scores, workload estimates, and student sentiment." },
                { icon: "✍️", title: "Share your experience", desc: "Submit an anonymous review to help future students make better decisions." },
              ].map((item) => (
                <div key={item.title} className="bg-white border border-gray-200 rounded-xl p-6">
                  <div className="text-3xl mb-3">{item.icon}</div>
                  <h3 className="font-semibold text-gray-900 mb-1">{item.title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>

            <p className="mt-10 text-xs text-gray-400 text-center">
              CourseRank AI provides unofficial, student-centered course summaries. Not affiliated with Western University. Not a replacement for official academic advising.
            </p>
          </section>
        )}
      </main>
    </div>
  );
}
