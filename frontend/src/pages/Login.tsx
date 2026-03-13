import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { LogIn } from 'lucide-react';

export function Login() {
  const { login, loading, error, token } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin');

  // If already has token, go to dashboard
  useEffect(() => {
    if (token) {
      navigate('/', { replace: true });
    }
  }, [token, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const success = await login(username, password);
    if (success) {
      navigate('/');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <div className="w-full max-w-md p-8 bg-white shadow-xl rounded-2xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">ELOS <span className="text-blue-600">Sync</span></h1>
          <p className="text-gray-500 mt-2">Plataforma de Tabulação e Automação</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 rounded-lg text-center">
              {error}
            </div>
          )}

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-700">Usuário</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 border rounded-xl focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-colors bg-gray-50"
              required
            />
          </div>

          <div>
            <label className="block mb-2 text-sm font-medium text-gray-700">Senha</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 border rounded-xl focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-colors bg-gray-50"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center px-4 py-3 text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition-colors font-medium cursor-pointer disabled:opacity-50"
          >
            {loading ? <span className="animate-pulse">Acessando...</span> : (
              <>
                Entrar <LogIn className="ml-2" size={18} />
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
