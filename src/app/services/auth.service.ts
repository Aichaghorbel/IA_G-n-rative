import { Injectable, signal, effect, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';

export type Role = 'student' | 'admin' | 'enseignant';

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  avatar?: string;
  university?: string;
  field?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private readonly STORAGE_KEY = 'eduportal_user';
  private readonly TOKEN_KEY = 'unihelp_token';
  
  // Signals for state
  user = signal<User | null>(null);
  isLoading = signal<boolean>(true);

  constructor() {
    const storedUser = localStorage.getItem(this.STORAGE_KEY);
    if (storedUser) {
      try {
        this.user.set(JSON.parse(storedUser));
      } catch (e) {
        console.error('Failed to parse stored user', e);
      }
    }
    this.isLoading.set(false);

    effect(() => {
      const currentUser = this.user();
      if (currentUser) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(currentUser));
      } else {
        localStorage.removeItem(this.STORAGE_KEY);
        localStorage.removeItem(this.TOKEN_KEY);
      }
    });
  }

  async login(email: string, password = 'password', fallbackRole: Role = 'student'): Promise<void> {
    this.isLoading.set(true);

    try {
      const res = await firstValueFrom(
        this.http.post<AuthResponse>(`${environment.apiUrl}/auth/login`, {
          email,
          password
        })
      );

      if (res && res.access_token) {
        localStorage.setItem(this.TOKEN_KEY, res.access_token);
        this.user.set(res.user);
      }
    } catch (apiError: any) {
      if (apiError.status === 401 || apiError.status === 400 || apiError.status === 403) {
        const errorMsg = apiError?.error?.detail || 'Email ou mot de passe incorrect';
        throw new Error(errorMsg);
      }

      if (apiError.status === 0) {
        throw new Error('Impossible de contacter le serveur. Vérifiez que le backend est lancé.');
      }

      throw new Error(apiError?.error?.detail || apiError?.message || 'Identifiants incorrects');
    } finally {
      this.isLoading.set(false);
    }
  }

  async register(data: any): Promise<void> {
    this.isLoading.set(true);

    const isTeacher = data.role === 'enseignant';
    const endpoint = isTeacher ? `${environment.apiUrl}/auth/register-teacher` : `${environment.apiUrl}/auth/register`;

    try {
      const res = await firstValueFrom(
        this.http.post<AuthResponse>(endpoint, data)
      );

      if (res && res.access_token) {
        localStorage.setItem(this.TOKEN_KEY, res.access_token);
        this.user.set(res.user);
      }
    } catch (apiError: any) {
      if (apiError.status === 400 || apiError.status === 409 || apiError.status === 422) {
        throw new Error(apiError?.error?.detail || 'Erreur lors de l’inscription');
      }

      if (apiError.status === 0) {
        throw new Error('Impossible de contacter le serveur. Vérifiez que le backend est lancé.');
      }

      throw new Error(apiError?.error?.detail || apiError?.message || 'Erreur lors de l’inscription');
    } finally {
      this.isLoading.set(false);
    }
  }

  logout(): void {
    localStorage.removeItem(this.TOKEN_KEY);
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
