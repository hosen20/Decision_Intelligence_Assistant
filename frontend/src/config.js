// API base URL configuration
// In development (vite dev server): use localhost:8000
// In production (nginx): use relative path /api
const API_BASE = import.meta.env.DEV
  ? 'http://localhost:8000'
  : '/api'

export default API_BASE
