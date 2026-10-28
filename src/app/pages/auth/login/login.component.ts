import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule, Mail, Lock, Loader2 } from 'lucide-angular';
import { UniHelpLogoComponent } from '../../../components/uni-help-logo/uni-help-logo.component';
import { AuthService, Role } from '../../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, LucideAngularModule, UniHelpLogoComponent],
  templateUrl: './login.component.html'
})
export class LoginComponent {
  email = '';
  password = '';
  error = signal<string>('');
  isSubmitting = signal<boolean>(false);
  showPassword = signal<boolean>(false);

  constructor(private authService: AuthService, private router: Router) {}

  detectRole(email: string): Role {
    const lower = email.toLowerCase();
    if (lower.includes('@admin') || lower.includes('admin')) {
      return 'admin';
    }
    if (lower.includes('@enseignant') || lower.includes('enseignant') || lower.includes('@prof') || lower.includes('prof')) {
      return 'enseignant';
    }
    return 'student';
  }

  async handleSubmit(e?: Event) {
    if (e) e.preventDefault();
    this.error.set('');

    if (!this.email || !this.password) {
      this.error.set('Veuillez remplir tous les champs.');
      return;
    }

    this.isSubmitting.set(true);
    try {
      await this.authService.login(this.email, this.password);
      const user = this.authService.user();
      const role = user?.role || this.detectRole(this.email);

      if (role === 'student') {
        this.router.navigate(['/student/dashboard']);
      } else if (role === 'enseignant') {
        this.router.navigate(['/enseignant/dashboard']);
      } else {
        this.router.navigate(['/admin/dashboard']);
      }
    } catch (err: any) {
      this.error.set(err?.message || 'Email ou mot de passe incorrect.');
    } finally {
      this.isSubmitting.set(false);
    }
  }
}
