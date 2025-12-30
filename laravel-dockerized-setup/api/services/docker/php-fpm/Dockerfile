ARG PHP_VERSION
ARG NODE_VERSION
ARG LARAVEL_ENV_ENCRYPTION_KEY

FROM composer:latest AS composer

FROM php:${PHP_VERSION}-fpm

# Re-declare ARG after FROM to make it available in this stage
ARG NODE_VERSION
ARG LARAVEL_ENV_ENCRYPTION_KEY

# Set Laravel encryption key environment variable
ENV LARAVEL_ENV_ENCRYPTION_KEY=${LARAVEL_ENV_ENCRYPTION_KEY}

# Set the working directory to Laravel standard location
WORKDIR /var/www

# Create www-data user and group if they don't exist
RUN groupadd -g 1000 www-data || true && \
    useradd -u 1000 -ms /bin/bash -g www-data www-data || true

# Copy the composer stage
COPY --from=composer /usr/bin/composer /usr/bin/composer
# Set the PATH for Composer
ENV PATH="/root/.composer/vendor/bin:${PATH}"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    unzip \
    libzip-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install PHP extensions. Postgresql is needed
RUN docker-php-ext-install zip pdo pdo_pgsql

# Install only runtime libraries needed in production
# libfcgi-bin and procps are required for the php-fpm-healthcheck script
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libicu-dev \
    libzip-dev \
    libfcgi-bin \
    procps \
    && apt-get autoremove -y && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Download and install php-fpm health check script
RUN curl -o /usr/local/bin/php-fpm-healthcheck \
    https://raw.githubusercontent.com/renatomefi/php-fpm-healthcheck/master/php-fpm-healthcheck \
    && chmod +x /usr/local/bin/php-fpm-healthcheck

# Install Node 24
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    apt-get install -y nodejs

# Copy 
COPY ./php-fpm/dev.sh /usr/local/bin/dev.sh
RUN chmod +x /usr/local/bin/dev.sh

# Copy production script
COPY ./php-fpm/prod.sh /usr/local/bin/prod.sh
RUN chmod +x /usr/local/bin/prod.sh

# Copy PHP-FPM configuration
COPY ./php-fpm/www.conf /usr/local/etc/php-fpm.d/www.conf

# Copy application source code
COPY --chown=www-data:www-data . /var/www

# Set proper permissions
RUN mkdir -p /var/www/storage/app/public \
    /var/www/storage/framework/cache \
    /var/www/storage/framework/sessions \
    /var/www/storage/framework/testing \
    /var/www/storage/framework/views \
    /var/www/storage/logs \
    /var/www/bootstrap/cache \
    && chown -R www-data:www-data /var/www/storage /var/www/bootstrap/cache \
    && chmod -R 775 /var/www/storage /var/www/bootstrap/cache

EXPOSE 9000