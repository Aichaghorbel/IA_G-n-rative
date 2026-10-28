import { Component, signal, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { trigger, transition, animate, style } from '@angular/animations';
import { UniHelpLogoComponent } from '../../../components/uni-help-logo/uni-help-logo.component';
import { AuthLayoutComponent } from '../../../layouts/auth-layout/auth-layout.component';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-register-enseignant',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, LucideAngularModule, UniHelpLogoComponent, AuthLayoutComponent],
  animations: [
    trigger('stepTransition', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateX(20px)' }),
        animate('0.3s ease-out', style({ opacity: 1, transform: 'translateX(0)' }))
      ]),
      transition(':leave', [
        animate('0.3s ease-in', style({ opacity: 0, transform: 'translateX(-20px)' }))
      ])
    ])
  ],
  templateUrl: './register-enseignant.component.html'
})
export class RegisterEnseignantComponent {
  step = signal<number>(1);
  error = signal<string>('');
  isSubmitting = signal<boolean>(false);
  showPassword = signal<boolean>(false);

  // Dropdown visibility signals
  showUniversityDropdown = signal<boolean>(false);
  showDepartmentDropdown = signal<boolean>(false);
  showGradeDropdown = signal<boolean>(false);

  // Search input values
  universitySearch = '';
  departmentSearch = '';
  gradeSearch = '';

  // Options
  universityOptions = ['ISB', 'IIT'];

  departmentsByUniversity: Record<string, string[]> = {
    ISB: [
      'Finance & Ingénierie Financière',
      'Comptabilité & Audit',
      'Management & Ressources Humaines',
      'Marketing Digital & Commercial',
      'Sciences Économiques & Logistique',
      'Droit des Affaires & Droit Privé'
    ],
    IIT: ['Informatique de Gestion & Business Intelligence',

      "Génie Informatique & Systèmes d'Information",
      'Génie Logiciel',
      'Génie Civil',
      'Génie Industriel',
      'Génie Mécanique',
      'Génie des Procédés',
      'Génie des Télécommunications',
      'Architecture',
      'Mathématiques & Sciences Fondamentales'
    ]
  };

  get availableDepartments(): string[] {
    if (this.formData.university && this.departmentsByUniversity[this.formData.university]) {
      return this.departmentsByUniversity[this.formData.university];
    }
    // Si aucune université choisie, proposer tous les départements
    return [
      ...this.departmentsByUniversity['ISB'],
      ...this.departmentsByUniversity['IIT']
    ];
  }

  gradeOptions = [
    "Professeur de l'Enseignement Supérieur",
    'Maître de Conférences',
    'Maître-Assistant',
    'Assistant',
    'Enseignant Vacataire / Expert Professionnel'
  ];

  // Au début : toutes les valeurs sont VIDES
  formData = {
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    phone: '',
    university: '',
    department: '',
    grade: '',
    specialty: ''
  };

