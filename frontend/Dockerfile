# Use lightweight Nginx web server
FROM nginx:alpine

# Copy static frontend HTML to Nginx default public directory
COPY index.html /usr/share/nginx/html/index.html

# Expose HTTP port 80
EXPOSE 80

# Run Nginx in foreground mode
CMD ["nginx", "-g", "daemon off;"]

