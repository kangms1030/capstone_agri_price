interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  badge?: string;
  badgeColor?: string;
}

export default function StatCard({ label, value, sub, badge, badgeColor = "bg-emerald-500/20 text-emerald-400" }: StatCardProps) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-slate-400">{label}</p>
        {badge && (
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${badgeColor}`}>
            {badge}
          </span>
        )}
      </div>
      <p className="mt-3 text-3xl font-bold text-white tracking-tight">{value}</p>
      {sub && <p className="mt-1 text-sm text-slate-500">{sub}</p>}
      <div className="absolute -bottom-4 -right-4 h-20 w-20 rounded-full bg-emerald-500/5 blur-2xl" />
    </div>
  );
}
