import { Component, signal, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule, ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { trigger, transition, animate, style } from '@angular/animations';
import { UniHelpLogoComponent } from '../../../components/uni-help-logo/uni-help-logo.component';
import { AuthService } from '../../../services/auth.service';
import { OrientationService } from '../../../services/orientation.service';

@Component({
  selector: 'app-preinscription',
  standalone: true,
  imports: [CommonModule, RouterModule, FormsModule, LucideAngularModule, UniHelpLogoComponent],
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
  templateUrl: './preinscription.component.html'
})
export class PreinscriptionComponent implements OnInit {
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private authService = inject(AuthService);
  private orientationService = inject(OrientationService);

  step = signal<number>(1);
  error = signal<string>('');
  isSubmitting = signal<boolean>(false);

  showCountryDropdown = signal<boolean>(false);
  showSexDropdown = signal<boolean>(false);
  showLastDiplomaDropdown = signal<boolean>(false);
  showUniversityDropdown = signal<boolean>(false);
  showDesiredDiplomaDropdown = signal<boolean>(false);
  showLevelDropdown = signal<boolean>(false);
  showCourseTimeDropdown = signal<boolean>(false);
  showKnownByDropdown = signal<boolean>(false);

  countrySearch = '';
  sexSearch = '';
  lastDiplomaSearch = '';
  universitySearch = '';
  desiredDiplomaSearch = '';
  levelSearch = '';
  courseTimeSearch = '';
  knownBySearch = '';

  sexOptions = ['Homme', 'Femme'];
  diplomaOptions = ['Baccalauréat', 'Prépa', 'Licence', 'Master'];
  universityOptions = ['ISB', 'IIT'];
  levelOptions = ['1', '2', '3'];
  courseTimeOptions = ['Cours de jour', 'Cours de soir'];
  knownByOptions = [
    { label: 'Réseaux sociaux', icon: 'globe' },
    { label: 'Amis / Parents', icon: 'users' },
    { label: 'Site web', icon: 'globe' },
    { label: 'SMS', icon: 'message-square' },
    { label: 'Press', icon: 'file-text' },
    { label: 'Foire', icon: 'building' },
    { label: 'Tourné Lycée', icon: 'map-pin' },
    { label: 'Événement', icon: 'calendar' },
    { label: 'Email', icon: 'mail' },
    { label: 'Radio/TV', icon: 'megaphone' },
    { label: 'Autre', icon: 'plus' },
  ];

  formData = {
    firstName: '',
    lastName: '',
    email: '',
    cinPassport: '',
    country: '',
    birthDate: '',
    sex: '',
    phone: '',
    address: '',
    lastDiploma: '',
    diplomaYear: '',
    university: 'IIT',
    desiredDiploma: '',
    level: '1',
    courseTime: 'Cours de jour',
    knownBy: 'Site web',
  };

  countries = [
    'Tunisie', 'France', 'Algérie', 'Maroc', 'Canada', 'Allemagne', 'Belgique',
    'Côte d’Ivoire', 'Sénégal', 'Cameroun', 'Italie', 'Espagne', 'États-Unis'
  ];

  desiredDiplomas = [
    { type: 'header', text: 'Cycle Ingénieur' },
    { type: 'item', text: 'Architecture' },
    { type: 'item', text: 'Ingénierie' },
    { type: 'item', text: 'Cycle Préparatoire' },
    { type: 'item', text: 'Génie Logiciel & Informatique' },
    { type: 'item', text: 'Génie Civil' },
    { type: 'item', text: 'Génie Mécanique & Robotique' },
    { type: 'header', text: 'Licence & Master' },
    { type: 'item', text: 'Licence en Technologie & Informatique' },
    { type: 'item', text: 'Finance, Banque & Fintech' },
    { type: 'item', text: 'Marketing Digital & E-Commerce' },
    { type: 'item', text: 'Business Analytics & Big Data' }
  ];

  ngOnInit() {
    // Pré-remplir si connecté
    const u = this.authService.user();
    if (u) {
      if (u.name) {
        const parts = u.name.split(' ');
        this.formData.firstName = parts[0] || '';
        this.formData.lastName = parts.slice(1).join(' ') || '';
      }
      this.formData.email = u.email || '';
    }

    // Récupérer parcours sélectionné dans l'URL si présent
    this.route.queryParams.subscribe(params => {
      if (params['filiere']) {
        this.formData.desiredDiploma = params['filiere'];
        this.desiredDiplomaSearch = params['filiere'];
      }
      if (params['uni']) {
        this.formData.university = params['uni'];
        this.universitySearch = params['uni'];
      }
    });
  }

  get progressPercentage(): number {
    return Math.round(((this.step() - 1) / 3) * 100);
  }

  onlyNumbers(event: any, field: string) {
    const value = event.target.value.replace(/[^0-9]/g, '');
    (this.formData as any)[field] = value;
  }

  selectCountry(country: string) {
    this.countrySearch = country;
    this.formData.country = country;
    this.showCountryDropdown.set(false);
  }

  get filteredCountries() {
    return this.countries.filter(c => c.toLowerCase().includes(this.countrySearch.toLowerCase()));
  }

  selectSex(sex: string) {
    this.sexSearch = sex;
    this.formData.sex = sex;
    this.showSexDropdown.set(false);
  }

  get filteredSexOptions() {
    return this.sexOptions.filter(s => s.toLowerCase().includes(this.sexSearch.toLowerCase()));
  }

  selectLastDiploma(diploma: string) {
    this.lastDiplomaSearch = diploma;
    this.formData.lastDiploma = diploma;
    this.showLastDiplomaDropdown.set(false);
  }

  get filteredLastDiplomaOptions() {
    return this.diplomaOptions.filter(d => d.toLowerCase().includes(this.lastDiplomaSearch.toLowerCase()));
  }

  selectUniversity(uni: string) {
    this.universitySearch = uni;
    this.formData.university = uni;
    this.showUniversityDropdown.set(false);
  }

  get filteredUniversityOptions() {
    return this.universityOptions.filter(u => u.toLowerCase().includes(this.universitySearch.toLowerCase()));
  }

  selectDesiredDiploma(diploma: string) {
    this.desiredDiplomaSearch = diploma;
    this.formData.desiredDiploma = diploma;
    this.showDesiredDiplomaDropdown.set(false);
  }

  get filteredDesiredDiplomaOptions() {
    return this.desiredDiplomas.filter(d => d.text.toLowerCase().includes(this.desiredDiplomaSearch.toLowerCase()));
  }

  selectLevel(level: string) {
    this.levelSearch = level;
    this.formData.level = level;
    this.showLevelDropdown.set(false);
  }

  get filteredLevelOptions() {
    return this.levelOptions.filter(l => l.toLowerCase().includes(this.levelSearch.toLowerCase()));
  }

  selectCourseTime(course: string) {
    this.courseTimeSearch = course;
    this.formData.courseTime = course;
    this.showCourseTimeDropdown.set(false);
  }

  get filteredCourseTimeOptions() {
    return this.courseTimeOptions.filter(c => c.toLowerCase().includes(this.courseTimeSearch.toLowerCase()));
  }

  selectKnownBy(knownBy: string) {
    this.knownBySearch = knownBy;
    this.formData.knownBy = knownBy;
    this.showKnownByDropdown.set(false);
  }

  get filteredKnownByOptions() {
    return this.knownByOptions.filter(k => k.label.toLowerCase().includes(this.knownBySearch.toLowerCase()));
  }

  validateStep(): boolean {
    this.error.set('');
    if (this.step() === 1) {
      if (!this.formData.firstName || !this.formData.lastName || !this.formData.email) {
        this.error.set('Veuillez renseigner votre nom, prénom et email.');
        return false;
      }
    } else if (this.step() === 2) {
      if (!this.formData.lastDiploma) {
        this.error.set('Veuillez sélectionner votre dernier diplôme.');
        return false;
      }
    } else if (this.step() === 3) {
      if (!this.formData.desiredDiploma) {
        this.error.set('Veuillez choisir le diplôme souhaité.');
        return false;
      }
    }
    return true;
  }

  handleNext() {
    if (this.validateStep()) {
      this.step.update(s => s + 1);
    }
  }

  handleBack() {
    this.error.set('');
    this.step.update(s => Math.max(1, s - 1));
  }

  async handleSubmit(e: Event) {
    e.preventDefault();
    if (!this.validateStep()) return;

    this.isSubmitting.set(true);
    try {
      this.orientationService.enregistrerPreinscription({
        nom: `${this.formData.firstName} ${this.formData.lastName}`.trim(),
        email: this.formData.email,
        phone: this.formData.phone || '+216 00 000 000',
        bac: this.formData.lastDiploma || 'Baccalauréat',
        universite: (this.formData.university === 'ISB' ? 'ISB' : 'IIT'),
        filiere: this.formData.desiredDiploma
      });

      // Passer à l'étape finale de confirmation
      this.step.set(4);
    } catch (err) {
      this.error.set('Une erreur est survenue lors de l’enregistrement de votre préinscription.');
    } finally {
      this.isSubmitting.set(false);
    }
  }

  commencerQCM() {
    this.router.navigate(['/student/qcm']);
  }
}

