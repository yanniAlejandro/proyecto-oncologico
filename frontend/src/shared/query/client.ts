import { QueryClient } from "@tanstack/react-query";

let browserClient: QueryClient | undefined;

function makeClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 } },
  });
}

/** Un único QueryClient por pestaña: las islas comparten caché aunque sean raíces React distintas. */
export function getQueryClient(): QueryClient {
  if (typeof window === "undefined") return makeClient();
  browserClient ??= makeClient();
  return browserClient;
}
