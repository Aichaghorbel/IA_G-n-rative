import { Injectable, signal, effect } from '@angular/core';

export type Role = 'student' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  avatar?: string;
  university?: string;
  field?: string;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly STORAGE_KEY = 'eduportal_user';
  
  // Signals for state
  user = signal<User | null>(null);
  isLoading = signal<boolean>(true);

  constructor() {
    // Check local storage on initialization
    const storedUser = localStorage.getItem(this.STORAGE_KEY);
    if (storedUser) {
      try {
        this.user.set(JSON.parse(storedUser));
      } catch (e) {
        console.error('Failed to parse stored user', e);
      }
    }
    this.isLoading.set(false);

    // Effect to sync user state with localStorage
    effect(() => {
      const currentUser = this.user();
      if (currentUser) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(currentUser));
      } else {
        localStorage.removeItem(this.STORAGE_KEY);
      }
    });
  }

  async login(email: string, role: Role): Promise<void> {
    this.isLoading.set(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 800));
    
    const mockUser: User = {
      id: Math.random().toString(36).substring(7),
      name: role === 'admin' ? 'Admin Principal' : 'Jean Dupont',
      email,
      role,
      avatar: `https://ui-avatars.com/api/?name=${email}&background=random`,
      university: role === 'student' ? 'Université de Paris' : undefined,
      field: role === 'student' ? 'Informatique' : undefined
    };
    
    this.user.set(mockUser);
    this.isLoading.set(false);
  }

  async register(data: Partial<User>): Promise<void> {
    this.isLoading.set(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1200));
    
    const newUser: User = {
      id: Math.random().toString(36).substring(7),
      name: data.name || 'Nouvel Étudiant',
      email: data.email || 'etudiant@example.com',
      role: 'student',
      avatar: `https://ui-avatars.com/api/?name=${data.name || 'User'}&background=random`,
      university: data.university,
      field: data.field
    };
    
    this.user.set(newUser);
    this.isLoading.set(false);
  }

  logout(): void {
    this.user.set(null);
  }

  updateAvatar(avatarUrl: string): void {
    this.user.update(u => {
      if (u) {
        return { ...u, avatar: avatarUrl };
      }
      return u;
    });
  }
}
