import { Component, signal, computed, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule, ActivatedRoute } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { animate, style, transition, trigger } from '@angular/animations';
import { OrientationService, CandidatOrientation } from '../../../services/orientation.service';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-students-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, LucideAngularModule],
  templateUrl: './students-list.component.html',
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
export class StudentsListComponent implements OnInit {
  private orientationService = inject(OrientationService);
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  ngOnInit() {
    this.route.queryParams.subscribe(params => {
      const statut = params['statut'];
      if (statut === 'Orientation validée' || statut === 'Orientation ajustée' || statut === 'En attente entretien') {
        this.statusFilter.set(statut);
        this.currentPage.set(1);
      }
    });
  }

  candidats = this.orientationService.candidats;
  entretiens = this.orientationService.entretiens;
  teacherUni = computed<'IIT' | 'ISB'>(() =>
    this.authService.user()?.university === 'ISB' ? 'ISB' : 'IIT'
  );

  getAvisEnseignant(candidatId: string): 'Favorable' | 'Défavorable' | null {
    const ent = this.entretiens().find(e => e.candidatId === candidatId && e.avisEnseignant);
    return ent?.avisEnseignant ?? null;
  }

  // Search & Filters
  searchQuery = signal('');
  uniFilter = signal('');
  statusFilter = signal('');
  qcmFilter = signal('');
  isFilterOpen = signal(false);

  // Selected candidate for profile modal
  selectedCandidat = signal<CandidatOrientation | null>(null);

  // Modal Ajuster Orientation
  candidatAjustement = signal<CandidatOrientation | null>(null);
  nouvelleFiliere = '';
  motifAjustement = '';

  // Options de réorientation IIT / ISB
  filieresDisponibles = [
    { uni: 'IIT', nom: 'Architecture (IIT)' },
    { uni: 'IIT', nom: 'Génie Logiciel & Informatique (IIT)' },
    { uni: 'IIT', nom: 'Génie Civil & BTP (IIT)' },
    { uni: 'IIT', nom: 'Génie Mécanique & Robotique (IIT)' },
    { uni: 'IIT', nom: 'Génie des Télécommunications & IoT (IIT)' },
    { uni: 'IIT', nom: 'Cycle Préparatoire aux Grandes Écoles (IIT)' },
    { uni: 'IIT', nom: 'Licence en Technologie & Informatique (IIT)' },
    { uni: 'ISB', nom: 'Licence en Business Intelligence & Analytics (ISB)' },
    { uni: 'ISB', nom: 'Licence en Gestion & Marketing Digital (ISB)' },
    { uni: 'ISB', nom: 'Licence en Comptabilité & Finance (ISB)' },
    { uni: 'ISB', nom: 'Master en Finance & Ingénierie Financière (ISB)' },
    { uni: 'ISB', nom: 'MBA - Master in Business Administration (ISB)' }
  ];

  // Pagination
  currentPage = signal(1);
  itemsPerPage = 6;

