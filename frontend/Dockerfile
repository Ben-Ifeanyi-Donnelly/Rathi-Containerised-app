# syntax=docker/dockerfile:1
FROM nginx:1.27-alpine
# Copy Nginx config and static assets
COPY frontend/nginx.conf /etc/nginx/nginx.conf
COPY frontend/week5.html /usr/share/nginx/html/week5.html
COPY frontend/index.html /usr/share/nginx/html/index.html
EXPOSE 8080
