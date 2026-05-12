import type { ReviewOut } from "../types/review";

interface Props {
  reviews: ReviewOut[];
}

const RATING_KEYS: { key: keyof ReviewOut; label: string }[] = [
  { key: "difficulty_rating", label: "Difficulty" },
  { key: "workload_rating", label: "Workload" },
  { key: "organization_rating", label: "Organization" },
  { key: "assessment_fairness_rating", label: "Fairness" },
  { key: "usefulness_rating", label: "Usefulness" },
];

function avg(values: (number | null | undefined)[]): number | null {
  const vals = values.filter((v): v is number => v != null);
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : null;
}

function barColor(value: number) {
  if (value >= 7.5) return "bg-red-400";
  if (value >= 5) return "bg-orange-400";
  return "bg-green-400";
}

export default function ReviewStats({ reviews }: Props) {
  if (!reviews.length) return null;

  const recommend = reviews.filter((r) => r.would_recommend === true).length;
  const recommendPct = Math.round((recommend / reviews.length) * 100);

  const avgHours = avg(reviews.map((r) => r.hours_per_week));

  return (
    <div className="space-y-5">
      {/* Summary row */}
      <div className="flex flex-wrap gap-4">
        <div className="bg-western-purple/5 border border-western-purple/20 rounded-xl px-5 py-3 text-center min-w-[100px]">
          <p className="text-2xl font-extrabold text-western-purple">{reviews.length}</p>
          <p className="text-xs text-gray-500 font-medium mt-0.5">Review{reviews.length !== 1 ? "s" : ""}</p>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-xl px-5 py-3 text-center min-w-[100px]">
          <p className="text-2xl font-extrabold text-green-600">{recommendPct}%</p>
          <p className="text-xs text-gray-500 font-medium mt-0.5">Would Recommend</p>
        </div>
        {avgHours !== null && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl px-5 py-3 text-center min-w-[100px]">
            <p className="text-2xl font-extrabold text-blue-600">{avgHours.toFixed(1)}</p>
            <p className="text-xs text-gray-500 font-medium mt-0.5">Hrs / Week</p>
          </div>
        )}
      </div>

      {/* Rating bars */}
      <div className="space-y-3">
        {RATING_KEYS.map(({ key, label }) => {
          const value = avg(reviews.map((r) => r[key] as number | null));
          if (value === null) return null;
          return (
            <div key={key} className="flex items-center gap-3">
              <p className="text-xs font-medium text-gray-600 w-28 shrink-0">{label}</p>
              <div className="flex-1 bg-gray-100 rounded-full h-2.5">
                <div
                  className={`h-2.5 rounded-full ${barColor(value)} transition-all`}
                  style={{ width: `${(value / 10) * 100}%` }}
                />
              </div>
              <p className="text-xs font-bold text-gray-700 w-8 text-right">{value.toFixed(1)}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
