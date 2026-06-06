import { Component, signal, inject, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../../services/auth.service';
import { animate, style, transition, trigger } from '@angular/animations';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, LucideAngularModule],
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.css'],
  animations: [
    trigger('fadeInOut', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(-20px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ]),
      transition(':leave', [
        animate('300ms ease-in', style({ opacity: 0, transform: 'translateY(-20px)' }))
      ])
    ])
  ]
})
export class ProfileComponent {
  private authService = inject(AuthService);
  private fb = inject(FormBuilder);

  user = this.authService.user;
  activeTab = signal<string>('informations');
  isEditing = signal<boolean>(false);
  showToast = signal<boolean>(false);
  avatarImage = signal<string | null>(null);
  showPassword = signal<boolean>(false);

  profileData = signal({
    nom: 'Martin',
    prenom: 'Sophie',
    email: 'sophie.m@example.com',
    motDePasse: '********',
    phone: '+216 55 123 456',
    birthDate: '1999-04-15',
    cin: '12345678',
    passport: '',
    country: 'Tunisie',
    sex: 'Femme',
    address: '123 Rue de la République, Tunis',
    lastDiploma: 'Baccalauréat',
    diplomaYear: '2023',
    university: 'ISB',
    desiredDiploma: 'Informatique',
    level: 'L3',
    courseTime: 'Cours de jour',
    knownBy: 'Réseaux sociaux',
    status: 'Actif',
    inscriptionDate: '2024-06-12'
  });

  studentId = '20240156';

  editForm: FormGroup;

  tabs = [
    { id: 'informations', label: 'Informations' },
    { id: 'activite', label: 'Activité récente' },
    { id: 'emails', label: 'Emails générés' }
  ];

  activities = [
    {
      title: 'A posé une question au Chatbot IA',
      description: "Demande d'information sur les inscriptions",
      time: 'Il y a 2 heures',
      icon: 'message-square',
      bg: 'bg-blue-50',
      color: 'text-[#1d4b99]'
    },
    {
      title: 'A généré un email',
      description: "Demande d'attestation de scolarité",
      time: 'Hier à 14:30',
      icon: 'mail',
      bg: 'bg-purple-50',
      color: 'text-purple-500'
    },
    {
      title: 'A consulté la FAQ',
      description: 'Section Inscription',
      time: 'Hier à 10:15',
      icon: 'file-text',
      bg: 'bg-emerald-50',
      color: 'text-emerald-500'
    },
    {
      title: 'A mis à jour son profil',
      description: 'Modification des informations personnelles',
      time: 'Il y a 3 jours',
      icon: 'user',
      bg: 'bg-slate-50',
      color: 'text-slate-400'
    }
  ];

  generatedEmails = [
    { type: 'Attestation de scolarité', recipient: 'Service scolarité', date: '12/06/2024', status: 'Envoyé' },
    { type: 'Demande de stage', recipient: 'Chef de département', date: '10/06/2024', status: 'Envoyé' },
    { type: 'Demande de rattrapage', recipient: 'Enseignant', date: '08/06/2024', status: 'Envoyé' }
  ];

  constructor() {
    const u = this.user();
    if (u) {
      const parts = (u.name || '').split(' ');
      const prenom = parts[0] || this.profileData().prenom;
      const nom = parts.slice(1).join(' ') || this.profileData().nom;
      this.profileData.update(d => ({ ...d, nom, prenom, email: u.email || d.email }));
    }

    this.editForm = this.fb.group({
      nom: [this.profileData().nom],
      prenom: [this.profileData().prenom],
      email: [this.profileData().email],
      motDePasse: [this.profileData().motDePasse],
      phone: [this.profileData().phone],
      birthDate: [this.profileData().birthDate],
      cin: [this.profileData().cin],
      passport: [this.profileData().passport],
      country: [this.profileData().country],
      sex: [this.profileData().sex],
      address: [this.profileData().address],
      lastDiploma: [this.profileData().lastDiploma],
      diplomaYear: [this.profileData().diplomaYear],
      university: [this.profileData().university],
      desiredDiploma: [this.profileData().desiredDiploma],
      level: [this.profileData().level],
      courseTime: [this.profileData().courseTime],
      knownBy: [this.profileData().knownBy]
    });
  }

  initials() {
    return (this.profileData().prenom[0] + this.profileData().nom[0])
      .toUpperCase()
      .slice(0, 2);
  }

  formatDate(dateStr: string) {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('fr-FR');
  }

  setActiveTab(tabId: string) {
    this.activeTab.set(tabId);
  }

  startEdit() {
    this.editForm.patchValue(this.profileData());
    this.isEditing.set(true);
  }

  cancelEdit() {
    this.isEditing.set(false);
  }

  handleSave() {
    if (this.editForm.valid) {
      this.profileData.set(this.editForm.value);
      this.isEditing.set(false);
      this.showToast.set(true);
      setTimeout(() => this.showToast.set(false), 3000);
    }
  }

  handleImageUpload(event: any) {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => {
        this.avatarImage.set(reader.result as string);
        this.authService.updateAvatar(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  }
}
