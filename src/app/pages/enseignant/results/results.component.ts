import { Component, signal, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { animate, style, transition, trigger } from '@angular/animations';
import { OrientationService, CandidatOrientation, QuestionQCM } from '../../../services/orientation.service';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './results.component.html',
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
export class ResultsComponent {
  private orientationService = inject(OrientationService);
  private authService = inject(AuthService);

  candidats = this.orientationService.candidats;
  optionLetters = ['A', 'B', 'C', 'D'];

  // Université de l'enseignant connecté (IIT ou ISB)
  teacherUni = computed<'IIT' | 'ISB'>(() =>
    this.authService.user()?.university === 'ISB' ? 'ISB' : 'IIT'
  );

  modules = computed(() => this.orientationService.getModulesForUniversite(this.teacherUni()));
  modalQuestions = computed(() => {
    const c = this.selectedCandidat();
    return this.orientationService.getQuestionsForUniversite(c?.universiteSouhaitee || this.teacherUni());
  });

  // Search & Filters
  searchQuery = signal('');
  scoreFilter = signal('');
  isFilterOpen = signal(false);

  // Selected candidate for QCM detail + correction modal
  selectedCandidat = signal<CandidatOrientation | null>(null);

  // Pagination
  currentPage = signal(1);
  itemsPerPage = 6;

  filteredCandidats = computed(() => {
    const q = this.searchQuery().toLowerCase().trim();
    const uni = this.teacherUni();
    const scoreRange = this.scoreFilter();

    return this.candidats().filter(c => {
      if (!c.qcmPasse || c.universiteSouhaitee !== uni) return false;

      const matchesSearch = !q ||
        c.nom.toLowerCase().includes(q) ||
        c.email.toLowerCase().includes(q) ||
        c.filiereSouhaitee.toLowerCase().includes(q) ||
        (c.bac && c.bac.toLowerCase().includes(q));

      let matchesScore = true;
      if (scoreRange) {
        if (c.scoreQcm === undefined) {
          matchesScore = false;
        } else if (scoreRange === 'haut') {
          matchesScore = c.scoreQcm >= 50;
        } else if (scoreRange === 'moyen') {
          matchesScore = c.scoreQcm >= 20 && c.scoreQcm < 50;
        } else if (scoreRange === 'bas') {
          matchesScore = c.scoreQcm < 20;
        }
      }

      return matchesSearch && matchesScore;
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
    this.scoreFilter.set('');
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

  openQcmModal(candidat: CandidatOrientation) {
    if (!candidat.qcmPasse) return;
    this.selectedCandidat.set(candidat);
  }

  closeQcmModal() {
    this.selectedCandidat.set(null);
  }

  getScoreColorClass(score?: number): { bar: string; text: string; badge: string } {
    if (score === undefined || score === null) {
      return { bar: 'bg-slate-200', text: 'text-slate-400', badge: 'bg-slate-100 text-slate-600 border-slate-200' };
    }
    if (score >= 50) {
      return { bar: 'bg-emerald-500', text: 'text-emerald-700', badge: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
    } else if (score >= 20) {
      return { bar: 'bg-amber-400', text: 'text-amber-700', badge: 'bg-amber-50 text-amber-700 border-amber-200' };
    } else {
      return { bar: 'bg-red-500', text: 'text-red-600', badge: 'bg-red-50 text-red-700 border-red-200' };
    }
  }

  private getQuestionsForCandidate(c: CandidatOrientation | null): QuestionQCM[] {
    return this.orientationService.getQuestionsForUniversite(c?.universiteSouhaitee || 'IIT');
  }

  getStudentAnswers(c: CandidatOrientation | null): Record<number, number> {
    if (!c) return {};
    if (c.reponsesQcm) return c.reponsesQcm;

    const questions = this.getQuestionsForCandidate(c);
    const score = c.scoreQcm || 0;
    const expectedCorrect = Math.round((score / 100) * questions.length);
    const derived: Record<number, number> = {};
    questions.forEach((q, idx) => {
      if (idx < expectedCorrect) {
        derived[q.id] = q.bonneReponseIndex;
      } else {
        derived[q.id] = (q.bonneReponseIndex + 1) % q.options.length;
      }
    });
    return derived;
  }

  getStudentAnswerForQuestion(c: CandidatOrientation | null, questionId: number): number | undefined {
    const answers = this.getStudentAnswers(c);
    return answers[questionId];
  }

  isQuestionCorrect(c: CandidatOrientation | null, q: QuestionQCM): boolean {
    const ans = this.getStudentAnswerForQuestion(c, q.id);
    return ans !== undefined && ans === q.bonneReponseIndex;
  }

  getCorrectCount(c: CandidatOrientation | null): number {
    if (!c || !c.qcmPasse) return 0;
    const questions = this.getQuestionsForCandidate(c);
    return questions.filter(q => this.isQuestionCorrect(c, q)).length;
  }

  getModuleScoreText(c: CandidatOrientation, domaine: string): string {
    const questions = this.getQuestionsForCandidate(c);
    const moduleQuestions = questions.filter(q => q.domaine === domaine);
    if (moduleQuestions.length === 0) return '0 / 0';
    const correctCount = moduleQuestions.filter(q => this.isQuestionCorrect(c, q)).length;
    return `${correctCount} / ${moduleQuestions.length}`;
  }

  getNiveauLabel(score?: number): string {
    if (score === undefined || score === null) return '—';
    if (score >= 80) return 'Avancé';
    if (score >= 50) return 'Intermédiaire';
    return 'À consolider';
  }
}
