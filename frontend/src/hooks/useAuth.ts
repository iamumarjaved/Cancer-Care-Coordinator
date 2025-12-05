'use client';

import { useEffect } from 'react';
import { useAuth as useClerkAuth } from '@clerk/nextjs';
import { api } from '@/lib/api';

/**
 * Hook to connect Clerk authentication with the API client.
 * This should be called once in a top-level component.
 */
export function useApiAuth() {
  const { getToken, isLoaded, isSignedIn } = useClerkAuth();

  useEffect(() => {
    if (isLoaded) {
      // Set the token getter in the API client
      api.setTokenGetter(async () => {
        if (!isSignedIn) return null;
        try {
          // Get a fresh token from Clerk
          return await getToken();
        } catch {
          return null;
        }
      });
    }
  }, [isLoaded, isSignedIn, getToken]);

  return { isLoaded, isSignedIn };
}

/**
 * Re-export Clerk's useAuth for convenience
 */
export { useAuth as useClerkAuth } from '@clerk/nextjs';
