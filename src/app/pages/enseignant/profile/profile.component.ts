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
  selector: 'app-enseignant-profile',
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
export class EnseignantProfileComponent {
  private authService = inject(AuthService);

  @ViewChild('avatarInput') avatarInput!: ElementRef<HTMLInputElement>;

  isEditing = signal(false);
  activeTab = signal('informations');
  showToast = signal(false);

  private currentUser = this.authService.user();
  private nameParts = (this.currentUser?.name || 'Prof. Dupont').trim().split(/\s+/);
  private initialPrenom = this.nameParts[0] || 'Prof.';
  private initialNom = this.nameParts.slice(1).join(' ') || 'Dupont';

  avatarImage = signal<string | null>(this.currentUser?.avatar || null);

  formData = signal({
    nom: this.initialNom,
    prenom: this.initialPrenom,
    email: this.currentUser?.email || 'enseignant@test.com',
    motDePasse: '********',
    phone: '+216 74 000 000',
    role: 'Enseignant',
    university: this.currentUser?.university === 'ISB' ? 'ISB' : 'IIT',
    department: this.currentUser?.field || 'Génie Logiciel',
    grade: 'Maître-Assistant'
  });

  // Working data for form
  editData = { ...this.formData() };

  initials = computed(() => {
    const p = this.formData().prenom?.[0] || 'E';
    const n = this.formData().nom?.[0] || 'N';
    return (p + n).toUpperCase();
  });

  tabs = [
    { id: 'informations', label: 'Informations' },
    { id: 'activite', label: 'Activité récente' }
  ];

  recentActivities: Activity[] = [
    { id: 1, action: "Entretien d'orientation clôturé", description: 'Compte-rendu enregistré (Avis favorable)', time: 'Il y a 2 heures', icon: 'check-circle', color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { id: 2, action: 'Orientation candidat validée', description: `Filière confirmée (${this.formData().university})`, time: 'Hier à 14:30', icon: 'user-check', color: 'text-[#1d4b99]', bg: 'bg-blue-50' },
    { id: 3, action: 'Consultation des résultats QCM', description: `Analyse des scores par module (${this.formData().university})`, time: 'Il y a 2 jours', icon: 'file-text', color: 'text-purple-600', bg: 'bg-purple-50' },
    { id: 4, action: "Planification d'un entretien", description: 'Créneau fixé en visioconférence', time: 'Il y a 3 jours', icon: 'calendar', color: 'text-amber-600', bg: 'bg-amber-50' }
  ];

  startEditing() {
    this.editData = { ...this.formData() };
    this.isEditing.set(true);
  }

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
    this.authService.user.update(u => u ? {
      ...u,
      name: `${this.editData.prenom} ${this.editData.nom}`.trim(),
      field: this.editData.department
    } : u);
    this.isEditing.set(false);
    this.showToast.set(true);
    setTimeout(() => this.showToast.set(false), 3000);
  }
}
