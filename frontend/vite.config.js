import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist', // Ensure output directory matches Netlify’s publish directory
    sourcemap: true, // Optional: for debugging
  },
  resolve: {
    alias: {
      // Optional: Add aliases if you have complex imports
      '@': '/src',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './setupTests.js',
    globals: true,
    include: ['src/**/*.{test,spec}.{js,jsx}'],
    coverage: {
      reporter: ['text', 'lcov'],
    },
  },
});