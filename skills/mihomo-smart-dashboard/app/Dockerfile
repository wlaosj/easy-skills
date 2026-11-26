FROM python:3.11-alpine

RUN apk add --no-cache openssh-client tzdata \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

WORKDIR /app

COPY bbolt_parser.py app.py /app/
COPY static /app/static

ENV PORT=8899
ENV SYNC_INTERVAL=60
ENV SOURCE_MODE=auto
ENV LOCAL_DB_PATH=/data/cache.db
ENV ROS_HOST=""
ENV ROS_PORT=22
ENV ROS_USER=admin
ENV ROS_DB_PATH=etc-mihomo/cache.db
ENV SSH_KEY_PATH=/ssh/id_ed25519

EXPOSE 8899

CMD ["python3", "/app/app.py"]
