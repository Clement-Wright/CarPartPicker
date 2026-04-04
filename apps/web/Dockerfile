FROM node:18-bullseye-slim

WORKDIR /workspace

COPY package.json package.json
COPY package-lock.json package-lock.json
COPY apps/web/package.json apps/web/package.json
RUN npm install

COPY apps/web /workspace/apps/web

WORKDIR /workspace/apps/web
ENV NEXT_TELEMETRY_DISABLED=1

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
