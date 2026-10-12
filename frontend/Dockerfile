# Dependencies, installed once and shared by every stage below. Everything
# runs as the image's unprivileged `node` user.
FROM node:24-alpine AS deps
ENV NEXT_TELEMETRY_DISABLED=1
WORKDIR /app
RUN chown node:node /app
USER node
COPY --chown=node:node package.json package-lock.json ./
RUN npm ci

FROM deps AS build
COPY --chown=node:node . .
RUN npm run build

# Last stage, so a plain `docker build .` produces the production image: the
# standalone server and its static files only - no source, no node_modules
# install, no dev dependencies. There is no dev stage: on Docker Desktop,
# file-change events don't reach the container, so hot reload can't work -
# develop with `npm run dev` on the host instead.
FROM node:24-alpine AS runtime
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0
WORKDIR /app
COPY --from=build --chown=node:node /app/.next/standalone ./
COPY --from=build --chown=node:node /app/.next/static ./.next/static
COPY --from=build --chown=node:node /app/public ./public
USER node
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
    CMD node -e "fetch('http://localhost:3000/').then(r => process.exit(r.ok ? 0 : 1), () => process.exit(1))"
CMD ["node", "server.js"]
