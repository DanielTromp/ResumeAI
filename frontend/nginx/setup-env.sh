#!/bin/sh
# Script to set up environment variables for Nginx

# Get backend URL from environment or use default
export BACKEND_URL=${BACKEND_URL:-http://backend:8008}

echo "Creating Nginx configuration"
echo "Backend URL set to: $BACKEND_URL"

# We're now using a hardcoded configuration instead of variable substitution
# because that's causing issues with IPv6 resolution
cp /etc/nginx/conf.d/default.conf.template /etc/nginx/conf.d/default.conf

# Log configured backend for debugging
echo "Using backend hostname: backend:8008 (hardcoded in Nginx config)"

# Test backend connectivity - helps with debugging
echo "Testing backend connectivity..."
echo "Resolving ${BACKEND_URL}..."

# Install necessary tools
apk add --no-cache bind-tools iputils curl

# Try to resolve the backend hostname using dig
BACKEND_HOST=$(echo "${BACKEND_URL}" | sed -E 's|^https?://([^:/]+).*|\1|')
echo "Backend hostname: ${BACKEND_HOST}"
echo "Attempting to resolve backend hostname with dig..."
dig +short "${BACKEND_HOST}" || echo "Failed to resolve hostname with dig"

# Try to ping the backend
echo "Pinging backend..."
ping -c 1 "${BACKEND_HOST}" || echo "Failed to ping backend"

# Test HTTP connectivity
echo "HTTP test to ${BACKEND_URL}/api/health..."
curl -v --connect-timeout 5 --max-time 10 "${BACKEND_URL}/api/health" || echo "ERROR: Cannot connect to backend"

# Create a diagnostic page
mkdir -p /usr/share/nginx/html/debug
cat > /usr/share/nginx/html/debug/index.html <<EOF
<!DOCTYPE html>
<html>
<head>
    <title>ResumeAI - API Diagnostics</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1 { color: #333; }
        .status { padding: 15px; margin: 15px 0; border-radius: 4px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
        .info { background-color: #e2e3e5; color: #383d41; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 4px; overflow-x: auto; }
        button { padding: 8px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0069d9; }
    </style>
</head>
<body>
    <h1>ResumeAI API Diagnostic Tool</h1>
    <div class="info">
        <strong>Backend URL:</strong> http://backend:8008 (hardcoded in Nginx)
    </div>
    
    <h2>API Connectivity Tests</h2>
    <div id="test-results">
        <p>Click the buttons below to test API connectivity:</p>
        <button onclick="testHealth()">Test Health Endpoint</button>
        <button onclick="testVacancyStats()">Test Vacancy Stats</button>
        <button onclick="testResumes()">Test Resumes</button>
        <div id="results"></div>
    </div>

    <h2>Environment Information</h2>
    <pre id="env-info">
Frontend URL: [Loading...]
API URL: http://backend:8008 (hardcoded in Nginx config)
User Agent: [Loading...]
Online: [Loading...]
    </pre>

    <script>
        async function testEndpoint(name, url) {
            const resultDiv = document.getElementById('results');
            const startTime = new Date().getTime();
            
            resultDiv.innerHTML += '<div class="info">Testing ' + name + '...</div>';
            
            try {
                const response = await fetch(url);
                const endTime = new Date().getTime();
                const duration = endTime - startTime;
                
                if (response.ok) {
                    const data = await response.json();
                    resultDiv.innerHTML += 
                    '<div class="status success">' +
                        '✅ ' + name + ': Success (HTTP ' + response.status + ', ' + duration + 'ms)<br>' +
                        '<pre>' + JSON.stringify(data, null, 2).substring(0, 200) + '...</pre>' +
                    '</div>';
                } else {
                    resultDiv.innerHTML += 
                    '<div class="status error">' +
                        '❌ ' + name + ': Error (HTTP ' + response.status + ', ' + duration + 'ms)<br>' +
                        await response.text() +
                    '</div>';
                }
            } catch (error) {
                resultDiv.innerHTML += 
                '<div class="status error">' +
                    '❌ ' + name + ': Network Error<br>' +
                    error.message +
                '</div>';
            }
        }
        
        function testHealth() {
            testEndpoint('Health Check', '/api/health');
        }
        
        function testVacancyStats() {
            testEndpoint('Vacancy Statistics', '/api/statistics/vacancies');
        }
        
        function testResumes() {
            testEndpoint('Resumes', '/api/resumes?limit=1');
        }
        
        // Update environment info with actual values
        window.onload = function() {
            const envInfo = document.getElementById('env-info');
            envInfo.textContent = 
'Frontend URL: ' + window.location.origin + 
'\nAPI URL: ' + window.location.origin + '/api (proxied to http://backend:8008)' +
'\nUser Agent: ' + navigator.userAgent +
'\nOnline: ' + navigator.onLine;
        };
    </script>
</body>
</html>
EOF

echo "Diagnostic page created at /debug/"