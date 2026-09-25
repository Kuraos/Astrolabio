# Las dos imágenes base van por digest (ADR 0013): el tag dice qué línea se
# sigue y el digest, en qué punto de ella.

# Etapa de build: compila el frontend con las versiones exactas del lockfile.
FROM node:24-alpine@sha256:ebfe2f90462722a7a4de65e91990e97fe0d401c70e0e762c5b53302f905ec1c1 AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY tsconfig.json vite.config.ts index.html ./
COPY src ./src
RUN npm run build

# Etapa final: nginx sirve el build y hace de proxy a la API (ADR 0005).
FROM nginx:alpine@sha256:1ed1b0e1d7652937d6cbdaf4018c7b6fc009a7dd6c3047351e2eddda745de43f

COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
