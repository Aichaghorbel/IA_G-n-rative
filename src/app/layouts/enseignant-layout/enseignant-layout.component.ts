import { Component, signal, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, RouterLinkActive, RouterLink } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-enseignant-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, RouterLinkActive, RouterLink, LucideAngularModule],
  templateUrl: './enseignant-layout.component.html',
  styles: [`
    .active-link {
      color: #1d4b99 !important;
    }
  `]
})
export class EnseignantLayoutComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  user = this.authService.user;
  teacherUni = computed<'IIT' | 'ISB'>(() => this.user()?.university === 'ISB' ? 'ISB' : 'IIT');
  isMobileMenuOpen = signal<boolean>(false);
  isProfileOpen = signal<boolean>(false);

  navItems = [
    { path: '/enseignant/dashboard', label: 'Tableau de bord' }, { path: '/enseignant/entretiens', label: 'Entretiens' },
    { path: '/enseignant/results', label: 'Résultats QCM' },

    { path: '/enseignant/students', label: 'Profils Candidats' },

  ];

  constructor() { }

  initials() {
    const u = this.user();
    if (!u || !u.name) return 'E';
    return u.name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2);
  }

  toggleMobileMenu() {
    this.isMobileMenuOpen.update(v => !v);
  }

  toggleProfile() {
    this.isProfileOpen.update(v => !v);
  }

  navigateTo(path: string) {
    this.router.navigate([path]);
    this.isProfileOpen.set(false);
  }

  handleLogout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
