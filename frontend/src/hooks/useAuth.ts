import { useState, useCallback } from 'react';
import { useAuthStore } from '../store/authStore';
import { api } from '../lib/api';
import type { components } from '../types/generated';

type TokenResponse = components["schemas"]["Token"];
type UserResponse = components["schemas"]["UserResponse"];

export function useAuth() {
  const { setAuth, logout, user, token } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      // OAuth2 uses form data
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const res = await api.post<TokenResponse>('/api/v1/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      const accessToken = res.data.access_token;
      
      // Fetch me
      const meRes = await api.get<UserResponse>('/api/v1/auth/me', {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      setAuth(meRes.data as any, accessToken);
      return true;
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Falha ao autenticar.');
      return false;
    } finally {
      setLoading(false);
    }
  }, [setAuth]);

  return {
    login,
    logout,
    user,
    token,
    loading,
    error,
  };
}