  filteredCandidats = computed(() => {
    const q = this.searchQuery().toLowerCase().trim();
    const uni = this.teacherUni();
    const status = this.statusFilter();
    const qcm = this.qcmFilter();

    return this.candidats().filter(c => {
      if (c.universiteSouhaitee !== uni) return false;

      const matchesSearch = !q ||
        c.nom.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q) ||
        c.filiereSouhaitee.toLowerCase().includes(q) ||
        (c.bac && c.bac.toLowerCase().includes(q));

      const matchesStatus = !status || c.statutOrientation === status;
      const matchesQcm = !qcm || (qcm === 'Passe' ? c.qcmPasse : !c.qcmPasse);

      return matchesSearch && matchesStatus && matchesQcm;
    });
  });

  filteredCount = computed(() => this.filteredCandidats().length);
  totalPages = computed(() => Math.ceil(this.filteredCount() / this.itemsPerPage) || 1);
  startIndex = computed(() => (this.currentPage() - 1) * this.itemsPerPage);
  endIndex = computed(() => Math.min(this.startIndex() + this.itemsPerPage, this.filteredCount()));

  paginatedCandidats = computed(() => {
    const start = this.startIndex();
    return this.filteredCandidats().slice(start, start + this.itemsPerPage);
  });

  pageNumbers = computed(() => {
    const total = this.totalPages();
    const current = this.currentPage();
    let start = Math.max(1, current - 2);
    let end = Math.min(total, start + 4);
    if (end - start < 4) {
      start = Math.max(1, end - 4);
    }
    return Array.from({ length: Math.max(0, end - start + 1) }, (_, i) => start + i);
  });

  toggleFilter() {
    this.isFilterOpen.update(v => !v);
  }

  clearFilters() {
    this.uniFilter.set('');
    this.statusFilter.set('');
    this.qcmFilter.set('');
    this.searchQuery.set('');
    this.currentPage.set(1);
    this.isFilterOpen.set(false);
  }

  prevPage() {
    if (this.currentPage() > 1) this.currentPage.update(v => v - 1);
  }

  nextPage() {
    if (this.currentPage() < this.totalPages()) this.currentPage.update(v => v + 1);
  }

  goToPage(p: number) {
    if (p >= 1 && p <= this.totalPages()) {
      this.currentPage.set(p);
    }
  }

  // Use Case: Consulter profil candidat
  viewProfile(candidat: CandidatOrientation) {
    this.selectedCandidat.set(candidat);
  }

  closeProfile() {
    this.selectedCandidat.set(null);
  }

  // Use Case: Valider l'orientation
  validerOrientation(candidat: CandidatOrientation, event?: Event) {
    if (event) event.stopPropagation();
    const filiere = candidat.filiereSouhaitee + ` (${candidat.universiteSouhaitee})`;
    this.orientationService.validerOrientation(candidat.id, filiere);
    
    // Refresh modal if opened
    if (this.selectedCandidat()?.id === candidat.id) {
      const updated = this.candidats().find(c => c.id === candidat.id);
      if (updated) this.selectedCandidat.set(updated);
    }
  }

  // Use Case: Ajuster l'orientation
  openAjusterModal(candidat: CandidatOrientation, event?: Event) {
    if (event) event.stopPropagation();
    this.candidatAjustement.set(candidat);
    this.nouvelleFiliere = candidat.filiereSouhaitee + ` (${candidat.universiteSouhaitee})`;
    this.motifAjustement = '';
  }

  closeAjusterModal() {
    this.candidatAjustement.set(null);
    this.motifAjustement = '';
  }

  confirmerAjustement() {
    const c = this.candidatAjustement();
    if (!c) return;

    this.orientationService.ajusterOrientation(
      c.id,
      this.nouvelleFiliere,
      this.motifAjustement || "Réorientation pédagogique suite à l'analyse du profil et score QCM."
    );

    // Refresh modal if opened
    if (this.selectedCandidat()?.id === c.id) {
      const updated = this.candidats().find(cand => cand.id === c.id);
      if (updated) this.selectedCandidat.set(updated);
    }

    this.closeAjusterModal();
  }

  // Helpers d'affichage Score QCM, Reco IA & Statuts
  getScoreColorClass(score?: number): { bar: string; text: string } {
    if (score === undefined || score === null) {
      return { bar: 'bg-slate-200', text: 'text-slate-400' };
    }
    // Règle demandée :
    // - vert lorsque plus de 50% (>= 50)
    // - jaune si inférieur (< 50 et >= 20)
    // - rouge si inférieur à 20 (< 20)
    if (score >= 50) {
      return { bar: 'bg-emerald-500', text: 'text-emerald-700' };
    } else if (score >= 20) {
      return { bar: 'bg-amber-400', text: 'text-amber-700' };
    } else {
      return { bar: 'bg-red-500', text: 'text-red-600' };
    }
  }

  getRecoFiliere(c: CandidatOrientation): string {
    if (c.recoFiliere) return c.recoFiliere;
    if (!c.qcmPasse) return 'Test QCM en attente';
    return c.filiereSouhaitee;
  }

  getRecoMatch(c: CandidatOrientation): string {
    if (!c.qcmPasse) return 'Évaluation en attente';
    const match = c.recoMatch || (c.scoreQcm ? Math.min(95, Math.max(35, c.scoreQcm + 6)) : 75);
    return `${c.universiteSouhaitee} · ${match}%`;
  }

  getOrientationLabel(statut: string): string {
    switch (statut) {
      case 'Orientation validée': return 'Validée';
      case 'Orientation ajustée': return 'Ajustée';
      case 'En attente entretien': return 'À valider';
      case 'En attente QCM': return 'En attente';
      default: return statut;
    }
  }

  // Use Case: Planifier un entretien pour ce candidat
  planifierEntretien(candidat: CandidatOrientation, event?: Event) {
    if (event) event.stopPropagation();
    this.closeProfile();
    this.router.navigate(['/enseignant/entretiens']);
  }
}
