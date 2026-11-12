import { Component, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, RouterLinkActive, RouterLink, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../services/auth.service';
import { OrientationService, NotificationCandidat } from '../../services/orientation.service';
import { ChatbotFabComponent } from '../../components/chatbot-fab/chatbot-fab.component';

@Component({
  selector: 'app-student-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, RouterLinkActive, RouterLink, LucideAngularModule, ChatbotFabComponent],
  templateUrl: './student-layout.component.html',
  styles: [`
    .active-link {
      color: #1d4b99 !important;
    }
  `]
})
export class StudentLayoutComponent {
  private authService = inject(AuthService);
  private orientationService = inject(OrientationService);
  private router = inject(Router);

  user = this.authService.user;
  isMobileMenuOpen = signal<boolean>(false);
  isProfileOpen = signal<boolean>(false);
  isNotifsOpen = signal<boolean>(false);

  selectedEntretienModal = this.orientationService.selectedEntretienModal;

  currentUrl = signal<string>(this.router.url);
  isFullWidth = computed(() => {
    return this.currentUrl().includes('/preinscription');
  });

  notifications = this.orientationService.notifications;
  unreadCount = () => this.notifications().filter(n => !n.lue).length;

  navItems: Array<{ path: string; label: string; icon?: string }> = [
    { path: '/student/dashboard', label: 'Tableau de bord' },
    { path: '/student/parcours', label: 'Parcours' },
  ];

  constructor() {
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd)
    ).subscribe((e) => {
      this.currentUrl.set(e.urlAfterRedirects || e.url);
    });
  }

  initials() {
    const u = this.user();
    if (!u || !u.name) return 'U';
    return u.name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2);
  }

  toggleMobileMenu() {
    this.isMobileMenuOpen.update(v => !v);
  }

  toggleProfile() {
    this.isProfileOpen.update(v => !v);
    this.isNotifsOpen.set(false);
  }

  toggleNotifs() {
    this.isNotifsOpen.update(v => !v);
    this.isProfileOpen.set(false);
    if (this.isNotifsOpen()) {
      this.orientationService.marquerToutesNotifsLues();
    }
  }

  navigateTo(path: string) {
    this.router.navigate([path]);
    this.isProfileOpen.set(false);
    this.isNotifsOpen.set(false);
  }

  handleNotifClick(notif: NotificationCandidat) {
    this.isNotifsOpen.set(false);
    const titreLower = notif.titre.toLowerCase();
    const msgLower = notif.message.toLowerCase();

    if (notif.type === 'rdv' || titreLower.includes('entretien') || msgLower.includes('entretien') || msgLower.includes('rendez-vous')) {
      this.orientationService.ouvrirModalEntretien();
    } else if (notif.type === 'qcm' || titreLower.includes('qcm')) {
      this.router.navigate(['/student/qcm']);
    } else if (notif.type === 'orientation') {
      this.router.navigate(['/student/dashboard']);
    }
  }

  fermerModalEntretien() {
    this.orientationService.fermerModalEntretien();
  }

  handleLogout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
