const TAG_COLORS: Record<string, string> = {
  "exam-heavy": "bg-red-100 text-red-700",
  "assignment-heavy": "bg-orange-100 text-orange-700",
  "coding-heavy": "bg-blue-100 text-blue-700",
  "math-heavy": "bg-indigo-100 text-indigo-700",
  "lab-heavy": "bg-teal-100 text-teal-700",
  "participation-heavy": "bg-green-100 text-green-700",
  "group-work-heavy": "bg-yellow-100 text-yellow-700",
  "technical-interview-relevant": "bg-purple-100 text-purple-700",
};

const DEFAULT_COLOR = "bg-gray-100 text-gray-600";

interface Props {
  tag: string;
}

export default function TagBadge({ tag }: Props) {
  const color = TAG_COLORS[tag] ?? DEFAULT_COLOR;
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${color}`}>
      {tag}
    </span>
  );
}
