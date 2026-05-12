import type { SentimentResult } from "../types/course";

const SENTIMENT_STYLES: Record<string, string> = {
  positive: "bg-green-50 border-green-200 text-green-800",
  "mixed-positive": "bg-teal-50 border-teal-200 text-teal-800",
  mixed: "bg-yellow-50 border-yellow-200 text-yellow-800",
  "mixed-negative": "bg-orange-50 border-orange-200 text-orange-800",
  negative: "bg-red-50 border-red-200 text-red-800",
};

interface Props {
  sentiment: SentimentResult;
}

export default function SentimentSummary({ sentiment }: Props) {
  const style = SENTIMENT_STYLES[sentiment.overall_sentiment ?? ""] ?? "bg-gray-50 border-gray-200 text-gray-800";

  return (
    <div className="space-y-4">
      {sentiment.overall_sentiment && (
        <span className={`inline-block text-xs font-semibold px-3 py-1 rounded-full border ${style}`}>
          {sentiment.overall_sentiment.replace("-", " ")}
        </span>
      )}

      {sentiment.summary && (
        <p className="text-sm text-gray-700 leading-relaxed">{sentiment.summary}</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {sentiment.positive_themes.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-green-700 uppercase tracking-wide mb-2">
              What students like
            </p>
            <ul className="space-y-1">
              {sentiment.positive_themes.map((t) => (
                <li key={t} className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-green-500 shrink-0" />
                  {t}
                </li>
              ))}
            </ul>
          </div>
        )}

        {sentiment.negative_themes.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-red-600 uppercase tracking-wide mb-2">
              Common concerns
            </p>
            <ul className="space-y-1">
              {sentiment.negative_themes.map((t) => (
                <li key={t} className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                  {t}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
