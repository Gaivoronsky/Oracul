#!/bin/bash

# This script generates env.js with environment variables
# to make them available to the React app at runtime

# Path to env.js
ENV_FILE=/usr/share/nginx/html/env.js

# Start with empty env object
echo "window.env = {" > $ENV_FILE

# Add API_URL
if [ -n "$API_URL" ]; then
  echo "  \"API_URL\": \"$API_URL\"," >> $ENV_FILE
else
  echo "  \"API_URL\": \"http://localhost:8000\"," >> $ENV_FILE
fi

# Add other environment variables that start with REACT_APP_
for envvar in $(env | grep -E "^REACT_APP_" | sort); do
  key=$(echo $envvar | cut -d= -f1)
  value=$(echo $envvar | cut -d= -f2-)
  echo "  \"$key\": \"$value\"," >> $ENV_FILE
done

# Close the env object
echo "};" >> $ENV_FILE

# Update Nginx configuration with environment variables
envsubst '${API_URL}' < /etc/nginx/conf.d/default.conf > /etc/nginx/conf.d/default.conf.tmp
mv /etc/nginx/conf.d/default.conf.tmp /etc/nginx/conf.d/default.conf

echo "Environment variables configured"