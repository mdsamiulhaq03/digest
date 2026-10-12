---
name: Digest
description: Paste text or upload a file and see what it's made of
colors:
  ground: "#f5f7f5"
  surface: "#ffffff"
  ink: "#141a17"
  muted: "#4b5852"
  rule: "#c7d0cb"
  leader: "#87948d"
  band: "#0e5a4a"
  band-deep: "#0a4639"
  on-band: "#f2f7f4"
  on-band-muted: "#b6d3c8"
  viridian: "#0e5a4a"
  live: "#d9a21b"
  on-live: "#141a17"
  fail: "#a8322a"
  fail-wash: "#f7e4e1"
  ground-dark: "#0f1412"
  surface-dark: "#161d1a"
  ink-dark: "#e6ece8"
  muted-dark: "#9fb0a8"
  rule-dark: "#2b3732"
  leader-dark: "#5d6e66"
  band-dark: "#0b3a30"
  band-deep-dark: "#072a22"
  on-band-dark: "#e6f0ec"
  on-band-muted-dark: "#9cc4b6"
  viridian-dark: "#6cc4a8"
  live-dark: "#e0ad2c"
  fail-dark: "#f08a7e"
  fail-wash-dark: "#3a1d1a"
typography:
  display:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "6rem"
    fontWeight: 800
    lineHeight: 0.85
    letterSpacing: "0.005em"
    fontVariation: "'wdth' 72"
  cover:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(4.5rem, 11vw, 9rem)"
    fontWeight: 800
    lineHeight: 0.8
    letterSpacing: "0.005em"
    fontVariation: "'wdth' 72"
  headline:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "3.75rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "0.005em"
    fontVariation: "'wdth' 72"
  title:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 800
    lineHeight: 1.25
    letterSpacing: "0.005em"
    fontVariation: "'wdth' 72"
  label:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    letterSpacing: "0.08em"
    fontVariation: "'wdth' 72"
  body:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    fontFeature: "'tnum' 1"
  reading:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "1.25rem"
    fontWeight: 400
    lineHeight: 1.75
  credit:
    fontFamily: "Source Serif 4, Georgia, serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  corner: "2px"
spacing:
  hair: "0.3rem"
  xs: "0.5rem"
  sm: "0.75rem"
  md: "1.5rem"
  lg: "2rem"
  xl: "3rem"
  gutter: "2rem"
components:
  band:
    backgroundColor: "{colors.band}"
    textColor: "{colors.on-band}"
    padding: "16px 32px"
  button-primary:
    backgroundColor: "{colors.band}"
    textColor: "{colors.on-band}"
    rounded: "{rounded.corner}"
    padding: "10px 20px"
    height: "44px"
  button-primary-hover:
    backgroundColor: "{colors.band-deep}"
    textColor: "{colors.on-band}"
  button-primary-disabled:
    backgroundColor: "{colors.rule}"
    textColor: "{colors.muted}"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.corner}"
    padding: "10px 16px"
    height: "44px"
  button-quiet-hover:
    backgroundColor: "{colors.surface}"
  field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.corner}"
    padding: "10px 12px"
  state-processing:
    backgroundColor: "{colors.live}"
    textColor: "{colors.on-live}"
    typography: "{typography.label}"
    padding: "2px 6px"
  state-ready:
    textColor: "{colors.viridian}"
    typography: "{typography.label}"
  state-failed:
    textColor: "{colors.fail}"
    typography: "{typography.label}"
  notice-error:
    backgroundColor: "{colors.fail-wash}"
    textColor: "{colors.ink}"
    padding: "12px 16px"
---

# Design System: Digest

## Overview

**Creative North Star: "The Pocket Digest"**

Every document comes back condensed, and the app presents it the way a pocket digest presents its contents: a committed viridian cover band across the top, a cool near-white page, near-black ink, condensed capitals for cover lines, and an index of dot-leader lines whose figures all land on one right-aligned tabular column. The same contents line lists what Digest counted and how the document got there (received, queued, picked up, attempt n of 3, analysed), so insight and machinery read in one gesture.

The system is flat, ruled, and typographic. Structure comes from ink rules (a 3px rule opens every section, 1px rules frame the running line and tables) and from type width, never from boxes, cards, or shadows. Colour carries meaning, not decoration: viridian is the house, ochre means "still happening", red means "failed", and nothing else gets a hue. The user's own text is set as a book page in Source Serif 4, with the words it leans on underlined in viridian.

