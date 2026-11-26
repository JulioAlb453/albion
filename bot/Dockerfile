# Etapa 1: compilar TypeScript con todas las dependencias
FROM node:22-alpine AS compilar
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json tsconfig.build.json ./
COPY src ./src
RUN npm run build

# Etapa 2: imagen final, solo con lo necesario para ejecutar
FROM node:22-alpine
ENV NODE_ENV=production
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=compilar /app/dist ./dist
# el usuario "node" ya existe en la imagen: el bot no corre como root
USER node
CMD ["node", "dist/index.js"]
