import { useState } from "react";
import type { ReviewOut } from "../types/review";
import { API_BASE } from "../api/courses";

interface Props {
  reviews: ReviewOut[];
  courseId: number;
  onFlag: (reviewId: number) => void;
}

const SHOWN_INITIALLY = 3;

function RatingDot({ value }: { value: number | null | undefined }) {
  if (!value) return null;
  const color =
    value >= 8 ? "bg-red-400" : value >= 5 ? "bg-orange-400" : "bg-green-400";
  return (
    <span className={`inline-block w-2 h-2 rounded-full ${color} mr-1`} />
  );
}

function ReviewCard({ review, onFlag }: { review: ReviewOut; onFlag: () => void }) {
  const [flagged, setFlagged] = useState(false);

  const handleFlag = () => {
    setFlagged(true);
    onFlag();
  };

  const date = new Date(review.created_at).toLocaleDateString("en-CA", {
    year: "numeric",
    month: "short",
  });

  return (
    <div className="border border-gray-200 rounded-xl p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          {review.term_taken && (
            <span className="text-xs font-semibold text-western-purple bg-purple-50 border border-purple-200 px-2 py-0.5 rounded-full">
              {review.term_taken}
            </span>
          )}
          {review.professor_name && (
            <span className="ml-2 text-xs text-gray-500">{review.professor_name}</span>
          )}
        </div>
        <span className="text-xs text-gray-400 shrink-0">{date}</span>
      </div>

      {/* Ratings row */}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
        {[
          { label: "Difficulty", val: review.difficulty_rating },
          { label: "Workload", val: review.workload_rating },
          { label: "Organization", val: review.organization_rating },
          { label: "Fairness", val: review.assessment_fairness_rating },
          { label: "Usefulness", val: review.usefulness_rating },
        ].map(({ label, val }) =>
          val != null ? (
            <span key={label} className="flex items-center">
              <RatingDot value={val} />
              {label}: <span className="font-semibold ml-0.5">{val}/10</span>
            </span>
          ) : null
        )}
        {review.hours_per_week != null && (
          <span className="flex items-center">
            ⏱ {review.hours_per_week} hrs/week
          </span>
        )}
      </div>

      {/* Review text */}
      {review.review_text && (
        <p className="text-sm text-gray-700 leading-relaxed">{review.review_text}</p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-1">
        {review.would_recommend !== null && review.would_recommend !== undefined ? (
          <span className={`text-xs font-medium ${review.would_recommend ? "text-green-600" : "text-red-500"}`}>
            {review.would_recommend ? "✓ Would recommend" : "✗ Would not recommend"}
          </span>
        ) : <span />}
        {!flagged ? (
          <button
            onClick={handleFlag}
            className="text-xs text-gray-400 hover:text-red-500 transition"
          >
            Report
          </button>
        ) : (
          <span className="text-xs text-gray-400">Reported</span>
        )}
      </div>
    </div>
  );
}

export default function ReviewsList({ reviews, courseId, onFlag }: Props) {
  const [showAll, setShowAll] = useState(false);

  if (!reviews.length) {
    return (
      <p className="text-sm text-gray-500">
        No reviews yet. Be the first to share your experience.
      </p>
    );
  }

  const visible = showAll ? reviews : reviews.slice(0, SHOWN_INITIALLY);

  const handleFlag = async (reviewId: number) => {
    await fetch(`${API_BASE}/courses/${courseId}/reviews/${reviewId}/flag`, {
      method: "POST",
    }).catch(() => {});
    onFlag(reviewId);
  };

  return (
    <div className="space-y-3">
      {visible.map((r) => (
        <ReviewCard key={r.id} review={r} onFlag={() => handleFlag(r.id)} />
      ))}
      {reviews.length > SHOWN_INITIALLY && (
        <button
          onClick={() => setShowAll((v) => !v)}
          className="text-sm text-western-purple font-medium hover:underline"
        >
          {showAll
            ? "Show fewer reviews"
            : `Show all ${reviews.length} reviews`}
        </button>
      )}
    </div>
  );
}