It refuses the SaaS stat-card grid and the status-pill dashboard. Accessibility floor: WCAG 2.2 AA for contrast, focus, and motion.

**Key Characteristics:**
- Viridian band owns the shell; the page is a cool near-white, never cream.
- One family at two widths: Archivo condensed (wdth 72) capitals for cover lines and labels, Archivo normal width for the interface.
- Source Serif 4 for the user's text and the italic "Condensed from …" credit line.
- Dot-leader contents lines with tabular figures as the signature, for counts and job steps alike.
- Ochre only for live work, red only for failure.
- 2px corners, no shadows, depth from ink rules.

## Colors

A single committed green house colour on a cool, slightly green-tinted neutral ramp, with two signal hues that each mean exactly one thing.

### Primary
- **Viridian Band** (`band`): the masthead band across every signed-in page and the full-height cover panel on sign-in; also the primary button fill and the text-selection colour. Hover deepens to **Band Deep** (`band-deep`).
- **Viridian Ink** (`viridian`): the text-role viridian for links, the Ready state, focus rings, caret, the active new-document tab underline, top-word rank numbers, and the marked-word underlines. In light mode it equals the band hue; in dark mode it lifts to `viridian-dark` so it stays legible as text on the dark ground.
- **On Band** (`on-band`) and **On Band Muted** (`on-band-muted`): text on the band; muted carries inactive nav links, the signed-in email, and the cover's credit line and leaders.

### Secondary
- **Live Ochre** (`live`, text `on-live`): the fill behind the In line / Analysing state and behind the figure of the one contents line still in progress. Nothing finished or idle is ever ochre.

### Tertiary
- **Failure Red** (`fail`) with **Failure Wash** (`fail-wash`): the Failed state, the figure of a "Gave up" step, invalid-field borders, inline field errors, and the error notice (red border on the wash).

### Neutral
- **Cool Ground** (`ground`): the page. A cool near-white with a green cast; it must never drift warm or cream.
- **Surface White** (`surface`): field interiors, notices, the upload target, and hover fill on document rows and quiet buttons.
- **Near-Black Ink** (`ink`): text, the 3px section rules, the running-line rules, field bottom borders, quiet-button outlines.
- **Muted Slate-Green** (`muted`): secondary text, journey summaries, table header labels, dates.
- **Hairline** (`rule`): 1px dividers, field side borders, row separators, disabled button fill.
- **Leader Grey** (`leader`): the 2px dotted leaders and field hover border. Decorative, never text.

### Dark mode
Every role has a `-dark` counterpart applied under `prefers-color-scheme: dark`. The band deliberately drops from `band` to `band-dark` rather than keeping the light value: at full `#0e5a4a` the band glares against the `#0f1412` dark ground and out-weighs the content; the deeper band keeps the shell committed while staying calmer than the page's text.

### Named Rules
**The One Meaning Rule.** Ochre means "still happening" and red means "failed". Neither appears for emphasis, branding, or warnings of any other kind; if nothing is in progress, no ochre is on screen.

**The Band Owns the Shell Rule.** Viridian fills the masthead (and the sign-in cover) edge to edge. Content regions stay on the cool ground; the band is never reused as a content card or section background.

**The Cool Page Rule.** The ground is `ground`, a cool green-tinted near-white. No cream, beige, or warm paper tones.

## Typography

**Display Font:** Archivo, variable with the `wdth` axis loaded (fallback system-ui, sans-serif)
**Body Font:** Archivo at normal width (fallback system-ui, sans-serif)
**Reading Font:** Source Serif 4, weight axis only (no `opsz`: it more than doubled each file for no visible gain at reading sizes), roman and italic (fallback Georgia, serif)

**Character:** One grotesque at two widths: pulled to condensed width and set in heavy capitals it becomes a magazine cover line; at normal width it is a plain, sturdy interface face. Source Serif 4 is the page of the book: the user's words and the digest's italic credit.

