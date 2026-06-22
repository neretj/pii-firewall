# Builder stage: install deps and produce the standalone build.
FROM node:20-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Runner stage: serve the standalone output (next.config.mjs sets output: 'standalone').
FROM node:20-slim AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3010

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3010

# Standalone output is served via node server.js (not `next start`); port comes from PORT.
CMD ["node", "server.js"]
