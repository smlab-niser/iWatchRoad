import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import { networkInterfaces } from 'os'

// Get the actual network IP address
const getNetworkIP = () => {
  const nets = networkInterfaces();
  const results = [];

  for (const name of Object.keys(nets)) {
    for (const net of nets[name] || []) {
      // Skip internal and non-IPv4 addresses
      if (net.family === 'IPv4' && !net.internal) {
        results.push(net.address);
      }
    }
  }

  return results;
}

// Get current network IP for display purposes
const networkIPs = getNetworkIP();

console.log(`🌐 Available network IPs: ${networkIPs.join(', ')}`);
console.log(`🔧 Primary IP for backend: 127.0.0.1:8000`);
console.log(`🔧 Vite will use relative URLs for API calls (network-agnostic)`);

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/project/iwatchroad/',
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // Regular API endpoints (potholes, etc.)
      '/project/iwatchroad/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('🚨 API Proxy error:', err);
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            const reqUrl = req.url || '';
            console.log(`🔄 Proxying API request: ${req.method} ${reqUrl} -> http://127.0.0.1:8000${reqUrl}`);
          });
        }
      },
      // Government API endpoints
      '/project/iwatchroad/gov-api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('🚨 Gov API Proxy error:', err);
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            const reqUrl = req.url || '';
            console.log(`🔄 Proxying Gov API request: ${req.method} ${reqUrl} -> http://127.0.0.1:8000${reqUrl}`);
          });
        }
      },
      // Accounts endpoints with prefix
      '/project/iwatchroad/accounts': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('🚨 Accounts Proxy error:', err);
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            const reqUrl = req.url || '';
            console.log(`🔄 Proxying Accounts request: ${req.method} ${reqUrl} -> http://127.0.0.1:8000${reqUrl}`);
          });
        }
      },
      // Media endpoints with prefix
      '/project/iwatchroad/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      },
      // Fallback for direct API calls
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('🚨 Proxy error:', err);
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            console.log(`🔄 Proxying API request: ${req.method} ${req.url} -> http://127.0.0.1:8000${req.url}`);
          });
        }
      },
      '/accounts': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('🚨 Proxy error:', err);
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            console.log(`🔄 Proxying ACCOUNTS request: ${req.method} ${req.url} -> http://127.0.0.1:8000${req.url}`);
          });
        }
      },
      '/media': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
});
