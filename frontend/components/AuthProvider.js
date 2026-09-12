"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api, errorMessage } from "../lib/api";

const STORAGE_KEY = "crewlink.token";
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      setReady(true);
      return;
    }
    api("/api/auth/me/", { token: stored }).then(({ ok, data }) => {
      if (ok) {
        setToken(stored);
        setUser(data);
      } else {
        window.localStorage.removeItem(STORAGE_KEY);
      }
      setReady(true);
    });
  }, []);

  const value = useMemo(
    () => ({
      ready,
      token,
      user,
      async login(email, password) {
        const { ok, status, data } = await api("/api/auth/login/", {
          method: "POST",
          body: { email, password },
        });
        if (!ok) {
          throw new Error(errorMessage(data, status));
        }
        window.localStorage.setItem(STORAGE_KEY, data.token);
        setToken(data.token);
        setUser(data.user);
        return data.user;
      },
      async logout() {
        if (token) {
          await api("/api/auth/logout/", { method: "POST", token });
        }
        window.localStorage.removeItem(STORAGE_KEY);
        setToken(null);
        setUser(null);
      },
    }),
    [ready, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
