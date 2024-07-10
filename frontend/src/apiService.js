// src/apiService.js

import axios from 'axios';
import API_BASE_URL from './config';

export const uploadFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await axios.post(`${API_BASE_URL}/upload/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw error;
  }
};

export const queryIndex = async (question) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/query/`, { question });
    return response.data;
  } catch (error) {
    console.error('Error querying index:', error);
    throw error;
  }
};
