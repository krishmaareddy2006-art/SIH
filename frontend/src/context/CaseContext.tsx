import React, { createContext, useContext, useState, useEffect } from 'react';
import { ForensicCase } from '../types';
import { api } from '../services/api';

interface CaseContextType {
  cases: ForensicCase[];
  activeCase: ForensicCase | null;
  setActiveCaseId: (caseId: number) => void;
  refreshCases: () => Promise<void>;
  isLoading: boolean;
}

const CaseContext = createContext<CaseContextType | undefined>(undefined);

export const CaseProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cases, setCases] = useState<ForensicCase[]>([]);
  const [activeCase, setActiveCase] = useState<ForensicCase | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const refreshCases = async () => {
    setIsLoading(true);
    const res = await api.listCases();
    if (res.data) {
      setCases(res.data);
      if (!activeCase && res.data.length > 0) {
        setActiveCase(res.data[0]);
      } else if (activeCase) {
        const updated = res.data.find(c => c.id === activeCase.id);
        if (updated) setActiveCase(updated);
      }
    }
    setIsLoading(false);
  };

  useEffect(() => {
    refreshCases();
  }, []);

  const setActiveCaseId = (caseId: number) => {
    const found = cases.find(c => c.id === caseId);
    if (found) {
      setActiveCase(found);
    }
  };

  return (
    <CaseContext.Provider
      value={{
        cases,
        activeCase,
        setActiveCaseId,
        refreshCases,
        isLoading,
      }}
    >
      {children}
    </CaseContext.Provider>
  );
};

export const useCase = (): CaseContextType => {
  const context = useContext(CaseContext);
  if (!context) {
    throw new Error('useCase must be used within a CaseProvider');
  }
  return context;
};
