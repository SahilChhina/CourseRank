interface Props {
  label: string;
  value: number;
  size?: "sm" | "lg";
}

function scoreColor(value: number): string {
  if (value >= 8) return "text-red-600 bg-red-50 border-red-200";
  if (value >= 6) return "text-orange-600 bg-orange-50 border-orange-200";
  return "text-green-600 bg-green-50 border-green-200";
}

export default function ScorePill({ label, value, size = "sm" }: Props) {
  const color = scoreColor(value);
  return (
    <div className={`border rounded-lg text-center ${size === "lg" ? "px-4 py-3 min-w-[90px]" : "px-2.5 py-1.5 min-w-[70px]"} ${color}`}>
      <p className={`font-bold leading-none ${size === "lg" ? "text-2xl" : "text-base"}`}>
        {value.toFixed(1)}
      </p>
      <p className={`font-medium mt-0.5 ${size === "lg" ? "text-xs" : "text-[10px]"}`}>
        {label}
      </p>
    </div>
  );
}