### Hierarchy
- **Cover** (800, clamp(4.5rem, 11vw, 9rem), line-height 0.8, condensed caps): the "Digest" wordmark on the sign-in cover only.
- **Display** (800, 6rem, line-height 0.85, condensed caps): the poster figure that answers the document (word count or row count), with a condensed-caps label beneath it.
- **Headline** (800, 3rem mobile / 3.75rem from 640px, line-height 1, condensed caps, balanced wrap): page titles and document titles (max 28ch). The band wordmark uses the same style at 2.25rem.
- **Title** (800, 1.5rem to 1.875rem, condensed caps): the ranked top words and the "Choose a file" upload heading.
- **Label** (700, 0.8125rem to 1.125rem, letter-spacing 0.08em, condensed caps): section headings under a 3px rule, table headers, state labels (0.875rem), new-document tabs.
- **Body** (400 to 600, 0.9375rem to 1.125rem, Archivo normal width, tabular numerals everywhere): UI text, contents labels and figures, nav, buttons, document-row titles (600, 1.125rem).
- **Reading** (400, 1.125rem / 1.25rem from 640px, line-height 1.75, max 68ch): the user's text on the document page; also the paste textarea and the larger serif lead sentences in empty and processing states.
- **Credit** (italic, 1.125rem on title blocks, 0.9375rem in lists, muted): the "Condensed from …" line.

### Named Rules
**The Two Widths Rule.** Condensed width (`wdth` 72) is always paired with capitals and only used for cover lines, poster figures, and labels. Interface text is never condensed; capitals are never set at normal width.

**The Own Case Rule.** User data keeps its case. An uploaded filename used as a title, and CSV column names, are set in the cover style with capitals switched off (`normal-case`), because uppercasing would alter the data.

**The Credit Line Rule.** Every document title is followed by an italic serif credit, "Condensed from pasted text" or "Condensed from a text file / a CSV file, size", with the received time on the document page.

**The Tabular Rule.** Numerals are tabular across the whole app so figures stack on one right-aligned column.

## Layout

A single centred column, max 72rem wide, with 1rem side padding (2rem from 640px). The band spans full width with its content on the same column. Main content stacks with a 2rem gap and 2.5rem top and bottom padding; a footer under a hairline carries the API status line.

The document page splits from 1024px into a fixed 22rem left column (poster figure, "In this document" contents, "How it got here" contents; sticky at 1.5rem from the top) and a fluid right column (top words, then the serif text), 3rem apart (4rem from 1280px). Below 1024px the columns stack.

Under the document title sits **the running line**: state and a one-phrase journey summary on one row, framed above and below by 1px ink rules.

The sign-in screen is a two-part spread from 1024px: the viridian cover (1.1fr) with wordmark, contents list, and credit; the form (1fr, max 24rem) on the ground. On smaller screens the cover stacks above the form.

CSV columns render as a data table from 640px; on phones each column becomes its own contents block under a 3px rule so no figure scrolls off-screen.

Spacing rhythm: 0.3rem between contents lines, 0.5rem / 0.75rem inside groups, 1.5rem between sections in a column, 2rem between page blocks, 3rem between major columns.

## Elevation & Depth

The system is completely flat. There are no shadows anywhere, no blur, no layered cards. Depth and grouping come from ink rules and type weight: a 3px ink rule opens each section, 1px ink rules frame the running line and table heads, 1px hairlines separate rows. The only tonal shift is `surface` against `ground` for fields, notices, and hover fills.

### Named Rules
**The Ruled Not Raised Rule.** Separate content with ink rules and space. If a region seems to need a shadow or a card, give it a 3px section rule and a condensed label instead.

## Shapes

Square by intent: interactive controls (buttons, fields, the file-picker button) take a 2px corner (`rounded.corner`) and everything else is a sharp rectangle. State markers are 0.5rem squares, never dots. Live highlights are flat rectangular fills behind the text. Borders are 1px hairlines, 1px ink outlines, a 2px ink bottom edge on fields, 2px dotted leaders, 3px ink section rules, a 4px tab underline, and a 2px dashed outline only on the upload drop target.

## Components

### Buttons
Solid, square, and calm.
- **Shape:** near-square (2px corners), min height 2.75rem.
- **Primary:** band fill with on-band text, 600 weight, 0.9375rem, padding 0.625rem 1.25rem. Used for the main action on a page (New document, Upload it again, Sign in).
- **Hover / Focus:** fill deepens to band-deep over 160ms (cubic-bezier(0.2, 0.7, 0.2, 1)); focus is a 2px viridian outline offset 3px (on-band inside the band).
- **Disabled:** hairline fill, muted text, not-allowed cursor.
- **Quiet:** transparent with a 1px ink outline, full width, label left and a muted secondary value right on the baseline; hover fills with surface. Used for the demo-account sign-in choices.
- **Text actions:** links in viridian, 600, with a 1px underline at 0.22em offset that thickens to 2px on hover.

