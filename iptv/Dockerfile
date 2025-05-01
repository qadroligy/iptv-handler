FROM php:8.2-apache

# Install system packages: Python3 and required libraries
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-requests \
    python3-tabulate \
    python3-deepdiff \
    python3-paho-mqtt \
    locales \
    nano \
    curl \
    jq \
    nfs-common \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set timezone and locale
ENV TZ=Europe/Stockholm
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && locale-gen sv_SE.UTF-8

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Use custom entrypoint
ENTRYPOINT ["/entrypoint.sh"]
