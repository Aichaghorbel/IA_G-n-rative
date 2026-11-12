import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { OrientationService, QuestionQCM, ResultatQCM } from '../../../services/orientation.service';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-qcm',
  standalone: true,
  imports: [CommonModule, RouterModule, LucideAngularModule],
  templateUrl: './qcm.component.html'
})
export class QcmComponent {
  private orientationService = inject(OrientationService);
  private authService = inject(AuthService);

  user = this.authService.user;
  selectedUniversite = signal<'IIT' | 'ISB'>(this.detectUniversite());

  get questions(): QuestionQCM[] {
    return this.orientationService.getQuestionsForUniversite(this.selectedUniversite());
  }

  private detectUniversite(): 'IIT' | 'ISB' {
    const email = this.user()?.email?.toLowerCase() || '';
    const name = this.user()?.name?.toLowerCase() || '';
    const cand = this.orientationService.candidats().find(
      c => c.email.toLowerCase() === email || c.nom.toLowerCase() === name
    );
    return cand?.universiteSouhaitee || 'IIT';
  }

  // État du quiz
  currentIndex = signal<number>(0);
  reponses = signal<Record<number, number>>({});
  isCompleted = signal<boolean>(false);
  resultat = signal<ResultatQCM | null>(null);

  currentQuestion() {
    return this.questions[this.currentIndex()];
  }

  progression() {
    return Math.round(((this.currentIndex() + 1) / this.questions.length) * 100);
  }

  selectionnerReponse(optionIndex: number) {
    const qId = this.currentQuestion().id;
    this.reponses.update(prev => ({
      ...prev,
      [qId]: optionIndex
    }));
  }

  estOptionChoisie(optionIndex: number): boolean {
    const qId = this.currentQuestion().id;
    return this.reponses()[qId] === optionIndex;
  }

  questionSuivante() {
    if (this.currentIndex() < this.questions.length - 1) {
      this.currentIndex.update(i => i + 1);
    } else {
      this.validerQCM();
    }
  }

  questionPrecedente() {
    if (this.currentIndex() > 0) {
      this.currentIndex.update(i => i - 1);
    }
  }

  validerQCM() {
    const nom = this.user()?.name || 'Candidat';
    const res = this.orientationService.soumettreQCM(this.reponses(), nom, this.selectedUniversite());
    this.resultat.set(res);
    this.isCompleted.set(true);
  }

  recommencer() {
    this.reponses.set({});
    this.currentIndex.set(0);
    this.isCompleted.set(false);
    this.resultat.set(null);
  }
}

