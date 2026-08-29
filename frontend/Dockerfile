# Stage 1: Build Angular application
FROM node:20-alpine AS build
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build -- --configuration production

# Stage 2: Serve with Nginx
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled files from build stage (handling browser subfolder if present)
COPY --from=build /app/dist/support-ticket-angular/browser /usr/share/nginx/html/
# Fallback in case application builder output is directly in support-ticket-angular
RUN if [ ! -f /usr/share/nginx/html/index.html ]; then cp -r /app/dist/support-ticket-angular/* /usr/share/nginx/html/ || true; fi

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