### Inputs / Fields
- **Style:** surface fill, 1px hairline sides and top, a 2px ink bottom edge like a ruled line, 2px corners, padding 0.625rem 0.75rem, 1rem text. The paste textarea switches to the serif reading face.
- **Hover:** side borders darken to leader grey; the ink bottom stays.
- **Focus:** borders turn viridian with the 2px viridian outline at 0 offset.
- **Error:** borders turn red; the message sits below in red, 0.875rem, 500.
- **Upload target:** 2px dashed hairline box on surface with a condensed-caps "Choose a file" heading; the border turns viridian on hover.

### Navigation
- **Band nav:** wordmark left in condensed caps (2.25rem); right: Documents, New document, Accounts (admins), the email (on-band-muted, hidden below 640px), Log out. Links are 0.9375rem, 500. Inactive links are on-band-muted and brighten to on-band on hover; the current page is on-band with a 2px on-band underline. Documents stays current on every document and job page. Log out is an underlined text button.
- **Tabs (new document):** condensed-caps labels on a 1px ink baseline; the selected tab gets a 4px viridian underline and ink text, others are muted.

### State Marks
- **Style:** condensed caps, 700, 0.875rem, 0.08em tracking, led by a 0.5rem square in the current colour.
- **Ready:** viridian text and square. **Failed:** red text and square. **Inactive (accounts):** muted.
- **In progress (In line / Analysing):** an ochre rectangle behind ink text; its square breathes (opacity to 0.25 and back over 1.6s).

### Contents Line (signature)
The digest's index line: label, a flexible 2px dotted leader (min 1.5rem, nudged up 0.3em to sit at x-height), then the figure, 600 weight, tabular, right-aligned, never wrapping. Lines stack 0.3rem apart under a condensed-caps label and a 3px ink rule. One component serves the document's counts ("In this document"), the job's steps ("How it got here"), CSV column blocks on mobile, and the sign-in cover's list of what Digest does. The line still in progress gets an ochre fill behind its figure; a failed step's figure turns red. The documents list uses the same anatomy: title, leader, state mark, with the credit line and date beneath.

### Running Line
The row under a document title: the state mark, then a muted one-phrase journey summary ("queued 09:39, analysed in 2s", "picked up 09:40, attempt 1 of 3", "gave up after 3 attempts"), framed by 1px ink rules above and below.

### Marked Words
The ten words a text leans on are set 600 with a 0.14em viridian underline at 0.2em offset, fading 6% per rank. The ranked list above repeats them as condensed-caps titles with a small viridian rank number.

### Notices
Max 70ch, 1px hairline border on surface, padding 0.75rem 1rem. The error variant takes a red border on the failure wash. No side stripes, no icons.

### Data Table
Full width, opened by a 3px ink rule; condensed-caps muted headers over a 1px ink line; rows separated by hairlines with 0.625rem vertical padding; numeric columns right-aligned.

### Motion
Two moments only. **Leader set:** on the sign-in cover each leader draws left to right (scaleX 0 to 1, 640ms, cubic-bezier(0.16, 1, 0.3, 1)), starting at 300ms and staggered 120ms per line, as if the contents were being typeset. **Breathe:** the in-progress state square pulses. Both are switched off under `prefers-reduced-motion: reduce`. Elsewhere only colour transitions (160ms).

## Do's and Don'ts

### Do:
- **Do** keep the viridian band edge to edge at the top of every signed-in page, and use `band-dark` in dark mode so the shell stays committed without glaring.
- **Do** list figures as contents lines: label, dotted leader, tabular figure on a right-aligned column.
- **Do** open every section with a 3px ink rule and a condensed-caps label.
- **Do** follow every document title with the italic serif "Condensed from …" credit line, and on the document page with the running line between 1px ink rules.
- **Do** keep uploaded filenames and CSV column names in their own case (`normal-case`) when set in the cover style.
- **Do** reserve ochre for the one item still in progress and red for failure.
- **Do** keep corners at 2px and depth flat.
- **Do** turn off leader-set and breathe under reduced motion, and keep text pairs at WCAG 2.2 AA contrast.

### Don't:
- **Don't** use shadows, elevation, or floating cards.
- **Don't** put a kicker or eyebrow line above a heading; labels sit under a rule as the heading itself.
- **Don't** use side-stripe callouts (a thick coloured left border on notices or rows).
- **Don't** use pills or rounded badges; state is a square mark and condensed caps.
- **Don't** use ochre or red for anything except live work and failure.
- **Don't** let the ground drift warm or cream.
- **Don't** set interface text in condensed width, or set capitals at normal width.
- **Don't** lay out counts as a stat-card grid.
