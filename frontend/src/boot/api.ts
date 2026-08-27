interface CustomWindow extends Window {
  env: {
    API_URL: string;
    API_PATH: string;
  };
}

const appEnv = (window as unknown as CustomWindow).env;
export const baseUrl = `${appEnv.API_URL}${appEnv.API_PATH}`;

/**
 * Thin wrapper around fetch that targets the backend API.
 * Extend it with authentication and error handling as needed.
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, init);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return (await response.json()) as T;
}
