export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const TTS_VOICES = [
  { id: 'shubh', label: 'Shubh (Male)' },
  { id: 'aditya', label: 'Aditya (Male)' },
  { id: 'ritu', label: 'Ritu (Female)' },
  { id: 'priya', label: 'Priya (Female)' },
  { id: 'kavya', label: 'Kavya (Female)' },
];

export const MOOD_COLORS = {
  happy: { bg: '#E8F5E9', text: '#2E7D32', border: '#4CAF82' },
  joy: { bg: '#E8F5E9', text: '#2E7D32', border: '#4CAF82' },
  neutral: { bg: '#E8EAF6', text: '#3949AB', border: '#6366F1' },
  stressed: { bg: '#FFF3E0', text: '#E65100', border: '#F5A623' },
  fear: { bg: '#FFF3E0', text: '#E65100', border: '#F5A623' },
  frustrated: { bg: '#FCE4EC', text: '#C62828', border: '#F47B6E' },
  anger: { bg: '#FCE4EC', text: '#C62828', border: '#F47B6E' },
  sadness: { bg: '#F3E5F5', text: '#6A1B9A', border: '#7C5CFC' },
  surprise: { bg: '#E0F7FA', text: '#00695C', border: '#22D3EE' },
  disgust: { bg: '#EFEBE9', text: '#4E342E', border: '#8D6E63' },
};

export const DIFFICULTY_COLORS = {
  easy: { bg: '#E8F5E9', text: '#2E7D32' },
  medium: { bg: '#FFF3E0', text: '#E65100' },
  hard: { bg: '#FCE4EC', text: '#C62828' },
};
