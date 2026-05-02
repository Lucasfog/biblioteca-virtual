"use client";

import { useEffect, useState } from "react";
import { Users, Book, FileText, AlertCircle, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { format, subDays, parseISO } from "date-fns";

interface DashboardStats {
  users: number | null;
  books: number | null;
  activeLoans: number | null;
  overdueLoans: number | null;
}

interface Loan {
  id: string;
  due_at: string;
  status: string;
}

interface ChartDay {
  day: string;
  loans: number;
}

const NEON = "#36F4A4";
const DESTRUCTIVE = "#EF4444";

function buildDailyData(loans: Loan[]): ChartDay[] {
  const counts: Record<string, number> = {};
  for (let i = 6; i >= 0; i--) {
    const label = format(subDays(new Date(), i), "MMM d");
    counts[label] = 0;
  }
  for (const loan of loans) {
    try {
      const label = format(parseISO(loan.due_at), "MMM d");
      if (label in counts) counts[label]++;
    } catch (_) {}
  }
  return Object.entries(counts).map(([day, loans]) => ({ day, loans }));
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border border-border bg-popover p-3 text-sm shadow-lg">
        <p className="font-medium">{label}</p>
        <p className="text-[#36F4A4]">{payload[0].value} loans due</p>
      </div>
    );
  }
  return null;
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    users: null,
    books: null,
    activeLoans: null,
    overdueLoans: null,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loanChartData, setLoanChartData] = useState<ChartDay[]>([]);
  const [pieData, setPieData] = useState<{ name: string; value: number }[]>([]);

  useEffect(() => {
    const fetchStats = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [usersRes, booksRes, activeRes, overdueRes] = await Promise.all([
          api.get("/api/v1/users/", { params: { limit: 1 } }),
          api.get("/api/v1/books/", { params: { limit: 1 } }),
          api.get("/api/v1/loans/active", { params: { limit: 100 } }),
          api.get("/api/v1/loans/overdue", { params: { limit: 1 } }),
        ]);

        const activeCount = activeRes.data.total ?? 0;
        const overdueCount = overdueRes.data.total ?? 0;

        setStats({
          users: usersRes.data.total ?? 0,
          books: booksRes.data.total ?? 0,
          activeLoans: activeCount,
          overdueLoans: overdueCount,
        });

        // Build chart from active loans
        const activeLoans: Loan[] = activeRes.data.items || [];
        setLoanChartData(buildDailyData(activeLoans));

        // Pie: active vs overdue
        setPieData([
          { name: "On Time", value: Math.max(0, activeCount - overdueCount) },
          { name: "Overdue", value: overdueCount },
        ]);
      } catch (err: any) {
        console.error("Failed to fetch dashboard stats:", err);
        setError("Unable to load statistics. Please ensure the backend is running.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  const statCards = [
    { label: "Total Users", value: stats.users, icon: Users, sub: "Registered library members" },
    { label: "Total Books", value: stats.books, icon: Book, sub: "Unique titles in catalog" },
    { label: "Active Loans", value: stats.activeLoans, icon: FileText, sub: "Books currently borrowed" },
    { label: "Overdue", value: stats.overdueLoans, icon: AlertTriangle, sub: "Loans past due date", accent: true },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight font-heading">Overview</h2>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Stat Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.label}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">{card.label}</CardTitle>
                <Icon
                  className={`h-4 w-4 ${card.accent ? "text-destructive" : "text-[#36F4A4]"}`}
                />
              </CardHeader>
              <CardContent>
                <div className={`text-3xl font-bold ${card.accent && (stats.overdueLoans ?? 0) > 0 ? "text-destructive" : ""}`}>
                  {isLoading ? (
                    <span className="animate-pulse">—</span>
                  ) : (
                    (card.value ?? 0).toLocaleString()
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-1">{card.sub}</p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Bar Chart: Loans due by day */}
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Active Loans — Due Dates</CardTitle>
            <CardDescription>Distribution of current loans by due date</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="h-[220px] flex items-center justify-center text-muted-foreground text-sm animate-pulse">
                Loading chart...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={loanChartData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                  <XAxis
                    dataKey="day"
                    tick={{ fontSize: 11, fill: "#A1A1AA" }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#A1A1AA" }}
                    axisLine={false}
                    tickLine={false}
                    allowDecimals={false}
                  />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                  <Bar dataKey="loans" fill={NEON} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* Pie Chart: On-time vs Overdue */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Loan Health</CardTitle>
            <CardDescription>On-time vs overdue breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="h-[220px] flex items-center justify-center text-muted-foreground text-sm animate-pulse">
                Loading...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="45%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    <Cell fill={NEON} />
                    <Cell fill={DESTRUCTIVE} />
                  </Pie>
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    formatter={(value) => (
                      <span style={{ color: "#A1A1AA", fontSize: 12 }}>{value}</span>
                    )}
                  />
                  <Tooltip
                    formatter={(value, name) => [value, name]}
                    contentStyle={{
                      background: "#02090A",
                      border: "1px solid #1E2C31",
                      borderRadius: "8px",
                      fontSize: 13,
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
