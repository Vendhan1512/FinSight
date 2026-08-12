FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./

RUN npm install

COPY . .

# Expose Vite default port
EXPOSE 5173

# Command to run the application is specified in docker-compose.yml
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
