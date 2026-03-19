"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { ActivityPoint } from "@/lib/types";

interface ActivityChartProps {
  data: ActivityPoint[];
}

export function ActivityChart({ data }: ActivityChartProps) {
  const hasData = data.some((d) => d.matches > 0 || d.saved > 0);

  return (
    <div className="rounded-xl border border-foreground/10 bg-background p-6 shadow-sm">
      <h3 className="mb-4 text-sm font-semibold text-foreground">
        Weekly Activity
      </h3>

      {!hasData ? (
        <div className="flex h-48 items-center justify-center text-sm text-foreground/40">
          No activity data yet. Start matching jobs to see your progress!
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-foreground, #888)" opacity={0.1} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 12, fill: "var(--color-foreground, #888)" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "var(--color-foreground, #888)" }}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #e5e7eb",
                fontSize: "13px",
              }}
            />
            <Legend wrapperStyle={{ fontSize: "12px" }} />
            <Area
              type="monotone"
              dataKey="matches"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.15}
              strokeWidth={2}
              name="Matches"
            />
            <Area
              type="monotone"
              dataKey="saved"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.15}
              strokeWidth={2}
              name="Saved"
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
