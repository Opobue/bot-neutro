export type Tier = 'freemium' | 'premium';

export interface ClientConfig {
  apiBaseUrl: string;
  apiKey: string;
  defaultTier: Tier;
}

const parseTier = (value: string | undefined): Tier => {
  if (value === 'premium') {
    return 'premium';
  }
  return 'freemium';
};

export const getConfig = (): ClientConfig => {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;
  const apiKey = import.meta.env.VITE_API_KEY as string | undefined;
  const defaultTier = parseTier(import.meta.env.VITE_DEFAULT_TIER as string | undefined);

  if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL no está configurado');
  }

  if (!apiKey) {
    throw new Error('VITE_API_KEY no está configurado');
  }

  return {
    apiBaseUrl,
    apiKey,
    defaultTier,
  };
};
