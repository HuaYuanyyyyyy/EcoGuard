import axios from 'axios'


const getBaseURL = () => {
  const host = window.location.hostname
  if (host === 'localhost') {
    return 'http://localhost:8000'
  }
  return import.meta.env.VITE_API_BACKEND
}

const api = axios.create({
  baseURL: getBaseURL(),
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