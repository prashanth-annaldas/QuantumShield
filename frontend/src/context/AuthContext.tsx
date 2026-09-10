import React, { useState, useEffect, ReactNode } from "react";
import { User, LoginRequest, RegisterRequest } from "../types";
import { authApi } from "../services/api";
import { AuthContext } from "./auth-context";

const TOKEN_KEY = "qds_access_token";
const USER_KEY = "qds_user";

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem(USER_KEY);

    try {
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState<string | null>(() =>
    localStorage.getItem(TOKEN_KEY)
  );

  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Restore authenticated session on mount
  useEffect(() => {
    const restoreSession = async () => {
      const storedToken = localStorage.getItem(TOKEN_KEY);

      if (!storedToken) {
        setIsLoading(false);
        return;
      }

      try {
        const freshUser = await authApi.getMe();

        setUser(freshUser);
        localStorage.setItem(USER_KEY, JSON.stringify(freshUser));
      } catch (err) {
        console.warn("Session restoration failed or token expired:", err);

        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);

        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    void restoreSession();

    // Listen for unauthorized events from Axios interceptor
    const handleUnauthorized = () => {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);

      setUser(null);
      setToken(null);
    };

    window.addEventListener("auth:unauthorized", handleUnauthorized);

    return () => {
      window.removeEventListener("auth:unauthorized", handleUnauthorized);
    };
  }, []);

  const login = async (credentials: LoginRequest): Promise<void> => {
    setIsLoading(true);

    try {
      const resp = await authApi.login(credentials);

      localStorage.setItem(TOKEN_KEY, resp.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(resp.user));

      setToken(resp.access_token);
      setUser(resp.user);
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (data: RegisterRequest): Promise<void> => {
    setIsLoading(true);

    try {
      const resp = await authApi.register(data);

      localStorage.setItem(TOKEN_KEY, resp.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(resp.user));

      setToken(resp.access_token);
      setUser(resp.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);

    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: Boolean(token && user),
        isLoading,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};