import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { animate, style, transition, trigger, state } from '@angular/animations';

interface Language {
  id: string;
  label: string;
  flag: string;
}

@Component({
  selector: 'app-admin-settings',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './settings.component.html',
  animations: [
    trigger('scaleIn', [
      transition(':enter', [
        style({ transform: 'scale(0)' }),
        animate('200ms ease-out', style({ transform: 'scale(1)' }))
      ])
    ]),
    trigger('fadeIn', [
      transition(':enter', [
        style({ opacity: 0 }),
        animate('300ms ease-out', style({ opacity: 1 }))
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({ opacity: 0 }))
      ])
    ]),
    trigger('modalAnimation', [
      transition(':enter', [
        style({ opacity: 0, transform: 'scale(0.9) translateY(30px)' }),
        animate('400ms cubic-bezier(0.34, 1.56, 0.64, 1)', style({ opacity: 1, transform: 'scale(1) translateY(0)' }))
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({ opacity: 0, transform: 'scale(0.9) translateY(30px)' }))
      ])
    ])
  ]
})
export class AdminSettingsComponent {
  selectedLang = signal<string>('fr');
  isDarkMode = signal<boolean>(false);
  isAboutModalOpen = signal<boolean>(false);

  languages: Language[] = [
    { id: 'fr', label: 'Français', flag: '🇫🇷' },
    { id: 'en', label: 'English', flag: '🇬🇧' },
    { id: 'ar', label: 'العربية', flag: '🇹🇳' }
  ];

  setSelectedLang(id: string) {
    this.selectedLang.set(id);
  }

  toggleDarkMode() {
    this.isDarkMode.update(v => !v);
  }

  openAbout() {
    this.isAboutModalOpen.set(true);
  }

  closeAbout() {
    this.isAboutModalOpen.set(false);
  }
}
