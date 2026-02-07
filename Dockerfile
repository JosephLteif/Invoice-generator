# Stage 1: Build Angular Frontend
FROM node:22-alpine as build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build -- --configuration production

# Stage 2: Serve with Flask
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_ENV=production
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Set work directory
WORKDIR /app

# Install system dependencies
# fonts-liberation provides a fallback for Arial/Helvetica used in ReportLab
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files (backend)
COPY backend/ .

# Copy built frontend assets from build stage to 'static' folder
# Angular 17+ with application builder outputs to dist/frontend/browser
COPY --from=build /app/dist/frontend/browser static

# Create directory for invoices if it doesn't exist
RUN mkdir -p data/invoices

# Expose port 5000
EXPOSE 5000

# Run the application
CMD ["flask", "run"]
