export type ContentsRow = {
  label: React.ReactNode;
  figure: React.ReactNode;
  tone?: "live" | "failed";
};

/** A digest's contents column: label, dot leaders, figure. Used for a
 * document's counts and for the steps of its job alike. */
export function Contents({
  rows,
  animated = false,
  className = "",
}: {
  rows: ContentsRow[];
  animated?: boolean;
  className?: string;
}) {
  return (
    <ul className={`contents ${className}`}>
      {rows.map((row, index) => (
        <li
          key={index}
          className={row.tone === "live" ? "is-live" : row.tone === "failed" ? "is-failed" : ""}
        >
          <span>{row.label}</span>
          <span
            aria-hidden
            className={`leader ${animated ? "leader-set" : ""}`}
            style={animated ? ({ "--i": index } as React.CSSProperties) : undefined}
          />
          <span className="figure">{row.figure}</span>
        </li>
      ))}
    </ul>
  );
}
