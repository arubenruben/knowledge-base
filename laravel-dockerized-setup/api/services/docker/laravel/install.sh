#!/bin/bash

# Exit on any error
set -e

# Remove content within the application directory. Force a fresh install.
rm -rf ./out/${APP_NAME}

cd ./out

# Install Laravel with React, PHPUnit, and npm
laravel new ${APP_NAME} ${INSTRUCTIONS} --no-interaction -f

cd ${APP_NAME}