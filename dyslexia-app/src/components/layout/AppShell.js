'use client';
import { useUser } from '@/context/UserContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import Sidebar from './Sidebar';

export default function AppShell({ children, fullWidth }) {
  const { isLoggedIn, isInitialized } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (isInitialized && !isLoggedIn) {
      router.push('/login');
    }
  }, [isLoggedIn, isInitialized, router]);

  if (!isInitialized || !isLoggedIn) return null;

  return (
    <>
      <Sidebar />
      <main className="main-content">
        <div className="page-container" style={fullWidth ? { maxWidth: 'none', height: '100vh', display: 'flex', flexDirection: 'column' } : {}}>{children}</div>
      </main>
    </>
  );
}
