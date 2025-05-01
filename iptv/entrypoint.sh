#!/bin/bash
set -e

# Fix ownership: everything inside /var/www/html should belong to www-data
echo "Setting file permissions..."
chown -R www-data:www-data /var/www/html

# Optionally: make your Python script executable
chmod +x /var/www/html/cfg-handler/cfg-handler.py

# Then run the original apache2-foreground command to start Apache
echo "Starting Apache..."
exec apache2-foreground
