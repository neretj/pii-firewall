export function MetricCard({ 
  label, 
  value, 
  sub 
}: { 
  label: string; 
  value: number | string; 
  sub?: string 
}) {
  return (
    <div className="rounded-lg border bg-card p-3">
      <p className="text-[11px] text-muted-fg font-medium mb-1">{label}</p>
      <p className="text-2xl font-bold font-mono leading-none">{value}</p>
      {sub && <p className="text-[10px] text-primary font-semibold mt-1">{sub}</p>}
    </div>
  );
}
