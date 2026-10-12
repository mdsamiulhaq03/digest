import { formatNumber } from "@/components/format";
import type { CsvInsights } from "@/lib/documents";

const HEADINGS = ["Column", "Type", "Empty cells", "Min", "Max", "Mean"];

export function CsvInsightsView({ insights }: { insights: CsvInsights }) {
  return (
    <section aria-labelledby="csv-summary" className="flex flex-col gap-4">
      <h2 id="csv-summary" className="font-serif text-2xl">
        {formatNumber(insights.row_count)} {insights.row_count === 1 ? "row" : "rows"} across{" "}
        {formatNumber(insights.column_count)}{" "}
        {insights.column_count === 1 ? "column" : "columns"}
      </h2>
      <div className="overflow-x-auto rounded-md border border-rule bg-sheet">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-rule text-graphite">
            <tr>
              {HEADINGS.map((heading, index) => (
                <th
                  key={heading}
                  scope="col"
                  className={`px-4 py-3 font-medium ${index > 1 ? "text-right" : ""}`}
                >
                  {heading}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-rule">
            {insights.columns.map((column, index) => (
              // Index too: a CSV can repeat a header name.
              <tr key={`${index}-${column.name}`}>
                <th scope="row" className="px-4 py-3 font-semibold">
                  {column.name}
                </th>
                <td className="px-4 py-3 text-graphite">{column.inferred_type}</td>
                <td className="px-4 py-3 text-right">{formatNumber(column.null_count)}</td>
                <td className="px-4 py-3 text-right">{optional(column.min)}</td>
                <td className="px-4 py-3 text-right">{optional(column.max)}</td>
                <td className="px-4 py-3 text-right">{optional(column.mean)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-sm text-graphite">
        Min, max and mean are only worked out for numeric columns.
      </p>
    </section>
  );
}

function optional(value: number | null): string {
  return value === null ? "–" : formatNumber(value);
}
