ARG PHP_VERSION
ARG NODE_VERSION

FROM composer:latest AS composer

FROM php:${PHP_VERSION}-cli

WORKDIR /app

# Copy the composer stage
COPY --from=composer /usr/bin/composer /usr/bin/composer
# Set the PATH for Composer
ENV PATH="/root/.composer/vendor/bin:${PATH}"

# Install system dependencies to run a postgresql database
RUN apt-get update && apt-get install -y git \
    curl \
    unzip

# Install Node 24
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    apt-get install -y nodejs

RUN composer global require laravel/installer

COPY ./install.sh .

RUN chmod +x install.sh

ENTRYPOINT [ "./install.sh" ]