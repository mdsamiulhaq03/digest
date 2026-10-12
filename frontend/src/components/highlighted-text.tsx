// Same word pattern as the API (backend/app/utils/insights.py), so every word
// it counted as a top word is the one marked here.
const WORD_SPLIT = /([A-Za-z']+)/;

// Past this, one element per word costs more than the marks are worth.
const MAX_HIGHLIGHT_CHARS = 200_000;

/** The underline fades with rank, so the most used word is the strongest. */
export function rankStyle(rank: number): React.CSSProperties {
  return { "--rank": rank } as React.CSSProperties;
}

export function HighlightedText({ text, words }: { text: string; words: string[] }) {
  if (words.length === 0 || text.length > MAX_HIGHLIGHT_CHARS) {
    return <>{text}</>;
  }
  const ranks = new Map(words.map((word, rank) => [word, rank]));
  return (
    <>
      {text.split(WORD_SPLIT).map((part, index) => {
        // Odd indexes are the captured words; even ones the text between.
        const rank = index % 2 === 1 ? ranks.get(part.toLowerCase()) : undefined;
        return rank === undefined ? (
          part
        ) : (
          <mark key={index} className="mark-word bg-transparent text-inherit" style={rankStyle(rank)}>
            {part}
          </mark>
        );
      })}
    </>
  );
}
