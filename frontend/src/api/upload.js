import client from './client'

export const uploadApi = {
  uploadFile: (file, uploadType, onProgress) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('uploadType', uploadType)
    return client.post('/upload/dataset', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: e => {
        if (onProgress && e.total) onProgress(Math.round((e.loaded * 100) / e.total))
      },
    })
  },
  getHistory: () => client.get('/upload/history'),
  deleteUpload: (id) => client.delete(`/upload/${id}`),
}
