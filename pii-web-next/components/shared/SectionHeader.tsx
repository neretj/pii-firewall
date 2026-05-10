export function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[10px] font-bold uppercase tracking-widest text-muted-fg mb-3 flex items-center gap-2">
      <span className="w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0" />
      {children}
    </p>
  );
}
