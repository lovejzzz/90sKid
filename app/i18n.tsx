"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

export type Language = "zh" | "en";

type LanguageContextValue = {
  language: Language;
  setLanguage: (language: Language) => void;
  text: <T,>(zh: T, en: T) => T;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<Language>("en");

  useEffect(() => {
    const saved = window.localStorage.getItem("5279-language");
    // The public site defaults to English; apply a remembered preference after hydration.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (saved === "en" || saved === "zh") setLanguageState(saved);
  }, []);

  const setLanguage = (next: Language) => {
    setLanguageState(next);
    window.localStorage.setItem("5279-language", next);
  };

  useEffect(() => {
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
  }, [language]);

  const value = useMemo<LanguageContextValue>(
    () => ({ language, setLanguage, text: <T,>(zh: T, en: T) => language === "zh" ? zh : en }),
    [language],
  );
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage() {
  const value = useContext(LanguageContext);
  if (!value) throw new Error("useLanguage must be used inside LanguageProvider");
  return value;
}
