import React, { createContext, useContext, useState, useEffect } from 'react';
import { ForensicCase } from '../types';
import { api } from '../services/api';

import { useAuth } from './AuthContext';

interface CaseContextType {
  cases: ForensicCase[];
  activeCase: ForensicCase | null;
  setActiveCaseId: (caseId: number) => void;
  refreshCases: () => Promise<void>;
  isLoading: boolean;
}

const CaseContext = createContext<CaseContextType | undefined>(undefined);

export const CaseProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [cases, setCases] = useState<ForensicCase[]>([]);
  const [activeCase, setActiveCase] = useState<ForensicCase | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const refreshCases = async () => {
    setIsLoading(true);
    const res = await api.listCases();
    if (res.data) {
      const caseList = res.data;
      setCases(caseList);
      setActiveCase(prev => {
        if (!prev && caseList.length > 0) return caseList[0];
        if (prev) {
          const updated = caseList.find(c => c.id === prev.id);
          return updated || caseList[0] || null;
        }
        return null;
      });
    }
    setIsLoading(false);
  };

  useEffect(() => {
    if (isAuthenticated) {
      refreshCases();
    } else {
      setCases([]);
      setActiveCase(null);
    }
  }, [isAuthenticated]);

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
