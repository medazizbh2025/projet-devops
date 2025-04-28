FROM postgres:13-alpine
COPY schema.sql /docker-entrypoint-initdb.d/
ENV POSTGRES_USER=user
ENV POSTGRES_PASSWORD=password
ENV POSTGRES_DB=user-service