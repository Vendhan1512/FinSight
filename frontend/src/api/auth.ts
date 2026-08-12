import { api } from './client';

export const AuthAPI = {
  login: async (username: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const res = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return res.data;
  },

  me: async () => {
    const res = await api.get('/auth/me');
    return res.data; // { username, role }
  }
};
