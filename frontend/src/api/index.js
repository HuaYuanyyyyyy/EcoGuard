import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 120000
})

export const fileApi = {
  upload: (formData) => api.post('/files/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  list: () => api.get('/files/list'),
  delete: (fileId) => api.delete(`/files/${fileId}`)
}

export const chatApi = {
  query: (message) => api.post('/chat/query', { message })
}