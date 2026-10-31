'use client';
import { createContext, useContext, useReducer, useEffect } from 'react';

const A11yContext = createContext(null);

const defaults = {
  fontFamily: 'normal',
  fontSize: 1.125,
  lineHeight: 1.8,
  letterSpacing: 0.03,
  highContrast: false,
  ttsVoice: 'shubh',
};

function reducer(state, action) {
  switch (action.type) {
    case 'SET': return { ...state, [action.key]: action.value };
    case 'RESET': return { ...defaults };
    case 'LOAD': return { ...defaults, ...action.payload };
    default: return state;
  }
}

export function AccessibilityProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, defaults, () => {
    if (typeof window === 'undefined') return defaults;
    const saved = localStorage.getItem('dyslexia_a11y');
    return saved ? { ...defaults, ...JSON.parse(saved) } : defaults;
  });

  useEffect(() => {
    localStorage.setItem('dyslexia_a11y', JSON.stringify(state));
    // Fallback migration for existing users
    if (state.dyslexiaFont !== undefined) {
      const newFont = state.dyslexiaFont ? 'opendyslexic' : 'normal';
      dispatch({ type: 'SET', key: 'fontFamily', value: newFont });
      dispatch({ type: 'SET', key: 'dyslexiaFont', value: undefined });
    }
    // Migrate old 'dyslexie' (proprietary) → 'atkinson' (open-source replacement)
    if (state.fontFamily === 'dyslexie') {
      dispatch({ type: 'SET', key: 'fontFamily', value: 'atkinson' });
    }
    document.documentElement.setAttribute('data-font', state.fontFamily || 'normal');
    document.documentElement.style.setProperty('--fs-base', `${state.fontSize}rem`);
    document.documentElement.style.setProperty('--lh', `${state.lineHeight}`);
    document.documentElement.style.setProperty('--ls', `${state.letterSpacing}em`);
  }, [state]);

  const set = (key, value) => dispatch({ type: 'SET', key, value });
  const reset = () => dispatch({ type: 'RESET' });

  return (
    <A11yContext.Provider value={{ ...state, set, reset }}>
      {children}
    </A11yContext.Provider>
  );
}

export function useAccessibility() {
  const ctx = useContext(A11yContext);
  if (!ctx) throw new Error('useAccessibility must be used within AccessibilityProvider');
  return ctx;
}
