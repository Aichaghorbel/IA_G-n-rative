import { Component, inject, signal, computed, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { animate, style, transition, trigger } from '@angular/animations';
import { OrientationService, Entretien, CandidatOrientation } from '../../../services/orientation.service';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-entretiens',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './entretiens.component.html',
  animations: [
    trigger('fadeIn', [
      transition(':enter', [style({ opacity: 0 }), animate('200ms ease-out', style({ opacity: 1 }))]),
      transition(':leave', [animate('200ms ease-in', style({ opacity: 0 }))])
    ]),
    trigger('modalSlide', [
      transition(':enter', [
        style({ transform: 'scale(0.95) translateY(20px)', opacity: 0 }),
        animate('300ms cubic-bezier(0.34, 1.56, 0.64, 1)', style({ transform: 'scale(1) translateY(0)', opacity: 1 }))
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({ transform: 'scale(0.95) translateY(20px)', opacity: 0 }))
      ])
    ])
  ]
})
export class EntretiensComponent implements OnInit {
  private orientationService = inject(OrientationService);
  private authService = inject(AuthService);
  private route = inject(ActivatedRoute);

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      if (params['statut'] === 'Planifié' || params['statut'] === 'Terminé') {
        this.statutFilter.set(params['statut']);
        this.currentPage.set(1);
      }
    });
  }

  user = this.authService.user;
  teacherUni = computed<'IIT' | 'ISB'>(() =>
    this.authService.user()?.university === 'ISB' ? 'ISB' : 'IIT'
  );
  entretiens = this.orientationService.entretiens;
  allCandidats = this.orientationService.candidats;
  candidats = computed(() =>
    this.allCandidats().filter(c => c.universiteSouhaitee === this.teacherUni())
  );

  // Search & Filter state
  searchQuery = signal<string>('');
  statutFilter = signal<string>('TOUS');
  avisFilter = signal<string>('TOUS');
  isFilterOpen = signal<boolean>(false);

  // Pagination state (identique à students)
  currentPage = signal<number>(1);
  itemsPerPage = 6;

  // Modal Planifier (champs initialement vides)
  isPlanifierModalOpen = signal<boolean>(false);
  selectedCandidatForPlanif = signal<CandidatOrientation | null>(null);
  formDate = '';
  formHeure = '';
  formFormat = signal<'Présentiel' | 'Visio'>('Présentiel');
  formSalle = '';
  formLienVisio = '';

  setFormat(fmt: 'Présentiel' | 'Visio') {
    this.formFormat.set(fmt);
  }

  isVisio(lieu: string): boolean {
    if (!lieu) return false;
    const l = lieu.toLowerCase();
    return l.includes('http') || l.includes('meet') || l.includes('zoom') || l.includes('teams') || l.includes('visio');
  }

  // Modal Mener Entretien / Compte-rendu
  isMenerModalOpen = signal<boolean>(false);
  entretienEnCours = signal<Entretien | null>(null);
  isReadOnly = computed(() => this.entretienEnCours()?.statut === 'Terminé');
  formAvis = signal<'Favorable' | 'Défavorable'>('Favorable');
  formNotes = '';
  formOrientationFinale = '';

  filteredEntretiens = computed(() => {
    const q = this.searchQuery().toLowerCase().trim();
    const st = this.statutFilter();
    const av = this.avisFilter();
    const uni = this.teacherUni();
    const allowedIds = new Set(this.candidats().map(c => c.id));

    return this.entretiens().filter(e => {
      const cand = this.allCandidats().find(c => c.id === e.candidatId);
      if (cand && cand.universiteSouhaitee !== uni) return false;
      if (!cand && !allowedIds.has(e.candidatId) && !e.salleOuLien.toUpperCase().includes(uni)) return false;

      const matchSearch = !q ||
        e.candidatNom.toLowerCase().includes(q) ||
        e.candidatEmail.toLowerCase().includes(q) ||
        e.salleOuLien.toLowerCase().includes(q);
      const matchStatut = st === 'TOUS' || e.statut === st;
      const matchAvis = av === 'TOUS' || (e.avisEnseignant === av);
      return matchSearch && matchStatut && matchAvis;
    });
  });

  filteredCount = computed(() => this.filteredEntretiens().length);
  totalPages = computed(() => Math.ceil(this.filteredCount() / this.itemsPerPage) || 1);
  startIndex = computed(() => (this.currentPage() - 1) * this.itemsPerPage);
  endIndex = computed(() => Math.min(this.startIndex() + this.itemsPerPage, this.filteredCount()));

  paginatedEntretiens = computed(() => {
    const start = this.startIndex();
    return this.filteredEntretiens().slice(start, start + this.itemsPerPage);
  });

  pageNumbers = computed(() => {
    const total = this.totalPages();
    return Array.from({ length: total }, (_, i) => i + 1);
  });

  candidatsSansEntretien = computed(() => {
    const idsAvecEntretien = new Set(this.entretiens().map(e => e.candidatId));
    return this.candidats().filter(c => !idsAvecEntretien.has(c.id));
  });

  toggleFilter() {
    this.isFilterOpen.update(v => !v);
  }

  clearFilters() {
    this.statutFilter.set('TOUS');
    this.avisFilter.set('TOUS');
    this.searchQuery.set('');
    this.currentPage.set(1);
    this.isFilterOpen.set(false);
  }

  goToPage(p: number) {
    if (p >= 1 && p <= this.totalPages()) {
      this.currentPage.set(p);
    }
  }

  nextPage() {
    if (this.currentPage() < this.totalPages()) {
      this.currentPage.update(p => p + 1);
    }
  }

  prevPage() {
    if (this.currentPage() > 1) {
      this.currentPage.update(p => p - 1);
    }
  }

  onCandidatPlanifChange(id: string) {
    const found = this.candidats().find(c => c.id === id) || null;
    this.selectedCandidatForPlanif.set(found);
  }

  openPlanifierModal(candidat?: CandidatOrientation) {
    this.selectedCandidatForPlanif.set(candidat || null);
    this.formDate = '';
    this.formHeure = '';
    this.formFormat.set('Présentiel');
    this.formSalle = '';
    this.formLienVisio = '';
    this.isPlanifierModalOpen.set(true);
  }

  closePlanifierModal() {
    this.isPlanifierModalOpen.set(false);
    this.selectedCandidatForPlanif.set(null);
    this.formDate = '';
    this.formHeure = '';
    this.formSalle = '';
    this.formLienVisio = '';
  }

  validerPlanification() {
    const cand = this.selectedCandidatForPlanif();
    if (!cand) {
      alert('Veuillez sélectionner un candidat.');
      return;
    }
    if (!this.formDate) {
      alert('Veuillez renseigner la date de l’entretien.');
      return;
    }
    if (!this.formHeure) {
      alert('Veuillez renseigner l’heure de l’entretien.');
      return;
    }

    const lieu = this.formFormat() === 'Présentiel' ? this.formSalle : this.formLienVisio;
    if (!lieu) {
      alert(this.formFormat() === 'Présentiel' ? 'Veuillez indiquer la salle.' : 'Veuillez indiquer le lien de visioconférence.');
      return;
    }

    const enseignantNom = this.user()?.name || 'Prof. Dupont';
    const lieuComplet = this.formFormat() === 'Présentiel'
      ? `Présentiel : ${this.formSalle}`
      : `Visio : ${this.formLienVisio}`;

    this.orientationService.planifierEntretien(cand, this.formDate, this.formHeure, lieuComplet, enseignantNom);
    this.closePlanifierModal();
  }

  openMenerModal(e: Entretien) {
    this.entretienEnCours.set(e);
    this.formAvis.set(e.avisEnseignant === 'Défavorable' ? 'Défavorable' : 'Favorable');
    this.formNotes = e.notesEntretien || '';

    const cand = this.candidats().find(c => c.id === e.candidatId);
    this.formOrientationFinale = e.orientationFinale || cand?.filiereSouhaitee || 'Génie Logiciel & Informatique (IIT)';

    this.isMenerModalOpen.set(true);
  }

  closeMenerModal() {
    this.isMenerModalOpen.set(false);
    this.entretienEnCours.set(null);
  }

  validerFinEntretien() {
    const ent = this.entretienEnCours();
    if (!ent) return;

    this.orientationService.conclureEntretien(
      ent.id,
      this.formAvis(),
      this.formNotes,
      this.formOrientationFinale
    );
    this.closeMenerModal();
  }
}
