import { Injectable, signal, effect, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
// import { firstValueFrom } from 'rxjs';                       // ← [STATIC MODE] non utilisé
// import { environment } from '../../environments/environment'; // ← [STATIC MODE] non utilisé

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
  private readonly REGISTERED_USERS_KEY = 'eduportal_registered_users';

  // ─── [STATIC MODE] Comptes de test ──────────────────────────────────────────
  // Pour revenir à l'API réelle : commenter ce bloc et décommenter les imports ci-dessus
  private readonly STATIC_USERS: Record<string, User & { password: string }> = {
    'student@test.com': {
      id: 'stu-001', name: 'Sophie Martin', email: 'student@test.com',
      role: 'student', password: '1234',
      university: 'ISB', field: 'Informatique'
    },
    'admin@test.com': {
      id: 'adm-001', name: 'Admin Principal', email: 'admin@test.com',
      role: 'admin', password: '1234'
    },
    'enseignant@test.com': {
      id: 'ens-001', name: 'Prof. Dupont', email: 'enseignant@test.com',
      role: 'enseignant', password: '1234',
      university: 'IIT', field: 'Génie Logiciel'
    }
  };
  // ────────────────────────────────────────────────────────────────────────────

  // Signals for state
  user = signal<User | null>(null);
  isLoading = signal<boolean>(true);

  constructor() {
    const storedUser = localStorage.getItem(this.STORAGE_KEY);
    if (storedUser) {
      try {
        const parsed: User = JSON.parse(storedUser);
        if (parsed.role === 'enseignant' && !parsed.university) {
          parsed.university = 'IIT';
        }
        this.user.set(parsed);
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

  private getRegisteredUsers(): Record<string, User & { password: string }> {
    try {
      const raw = localStorage.getItem(this.REGISTERED_USERS_KEY);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }

  private saveRegisteredUser(user: User & { password: string }): void {
    const users = this.getRegisteredUsers();
    users[user.email.toLowerCase()] = user;
    localStorage.setItem(this.REGISTERED_USERS_KEY, JSON.stringify(users));
  }

  async login(email: string, password = 'password', fallbackRole: Role = 'student'): Promise<void> {
    this.isLoading.set(true);

    try {
      // ═════════════════════════════════════════════════════════════════════════
      // [STATIC MODE] - Authentification locale sans backend
      // Pour réactiver l'API réelle : commenter ce bloc et décommenter le bloc API ci-dessous
      // ═════════════════════════════════════════════════════════════════════════
      await new Promise(resolve => setTimeout(resolve, 400)); // simulation délai réseau

      const normalizedEmail = email.trim().toLowerCase();
      const registeredUsers = this.getRegisteredUsers();
      const staticUser = registeredUsers[normalizedEmail] || this.STATIC_USERS[normalizedEmail];
      if (!staticUser) {
        throw new Error('Aucun compte trouvé avec cet email.');
      }
      if (staticUser.password !== password) {
        throw new Error('Mot de passe incorrect.');
      }
      const { password: _pwd, ...userWithoutPassword } = staticUser;
      localStorage.setItem(this.TOKEN_KEY, 'static-token-' + staticUser.id);
      this.user.set(userWithoutPassword);
      // ═════════════════════════════════════════════════════════════════════════

      // ─── [API RÉELLE] Décommenter pour connecter au backend ──────────────────
      // const res = await firstValueFrom(
      //   this.http.post<AuthResponse>(`${environment.apiUrl}/auth/login`, {
      //     email,
      //     password
      //   })
      // );
      // if (res && res.access_token) {
      //   localStorage.setItem(this.TOKEN_KEY, res.access_token);
      //   this.user.set(res.user);
      // }
      // ─────────────────────────────────────────────────────────────────────────

    } catch (apiError: any) {
      // ─── [API RÉELLE] Gestion erreurs HTTP ───────────────────────────────────
      // if (apiError.status === 401 || apiError.status === 400 || apiError.status === 403) {
      //   const errorMsg = apiError?.error?.detail || 'Email ou mot de passe incorrect';
      //   throw new Error(errorMsg);
      // }
      // if (apiError.status === 0) {
      //   throw new Error('Impossible de contacter le serveur. Verifiez que le backend est lance.');
      // }
      // throw new Error(apiError?.error?.detail || apiError?.message || 'Identifiants incorrects');
      // ─────────────────────────────────────────────────────────────────────────

      throw new Error(apiError?.message || 'Identifiants incorrects');
    } finally {
      this.isLoading.set(false);
    }
  }

  async register(data: any): Promise<void> {
    this.isLoading.set(true);

    const isTeacher = data.role === 'enseignant';

    try {
      // ═════════════════════════════════════════════════════════════════════════
      // [STATIC MODE] - Inscription locale sans backend
      // Pour réactiver l'API réelle : commenter ce bloc et décommenter le bloc API ci-dessous
      // ═════════════════════════════════════════════════════════════════════════
      await new Promise(resolve => setTimeout(resolve, 500)); // simulation délai réseau

      const normalizedEmail = (data.email || '').trim().toLowerCase();
      const registeredUsers = this.getRegisteredUsers();
      if (this.STATIC_USERS[normalizedEmail] || registeredUsers[normalizedEmail]) {
        throw new Error('Un compte existe déjà avec cet email.');
      }

      const newUser: User = {
        id: 'usr-' + Date.now(),
        name: `${data.prenom || data.firstName || ''} ${data.nom || data.lastName || data.name || 'Nouvel Utilisateur'}`.trim(),
        email: normalizedEmail,
        role: isTeacher ? 'enseignant' : ((data.role as Role) || 'student'),
        university: data.university || 'ISB',
        field: data.field || 'Informatique'
      };
      this.saveRegisteredUser({ ...newUser, password: data.password || '1234' });
      localStorage.setItem(this.TOKEN_KEY, 'static-token-' + newUser.id);
      this.user.set(newUser);
      // ═════════════════════════════════════════════════════════════════════════

      // ─── [API RÉELLE] Décommenter pour connecter au backend ──────────────────
      // const endpoint = isTeacher
      //   ? `${environment.apiUrl}/auth/register-teacher`
      //   : `${environment.apiUrl}/auth/register`;
      // const res = await firstValueFrom(
      //   this.http.post<AuthResponse>(endpoint, data)
      // );
      // if (res && res.access_token) {
      //   localStorage.setItem(this.TOKEN_KEY, res.access_token);
      //   this.user.set(res.user);
      // }
      // ─────────────────────────────────────────────────────────────────────────

    } catch (apiError: any) {
      // ─── [API RÉELLE] Gestion erreurs HTTP ───────────────────────────────────
      // if (apiError.status === 400 || apiError.status === 409 || apiError.status === 422) {
      //   throw new Error(apiError?.error?.detail || "Erreur lors de l'inscription");
      // }
      // if (apiError.status === 0) {
      //   throw new Error('Impossible de contacter le serveur. Verifiez que le backend est lance.');
      // }
      // throw new Error(apiError?.error?.detail || apiError?.message || "Erreur lors de l'inscription");
      // ─────────────────────────────────────────────────────────────────────────

      throw new Error(apiError?.message || "Erreur lors de l'inscription");
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
