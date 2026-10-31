'use client';
import { useState, useRef, useEffect } from 'react';
import { Volume2, Loader2, Square } from 'lucide-react';
import { synthesizeTTS } from '@/lib/api';
import { cleanForTTS } from '@/lib/utils';
import { useAccessibility } from '@/context/AccessibilityContext';

/**
 * TTS Button — Uses Sarvam AI exclusively (no browser fallback).
 * The selected voice from Settings is sent to the backend API.
 */
export default function TTSButton({ text, size = 16 }) {
  const [loading, setLoading] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [error, setError] = useState('');
  const audioRef = useRef(null);
  const { ttsVoice } = useAccessibility();

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const play = async () => {
    // If already playing, stop it
    if (playing) {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
      }
      setPlaying(false);
      return;
    }

    setLoading(true);
    setError('');
    const cleaned = cleanForTTS(text);

    if (!cleaned) {
      setLoading(false);
      return;
    }

    try {
      // Call backend → Sarvam AI TTS
      const res = await synthesizeTTS(cleaned, ttsVoice || 'shubh');

      if (res.success && res.data?.audio) {
        // Decode base64 audio and play
        const bytes = Uint8Array.from(atob(res.data.audio), c => c.charCodeAt(0));
        const blob = new Blob([bytes], { type: 'audio/wav' });
        const url = URL.createObjectURL(blob);

        // Clean up previous audio if any
        if (audioRef.current) {
          audioRef.current.pause();
          URL.revokeObjectURL(audioRef.current.src);
        }

        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => setPlaying(false);
        audio.onerror = () => {
          setPlaying(false);
          setError('Audio playback failed');
        };
        await audio.play();
        setPlaying(true);
      } else {
        setError(res.error || 'TTS failed');
        console.error('Sarvam TTS error:', res.error);
      }
    } catch (e) {
      setError('TTS service unavailable');
      console.error('Sarvam TTS request failed:', e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      className="btn-icon"
      onClick={play}
      title={
        error ? `TTS Error: ${error}` :
        playing ? 'Stop reading' :
        `Read aloud (${ttsVoice || 'shubh'})`
      }
      aria-label={playing ? 'Stop reading' : 'Read aloud'}
      disabled={loading}
      style={error ? { color: 'var(--error)' } : {}}
    >
      {loading
        ? <Loader2 size={size} style={{ animation: 'spin .8s linear infinite' }} />
        : playing
        ? <Square size={size} />
        : <Volume2 size={size} />}
    </button>
  );
}
