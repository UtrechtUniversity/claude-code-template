# Dev-only image. Production build (static assets served by a reverse proxy) is out of scope.

FROM node:22-bookworm-slim

WORKDIR /app

# Install deps first for layer caching.
COPY package.json ./
RUN npm install

EXPOSE 5173

CMD ["npm", "run", "dev"]
