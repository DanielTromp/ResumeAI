# Raspberry Pi Network Fix for ResumeAI

This document explains how to fix network connectivity issues when running ResumeAI on a Raspberry Pi.

## Common Issues

1. Frontend cannot connect to backend (Dashboard showing "Failed to load dashboard data")
2. Nginx error: "host not found in upstream 'backend'"
3. Network error in console logs

## Solution

The issue is with Docker's DNS resolution on Raspberry Pi. The following changes have been made:

1. Updated `frontend/nginx/default.conf`:
   - Changed proxy_pass from `http://backend:8008` to `http://localhost:8008`
   - Updated Host headers to match

2. Updated `docker-compose.yml`:
   - Added extra_hosts setting to map host.docker.internal
   - Set BACKEND_URL environment variable to http://localhost:8008

## How to Apply the Fix

1. After pulling these changes, run:

```bash
./manage.sh docker-down
./manage.sh docker-up
```

2. If issues persist, you might need to rebuild the frontend:

```bash
docker-compose build --no-cache frontend
./manage.sh docker-up
```

3. To test the connectivity:

```bash
# Test backend API directly
curl http://localhost:8008/api/statistics/vacancies

# Check if frontend container can reach backend
docker exec resumeai-frontend-1 curl -I http://localhost:8008/api/statistics/vacancies
```

## Alternative Solutions

If the above doesn't work, try one of these:

1. Use host network mode for both containers:

```yaml
# In docker-compose.yml
services:
  backend:
    # Other settings...
    network_mode: host
  
  frontend:
    # Other settings...
    network_mode: host
```

2. Use the Raspberry Pi's actual IP address:

```
# Find your Raspberry Pi's IP address
ip addr show | grep "inet " | grep -v 127.0.0.1

# Then use that IP in docker-compose.yml
environment:
  - BACKEND_URL=http://192.168.x.x:8008
```

## Troubleshooting

If you're still experiencing issues:

1. Check backend logs: `docker logs resumeai-backend-1`
2. Check frontend logs: `docker logs resumeai-frontend-1`
3. Verify the backend is running: `curl http://localhost:8008/api/health`
4. Check the browser console for network errors