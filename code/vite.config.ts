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
const primaryIP = networkIPs[0] || 'localhost';

console.log(`🌐 Available network IPs: ${networkIPs.join(', ')}`);
console.log(`🔧 Primary IP for backend: ${primaryIP}:8000`);
console.log(`🔧 Vite will use relative URLs for API calls (network-agnostic)`);

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './', // Use relative paths for deployment
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          leaflet: ['leaflet', 'react-leaflet', 'react-leaflet-cluster']
        }
      }
    }
  },
  server: {
    host: '0.0.0.0', // Allow network access
    port: 5173,
    proxy: {
      '/api': {
        target: `http://${primaryIP}:8000`,
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('🚨 Proxy error:', err);
          });
          proxy.on('proxyReq', (_proxyReq, req, _res) => {
            console.log(`🔄 Proxying API request: ${req.method} ${req.url} -> http://${primaryIP}:8000${req.url}`);
          });
        },
      },
      '/media': {
        target: `http://${primaryIP}:8000`,
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
