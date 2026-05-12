import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { GradingComponent } from "../types/course";

const COLORS = ["#4F2683", "#807F44", "#6366f1", "#06b6d4", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"];

interface Props {
  components: GradingComponent[];
}

export default function GradingBreakdown({ components }: Props) {
  if (!components.length) {
    return <p className="text-sm text-gray-500">No grading data available yet.</p>;
  }

  const data = components.map((c) => ({
    name: c.component_name,
    value: Number(c.weight),
  }));

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200">
              <th className="text-left py-2 font-semibold text-gray-600">Component</th>
              <th className="text-right py-2 font-semibold text-gray-600">Weight</th>
              <th className="text-left py-2 pl-4 font-semibold text-gray-600 w-1/2">Distribution</th>
            </tr>
          </thead>
          <tbody>
            {components.map((c, i) => (
              <tr key={c.id} className="border-b border-gray-100 last:border-0">
                <td className="py-2.5 font-medium">{c.component_name}</td>
                <td className="py-2.5 text-right font-semibold">{c.weight}%</td>
                <td className="py-2.5 pl-4">
                  <div className="bg-gray-100 rounded-full h-2 w-full">
                    <div
                      className="h-2 rounded-full"
                      style={{
                        width: `${c.weight}%`,
                        backgroundColor: COLORS[i % COLORS.length],
                      }}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" innerRadius={50} outerRadius={85} paddingAngle={3} dataKey="value">
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(v: number) => `${v}%`} />
            <Legend wrapperStyle={{ fontSize: 12 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