  constructor(private authService: AuthService, private router: Router) { }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('[data-combo="university"]')) {
      this.showUniversityDropdown.set(false);
    }
    if (!target.closest('[data-combo="department"]')) {
      this.showDepartmentDropdown.set(false);
    }
    if (!target.closest('[data-combo="grade"]')) {
      this.showGradeDropdown.set(false);
    }
  }

  // Filtered lists
  get filteredUniversityOptions(): string[] {
    const query = this.universitySearch.trim().toLowerCase();
    if (!query) return this.universityOptions;
    return this.universityOptions.filter(u => u.toLowerCase().includes(query));
  }

  get filteredDepartmentOptions(): string[] {
    const list = this.availableDepartments;
    const query = this.departmentSearch.trim().toLowerCase();
    if (!query) return list;
    return list.filter(d => d.toLowerCase().includes(query));
  }

  get filteredGradeOptions(): string[] {
    const query = this.gradeSearch.trim().toLowerCase();
    if (!query) return this.gradeOptions;
    return this.gradeOptions.filter(g => g.toLowerCase().includes(query));
  }

  // Toggle & open handlers
  openUniversityDropdown(e?: Event) {
    if (e) e.stopPropagation();
    this.showDepartmentDropdown.set(false);
    this.showGradeDropdown.set(false);
    this.showUniversityDropdown.set(true);
  }

  openDepartmentDropdown(e?: Event) {
    if (e) e.stopPropagation();
    this.showUniversityDropdown.set(false);
    this.showGradeDropdown.set(false);
    this.showDepartmentDropdown.set(true);
  }

  openGradeDropdown(e?: Event) {
    if (e) e.stopPropagation();
    this.showUniversityDropdown.set(false);
    this.showDepartmentDropdown.set(false);
    this.showGradeDropdown.set(true);
  }

  // Select handlers - zéro effet de bord : aucun autre champ n'est auto-complété
  selectUniversity(option: string) {
    this.formData.university = option;
    this.universitySearch = option;
    this.showUniversityDropdown.set(false);

    // Si le département actuellement choisi n'appartient pas à la nouvelle université choisie, on le réinitialise à vide (sans forcer une fausse valeur)
    const allowed = this.departmentsByUniversity[option] || [];
    if (this.formData.department && !allowed.includes(this.formData.department)) {
      this.formData.department = '';
      this.departmentSearch = '';
    }
  }

  selectDepartment(option: string) {
    this.formData.department = option;
    this.departmentSearch = option;
    this.showDepartmentDropdown.set(false);
  }

  selectGrade(option: string) {
    this.formData.grade = option;
    this.gradeSearch = option;
    this.showGradeDropdown.set(false);
  }

  // Filtrer uniquement les chiffres (maximum 8 chiffres, pas de texte)
  onlyNumbers(event: any, fieldName: keyof typeof this.formData) {
    const input = event.target;
    input.value = input.value.replace(/[^0-9]/g, '').slice(0, 8);
    (this.formData as any)[fieldName] = input.value;
  }

  allowNumbersOnly(event: KeyboardEvent) {
    if (!/[0-9]/.test(event.key)) {
      event.preventDefault();
    }
  }

  get progressPercentage(): number {
    if (this.step() === 2) return 50;
    if (this.step() === 3) return 100;
    return 0;
  }

  handleNext() {
    this.error.set('');

    if (this.step() === 1) {
      if (!this.formData.firstName || !this.formData.lastName || !this.formData.email || !this.formData.password) {
        this.error.set('Veuillez remplir votre nom, prénom, adresse email et mot de passe.');
        return;
      }

      if (this.formData.password.length < 6) {
        this.error.set('Le mot de passe doit contenir au moins 6 caractères.');
        return;
      }

      this.step.set(2);
    }
  }

  handleBack() {
    this.error.set('');
    if (this.step() > 1) {
      this.step.update(s => s - 1);
    }
  }

  async handleSubmit(e?: Event) {
    if (e) e.preventDefault();
    this.error.set('');

    if (!this.formData.university) {
      this.error.set('Veuillez sélectionner un établissement / une université.');
      return;
    }
    if (!this.formData.department) {
      this.error.set("Veuillez sélectionner votre département d'attachement.");
      return;
    }
    if (!this.formData.grade) {
      this.error.set('Veuillez sélectionner votre grade académique.');
      return;
    }
    if (this.formData.phone && this.formData.phone.length !== 8) {
      this.error.set('Le numéro de téléphone doit comporter exactement 8 chiffres.');
      return;
    }

    this.isSubmitting.set(true);

    try {
      const payload = {
        name: `${this.formData.firstName} ${this.formData.lastName}`.trim(),
        firstName: this.formData.firstName,
        lastName: this.formData.lastName,
        email: this.formData.email,
        password: this.formData.password,
        role: 'enseignant',
        university: this.formData.university,
        field: this.formData.department,
        department: this.formData.department,
        phone: this.formData.phone,
        grade: this.formData.grade,
        specialty: this.formData.specialty
      };

      await this.authService.register(payload);
      this.step.set(3);
    } catch (err: any) {
      this.error.set(err?.message || "Une erreur est survenue lors de l'inscription.");
    } finally {
      this.isSubmitting.set(false);
    }
  }

  goToDashboard() {
    this.router.navigate(['/enseignant/dashboard']);
  }
}
