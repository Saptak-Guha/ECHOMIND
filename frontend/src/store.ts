import { create } from 'zustand';

const TOKEN_KEY = 'echomind_token';
const USER_KEY = 'echomind_user';

export interface AuthUser {
  id: string;
  email: string;
  username: string;
  full_name?: string | null;
}

interface AppState {
  sidebarOpen: boolean;
  currentPage: string;
  isLoading: boolean;
  user: AuthUser | null;
  token: string | null;
  dashboardMetrics: any | null;
  toggleSidebar: () => void;
  setCurrentPage: (page: string) => void;
  setLoading: (loading: boolean) => void;
  setUser: (user: AuthUser | null) => void;
  signIn: (token: string, user: AuthUser) => void;
  signOut: () => void;
  setDashboardMetrics: (metrics: any) => void;
}

/** Restore a previous session so a refresh does not log the user out. */
function restoreUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export const useStore = create<AppState>((set) => ({
  sidebarOpen: true,
  currentPage: 'dashboard',
  isLoading: false,
  user: restoreUser(),
  token: localStorage.getItem(TOKEN_KEY),
  dashboardMetrics: null,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setCurrentPage: (page) => set({ currentPage: page }),
  setLoading: (loading) => set({ isLoading: loading }),
  setUser: (user) => {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(USER_KEY);
    set({ user });
  },
  signIn: (token, user) => {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    set({ token, user });
  },
  signOut: () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    // Clear cached twin data so the next account never sees the previous one's.
    set({ token: null, user: null, dashboardMetrics: null });
  },
  setDashboardMetrics: (metrics) => set({ dashboardMetrics: metrics }),
}));
