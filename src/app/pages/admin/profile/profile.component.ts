import { Component, signal, computed, inject, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../../services/auth.service';
import { animate, style, transition, trigger, state } from '@angular/animations';

interface Activity {
  id: number;
  action: string;
  description: string;
  time: string;
  icon: string;
  color: string;
  bg: string;
}

@Component({
  selector: 'app-admin-profile',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './profile.component.html',
  animations: [
    trigger('toastAnimation', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(-20px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ]),
      transition(':leave', [
        animate('300ms ease-in', style({ opacity: 0, transform: 'translateY(-20px)' }))
      ])
    ]),
    trigger('tabTransition', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class AdminProfileComponent {
  private authService = inject(AuthService);

  @ViewChild('avatarInput') avatarInput!: ElementRef<HTMLInputElement>;

  isEditing = signal(false);
  activeTab = signal('informations');
  showToast = signal(false);
  avatarImage = signal<string | null>(null);

  formData = signal({
    nom: 'Principal',
    prenom: 'Admin',
    email: 'admin@unihelp.tn',
    motDePasse: '********',
    phone: '+216 71 123 456',
    role: 'Super Administrateur',
    department: 'Direction Générale'
  });

  // Working data for form
  editData = { ...this.formData() };

  initials = computed(() => {
    return (this.formData().prenom[0] + this.formData().nom[0]).toUpperCase().slice(0, 2);
  });

  tabs = [
    { id: 'informations', label: 'Informations' },
    { id: 'activite', label: 'Activité récente' }
  ];

  recentActivities: Activity[] = [
    { id: 1, action: "Ajout d'un nouveau document", description: 'Règlement intérieur 2023-2024', time: 'Il y a 2 heures', icon: 'file-text', color: 'text-blue-500', bg: 'bg-blue-50' },
    { id: 2, action: "Validation d'un étudiant", description: 'Sophie Martin - Informatique L3', time: 'Hier à 14:30', icon: 'users', color: 'text-emerald-500', bg: 'bg-emerald-50' },
    { id: 3, action: 'Modification des paramètres', description: 'Mise à jour des permissions', time: 'Il y a 2 jours', icon: 'settings', color: 'text-slate-500', bg: 'bg-slate-50' },
    { id: 4, action: "Suppression d'un administrateur", description: 'Jean Dupont - Accès révoqué', time: 'Il y a 3 jours', icon: 'shield', color: 'text-red-500', bg: 'bg-red-50' }
  ];

  onAvatarChange(event: any) {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e: any) => {
        this.avatarImage.set(e.target.result);
        this.authService.updateAvatar(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  }

  handleSave() {
    this.formData.set({ ...this.editData });
    this.isEditing.set(false);
    this.showToast.set(true);
    setTimeout(() => this.showToast.set(false), 3000);
  }
}
