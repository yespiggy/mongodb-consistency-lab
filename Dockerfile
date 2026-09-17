FROM mongo:7.0.32
USER root
RUN apt-get update && apt-get install -y --no-install-recommends iptables \
    && rm -rf /var/lib/apt/lists/*
# The official entrypoint starts mongod as the mongodb user. Fault injection uses
# docker exec --user root, with NET_ADMIN only in this disposable lab container.
