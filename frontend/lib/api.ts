export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export async function api<T>(path:string, init?:RequestInit):Promise<T> {
  const response = await fetch(`${API}${path}`, {headers:{"Content-Type":"application/json", ...(init?.headers||{})}, cache:"no-store", ...init});
  if (!response.ok) throw new Error(`Service unavailable (${response.status})`);
  return response.json() as Promise<T>;
}
export const post = <T,>(path:string, body:unknown) => api<T>(path,{method:"POST",body:JSON.stringify(body)});
