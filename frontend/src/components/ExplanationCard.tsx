interface ExplanationCardProps {
  explanation: string;
  model: string;
  isLoading?: boolean;
}

export default function ExplanationCard({ explanation, model, isLoading }: ExplanationCardProps) {
  if (isLoading) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 animate-pulse">
        <div className="h-4 bg-white/10 rounded w-1/4 mb-4" />
        <div className="space-y-2">
          <div className="h-3 bg-white/10 rounded w-full" />
          <div className="h-3 bg-white/10 rounded w-5/6" />
          <div className="h-3 bg-white/10 rounded w-4/6" />
        </div>
      </div>
    );
  }

  const modelLabel = model === "gemini-2.0-flash" ? "Gemini 2.0 Flash" : model === "rule_based" ? "규칙 기반" : model;

  return (
    <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/5 backdrop-blur-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">🤖</span>
        <h3 className="font-semibold text-slate-200">AI 가격 분석</h3>
        <span className="ml-auto text-xs px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-400 font-medium">
          {modelLabel}
        </span>
      </div>
      <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
        {explanation}
      </div>
    </div>
  );
}
