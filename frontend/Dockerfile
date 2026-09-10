# Stage 1: Build production bundle
FROM node:20-alpine AS builder

WORKDIR /app

# Build arguments for API URL
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL:-http://localhost:8000}

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve using hardened Nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
