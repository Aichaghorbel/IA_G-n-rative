import { Component, inject, OnInit, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../../services/auth.service';
import { OrientationService } from '../../../services/orientation.service';

@Component({
  selector: 'app-enseignant-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, LucideAngularModule],
  templateUrl: './enseignant-dashboard.component.html'
})
export class EnseignantDashboardComponent implements OnInit {
  private authService = inject(AuthService);
  private orientationService = inject(OrientationService);

  user = this.authService.user;
  teacherUni = computed<'IIT' | 'ISB'>(() =>
    this.authService.user()?.university === 'ISB' ? 'ISB' : 'IIT'
  );
  allCandidats = this.orientationService.candidats;
  candidats = computed(() =>
    this.allCandidats().filter(c => c.universiteSouhaitee === this.teacherUni())
  );
  entretiens = computed(() => {
    const uni = this.teacherUni();
    const allowedIds = new Set(this.candidats().map(c => c.id));
    return this.orientationService.entretiens().filter(e => {
      const cand = this.allCandidats().find(c => c.id === e.candidatId);
      if (cand) return cand.universiteSouhaitee === uni;
      return allowedIds.has(e.candidatId);
    });
  });

  prochainsEntretiens = () => this.entretiens().filter(e => e.statut === 'Planifié');
  candidatsAValider = () => this.candidats().filter(c => c.statutOrientation === 'En attente entretien');

  scoreQcmMoyen = () => {
    const passes = this.candidats().filter(c => c.qcmPasse && typeof c.scoreQcm === 'number');
    if (passes.length === 0) return '0%';
    const total = passes.reduce((acc, c) => acc + (c.scoreQcm || 0), 0);
    return `${Math.round(total / passes.length)}%`;
  };

  stats = () => [
    { label: 'Candidats à orienter', value: this.candidats().length, icon: 'users', color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Entretiens planifiés', value: this.prochainsEntretiens().length, icon: 'calendar', color: 'text-amber-600', bg: 'bg-amber-50' },
    { label: 'Score QCM moyen', value: this.scoreQcmMoyen(), icon: 'clipboard-check', color: 'text-purple-600', bg: 'bg-purple-50' },
    { label: 'Orientations validées', value: this.candidats().filter(c => c.statutOrientation.includes('validée')).length, icon: 'check-circle', color: 'text-emerald-600', bg: 'bg-emerald-50' }
  ];

  ngOnInit() {}
}
