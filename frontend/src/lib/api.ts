export const getDefaultApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    const { protocol, hostname } = window.location;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }
    // Derivar backend por convención en Azure: reemplazar "frontend" por "backend" y usar puerto 8000
    let backendHost = hostname;
    if (backendHost.includes('frontend')) {
      backendHost = backendHost.replace('frontend', 'backend');
    }
    return `${protocol}//${backendHost}:8000`;
  }
  return 'http://localhost:8000';
};

export const API_BASE_URL: string = (import.meta as any).env?.VITE_API_URL || getDefaultApiBaseUrl();

export const apiFetch = (path: string, options?: RequestInit) => {
  const url = path.startsWith('http') ? path : `${API_BASE_URL}${path}`;
  return fetch(url, options);
};


