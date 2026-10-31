'use client';
import { createContext, useContext, useReducer, useEffect, useState } from 'react';

const UserContext = createContext(null);

const initialState = {
  isLoggedIn: false,
  userId: '',
  name: '',
  role: '', // 'student' or 'parent'
  parentLinkedStudentId: '',
};

function reducer(state, action) {
  switch (action.type) {
    case 'LOGIN':
      return { ...state, isLoggedIn: true, ...action.payload };
    case 'LOGOUT':
      return { ...initialState };
    case 'SET_NAME':
      return { ...state, name: action.payload };
    default:
      return state;
  }
}

export function UserProvider({ children }) {
  // Always start with initialState so server and client initial renders are identical.
  // Restoring from localStorage in useEffect (after hydration) prevents the hydration
  // mismatch caused by reading localStorage synchronously inside the reducer initializer.
  const [state, dispatch] = useReducer(reducer, initialState);
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    // Restore persisted session on the client after hydration
    try {
      const saved = localStorage.getItem('dyslexia_user');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed?.isLoggedIn) {
          dispatch({ type: 'LOGIN', payload: parsed });
        }
      }
    } catch { /* corrupted storage — ignore */ }
    setIsInitialized(true);
  }, []); // run once on mount

  const login = (userId, name, role, parentLinkedStudentId = '') => {
    const payload = { userId, name, role, parentLinkedStudentId };
    dispatch({ type: 'LOGIN', payload });
    localStorage.setItem('dyslexia_user', JSON.stringify({ isLoggedIn: true, ...payload }));
  };

  const logout = () => {
    dispatch({ type: 'LOGOUT' });
    localStorage.removeItem('dyslexia_user');
  };

  const effectiveUserId = state.role === 'parent' ? state.parentLinkedStudentId : state.userId;

  return (
    <UserContext.Provider value={{ ...state, isInitialized, effectiveUserId, login, logout, dispatch }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error('useUser must be used within UserProvider');
  return ctx;
}
