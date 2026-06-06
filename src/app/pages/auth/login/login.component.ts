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
    if (email.includes('@admin') || email.toLowerCase().includes('admin')) {
      return 'admin';
    }
    return 'student';
  }

  async handleSubmit(e: Event) {
    e.preventDefault();
    this.error.set('');

    if (!this.email || !this.password) {
      this.error.set('Veuillez remplir tous les champs.');
      return;
    }

    this.isSubmitting.set(true);
    try {
      const role = this.detectRole(this.email);
      await this.authService.login(this.email, role);
      if (role === 'student') {
        this.router.navigate(['/student/dashboard']);
      } else {
        this.router.navigate(['/admin/dashboard']);
      }
    } catch (err) {
      this.error.set('Identifiants incorrects. Veuillez réessayer.');
    } finally {
      this.isSubmitting.set(false);
    }
  }
}
