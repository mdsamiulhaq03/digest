import { Contents } from "@/components/contents";
import { formatNumber } from "@/components/format";
import type { CsvInsights } from "@/lib/documents";

const HEADINGS = ["Column", "Type", "Empty cells", "Min", "Max", "Mean"];

export function CsvInsightsView({ insights }: { insights: CsvInsights }) {
  return (
    <section aria-labelledby="csv-columns" className="flex min-w-0 flex-col gap-3">
      <h2 id="csv-columns" className="cover-label text-base">
        Column by column
      </h2>
      {/* On a phone each column gets its own contents block, so no figure
          ends up off-screen in a sideways-scrolling table. */}
      <ul className="flex flex-col gap-6 sm:hidden">
        {insights.columns.map((column, index) => (
          <li key={`${index}-${column.name}`} className="section-rule flex flex-col gap-1">
            <h3 className="cover-label text-base normal-case wrap-break-word">{column.name}</h3>
            <Contents
              rows={[
                { label: "Type", figure: column.inferred_type },
                { label: "Empty cells", figure: formatNumber(column.null_count) },
                { label: "Min", figure: optional(column.min) },
                { label: "Max", figure: optional(column.max) },
                { label: "Mean", figure: optional(column.mean) },
              ]}
            />
          </li>
        ))}
      </ul>
      <div className="hidden overflow-x-auto sm:block">
        <table className="data-table">
          <thead>
            <tr>
              {HEADINGS.map((heading, index) => (
                <th key={heading} scope="col" className={index > 1 ? "num" : ""}>
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {insights.columns.map((column, index) => (
              // Index too: a CSV can repeat a header name.
              <tr key={`${index}-${column.name}`}>
                <th scope="row" className="font-semibold">
                  {column.name}
                </th>
                <td className="text-muted">{column.inferred_type}</td>
                <td className="num">{formatNumber(column.null_count)}</td>
                <td className="num">{optional(column.min)}</td>
                <td className="num">{optional(column.max)}</td>
                <td className="num">{optional(column.mean)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-sm text-muted">
        Min, max and mean are only worked out for numeric columns.
      </p>
    </section>
  );
}

function optional(value: number | null): string {
  return value === null ? "–" : formatNumber(value);
}
