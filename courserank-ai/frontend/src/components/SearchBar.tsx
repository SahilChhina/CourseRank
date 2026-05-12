import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { searchCourses } from "../api/courses";
import type { CourseSearchResult } from "../types/course";

interface Props {
  onResults?: (results: CourseSearchResult[]) => void;
  large?: boolean;
}

export default function SearchBar({ onResults, large = false }: Props) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const results = await searchCourses(query.trim());
      if (onResults) {
        onResults(results);
      } else if (results.length === 1) {
        navigate(`/courses/${results[0].id}`);
      } else {
        navigate(`/?q=${encodeURIComponent(query.trim())}`);
      }
    } catch {
      setError("Search failed. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className={`flex gap-2 ${large ? "max-w-2xl mx-auto" : ""}`}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by course code or name, e.g. CS 2210"
          className={`flex-1 border border-gray-300 rounded-lg px-4 focus:outline-none focus:ring-2 focus:ring-western-purple bg-white ${
            large ? "py-4 text-lg" : "py-2 text-sm"
          }`}
        />
        <button
          type="submit"
          disabled={loading}
          className={`bg-western-purple text-white font-semibold rounded-lg px-6 hover:bg-purple-900 transition disabled:opacity-60 ${
            large ? "py-4 text-lg" : "py-2 text-sm"
          }`}
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>
      {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
    </form>
  );
}
