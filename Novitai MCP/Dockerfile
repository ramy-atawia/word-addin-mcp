# Multi-stage Dockerfile for Word Add-in MCP Frontend
FROM node:18-alpine as base

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Development stage
FROM node:18-alpine as development
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev-server"]

# Test stage
FROM node:18-alpine as test
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
CMD ["npm", "run", "test"]

# Production stage
FROM node:18-alpine as production
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]