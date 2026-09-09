interface CustomWindow extends Window {
  env: {
    API_URL: string;
    API_PATH: string;
  };
}

const appEnv = (window as unknown as CustomWindow).env;
export const baseUrl = `${appEnv.API_URL}${appEnv.API_PATH}`;

/** A non-2xx response, carrying the backend's own explanation. */
export class ApiError extends Error {
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Read the `detail` an error response carries.
 *
 * The backend sends a plain string for service-level rejections (404, 409) but
 * FastAPI sends an array of validation objects for 422, so both shapes are
 * handled here rather than at every call site.
 */
async function readDetail(response: Response): Promise<string> {
  const fallback = `Request failed with status ${response.status}`;

  try {
    const body: unknown = await response.json();
    if (typeof body !== 'object' || body === null || !('detail' in body)) {
      return fallback;
    }

    const { detail } = body;
    if (typeof detail === 'string') {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) =>
          typeof item === 'object' && item !== null && 'msg' in item
            ? String((item as { msg: unknown }).msg)
            : null,
        )
        .filter((message): message is string => message !== null);
      if (messages.length > 0) {
        return messages.join('; ');
      }
    }

    return fallback;
  } catch {
    return fallback;
  }
}

/**
 * Thin wrapper around fetch that targets the backend API.
 *
 * Always sends credentials: the backend identifies the learner from its
 * development cookie, and the dev server is a different origin from the API.
 */
export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    credentials: 'include',
  });
  if (!response.ok) {
    throw new ApiError(response.status, await readDetail(response));
  }
  return (await response.json()) as T;
}
