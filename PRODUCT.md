# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary: reviewers and evaluators (mentors, interviewers, hiring managers) who open the web UI, often signing in with a demo account, to judge how the system was built. They are scanning for proof that the pieces work and fit together, usually without much time.

Secondary: people who actually want insights about their own text or CSV files. The UI must hold up as a usable tool for them, not just a demo.

## Product Purpose

Digest is a document ingestion and insight service. A user pastes text or uploads a `.txt`/`.csv` file, the service computes insights, stores them, and lets the user read them back one at a time or as a list.

It was built in phases as an internship learning project. The feature is deliberately trivial; the point is the infrastructure around it (stateless API, Postgres as the source of truth, a Redis queue and cache, a background worker, structured logging, JWT auth, CI). Success means a reviewer leaves convinced the system is real, coherent and correct, and a real user gets readable insights without friction.

## Positioning

The insights and the infrastructure carry equal weight. Insights are the content and should be readable and satisfying. Infrastructure state shows up where it is part of the user's story: job progress for uploads, API health, and per-user ownership of documents. It should not be hidden, and it should not be staged as decoration either.

## Operating Context

- Entry is the login/register pages. When the API has demo mode on, they offer one-click demo user and demo admin sign-in.
- Paste flow: `POST /documents` returns insights immediately.
- Upload flow: `.txt`/`.csv` up to 10 MB is accepted with 202. A background job then moves `queued → running → succeeded | failed` and the UI polls it until it finishes. Up to 3 attempts; files that can never succeed (not UTF-8) fail at once with a reason.
- Documents list (newest first) and document detail are scoped to the signed-in user. Another user's document is a 404.
- Admins see an accounts page (`GET /admin/users`).
- The footer shows API status from the health endpoints.
- The browser talks only to Next.js. Next.js calls FastAPI server-side, and the JWT lives in an httpOnly cookie.

## Capabilities and Constraints

- Text insights: character counts (with and without whitespace), word, unique word, sentence and paragraph counts, average word length, top 10 words after stopword removal, and estimated reading time.
- CSV insights: row and column counts, plus per column its name, null count, inferred type (`integer`, `float`, `boolean`, `string`, `empty`) and min/max/mean for numeric columns.
- Out of scope by spec: language detection, sentiment, embeddings or any other "smarter" analysis. The UI must not imply them.
- Accepted formats are `.txt` and `.csv` only, UTF-8, 10 MB max. Documents cannot be edited once created.
- Tokens expire after 60 minutes. Roles are `user` and `admin`, and there is no in-app way to grant admin.
- Stack: Next.js 16 (App Router, TypeScript, Tailwind 4) frontend and a FastAPI backend, run together with Docker Compose.

## Brand Commitments

- Name: **Digest**.
- Existing tagline/description: "Paste text or upload a file and see what it's made of."
- Voice in the current UI is plain, direct and second person ("Your documents", "Just looking around? Use a demo account.").

## Evidence on Hand

- A real, working system with demo accounts, the README and phase write-ups in `docs/phase-*.md`.
- No testimonials, users, usage numbers or benchmarks exist. Do not invent any.

## Product Principles

1. **Show the system honestly.** States like queued, running, failed or API down are real information. Present them plainly and never fake progress or hide failure.
2. **Insights first, then the machinery.** A document page leads with what the text or CSV contains, and infrastructure detail sits where it explains something.
3. **Respect the reviewer's time.** Anyone landing cold, often via a demo account, should reach a meaningful document in a couple of clicks.
4. **Stay inside the spec.** Small feature set, done completely. No implied capabilities the backend doesn't have.

## Accessibility & Inclusion

WCAG 2.2 AA is the floor: contrast, visible focus, full keyboard operation, and status changes (job progress, errors) announced to assistive tech.
