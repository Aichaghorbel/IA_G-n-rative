import { Component, inject, signal, computed, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { OrientationService, Parcours } from '../../../services/orientation.service';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-parcours',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, LucideAngularModule],
  templateUrl: './parcours.component.html',
  styleUrls: ['./parcours.component.css']
})
export class ParcoursComponent {
  @ViewChild('parcoursScrollContainer') parcoursScrollContainer!: ElementRef<HTMLDivElement>;

  private orientationService = inject(OrientationService);
  private authService = inject(AuthService);
  private router = inject(Router);

  user = this.authService.user;
  parcoursList = this.orientationService.parcoursList;

  selectedUni = signal<'TOUT' | 'IIT' | 'ISB'>('IIT');
  searchQuery = signal<string>('');
  selectedParcoursForDetails = signal<Parcours | null>(null);

  // Modal préinscription
  isPreinscriptionModalOpen = signal<boolean>(false);
  preinscriptionParcours = signal<Parcours | null>(null);

  formNom = '';
  formEmail = '';
  formPhone = '+216 ';
  formBac = 'Baccalauréat Scientifique / Technique';
  successMessage = signal<string | null>(null);

  constructor() {
    const currentUser = this.user();
    if (currentUser) {
      this.formNom = currentUser.name || '';
      this.formEmail = currentUser.email || '';
    }
  }

  // Visual styling dictionary per parcours (avec cache pour performance ultra-rapide)
  private visualCache = new Map<string, any>();

  getParcoursVisual(parcours: Parcours, index?: number): any {
    if (!parcours) {
      return this.getDefaultVisual();
    }

    const key = parcours.id || `${parcours.universite}-${parcours.nom}`;
    if (this.visualCache.has(key)) {
      return this.visualCache.get(key);
    }

    const visual = this.computeParcoursVisual(parcours);
    this.visualCache.set(key, visual);
    return visual;
  }

  private getDefaultVisual() {
    return {
      bgImage: 'assets/images/licence.jpg',
      badgeColor: 'text-indigo-300 border-indigo-500/20',
      tag1Color: 'text-indigo-300 border-indigo-500/20',
      tag2Color: 'text-sky-300 border-sky-500/20',
      subColor: 'text-indigo-200',
      actionPulse: 'text-indigo-400',
      titleGrad: 'from-indigo-600 to-cyan-600',
      borderBack: 'border-indigo-200',
      badgeBack: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      iconColor: 'text-indigo-500',
      descBg: 'from-indigo-600/10 to-cyan-600/10 text-indigo-800',
      btnGrad: 'from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500'
    };
  }

  private computeParcoursVisual(parcours: Parcours) {
    // ==========================================
    // ISB PARCOURS (Licence, Master, MBA)
    // ==========================================
    if (parcours?.universite === 'ISB') {
      const typeLower = (parcours.type || '').toLowerCase();
      const nomLower = (parcours.nom || '').toLowerCase();
      const idLower = (parcours.id || '').toLowerCase();

      // MBA
      if (typeLower.includes('mba') || nomLower.includes('mba') || idLower.includes('mba')) {
        return {
          bgImage: 'assets/images/mba-3.png',
          badgeColor: 'text-amber-300 border-amber-500/20',
          tag1Color: 'text-amber-300 border-amber-500/20',
          tag2Color: 'text-rose-300 border-rose-500/20',
          subColor: 'text-amber-200',
          actionPulse: 'text-amber-400',
          titleGrad: 'from-amber-600 to-rose-600',
          borderBack: 'border-amber-200',
          badgeBack: 'bg-amber-50 text-amber-700 border-amber-200',
          iconColor: 'text-amber-500',
          descBg: 'from-amber-600/10 to-rose-600/10 text-amber-800',
          btnGrad: 'from-amber-600 to-rose-600 hover:from-amber-500 hover:to-rose-500'
        };
      }

      // Master
      if (typeLower.includes('master') || nomLower.includes('master') || idLower.includes('master')) {
        return {
          bgImage: 'assets/images/MASTER.jpg',
          badgeColor: 'text-purple-300 border-purple-500/20',
          tag1Color: 'text-purple-300 border-purple-500/20',
          tag2Color: 'text-indigo-300 border-indigo-500/20',
          subColor: 'text-purple-200',
          actionPulse: 'text-purple-400',
          titleGrad: 'from-purple-600 to-indigo-600',
          borderBack: 'border-purple-200',
          badgeBack: 'bg-purple-50 text-purple-700 border-purple-200',
          iconColor: 'text-purple-500',
          descBg: 'from-purple-600/10 to-indigo-600/10 text-purple-800',
          btnGrad: 'from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500'
        };
      }

      // Licence (ISB)
      return {
        bgImage: 'assets/images/isb_licence.jpg',
        badgeColor: 'text-emerald-300 border-emerald-500/20',
        tag1Color: 'text-emerald-300 border-emerald-500/20',
        tag2Color: 'text-teal-300 border-teal-500/20',
        subColor: 'text-emerald-200',
        actionPulse: 'text-emerald-400',
        titleGrad: 'from-emerald-600 to-teal-600',
        borderBack: 'border-emerald-200',
        badgeBack: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        iconColor: 'text-emerald-500',
        descBg: 'from-emerald-600/10 to-teal-600/10 text-emerald-800',
        btnGrad: 'from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500'
      };
    }

    // ==========================================
    // IIT PARCOURS (Architecture, Ingénierie, Licence, Prépa)
    // ==========================================
    const nomLower = (parcours?.nom || '').toLowerCase();
    const typeLower = (parcours?.type || '').toLowerCase();

    // Architecture
    if (typeLower.includes('archi') || nomLower.includes('archi')) {
      return {
        bgImage: 'assets/images/architecture.jpg',
        badgeColor: 'text-cyan-300 border-cyan-500/20',
        tag1Color: 'text-cyan-300 border-cyan-500/20',
        tag2Color: 'text-indigo-300 border-indigo-500/20',
        subColor: 'text-cyan-200',
        actionPulse: 'text-cyan-400',
        titleGrad: 'from-cyan-600 to-indigo-600',
        borderBack: 'border-cyan-200',
        badgeBack: 'bg-cyan-50 text-cyan-700 border-cyan-200',
        iconColor: 'text-cyan-500',
        descBg: 'from-cyan-600/10 to-indigo-600/10 text-cyan-800',
        btnGrad: 'from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500'
      };
    }

    // Ingénierie (Image ultra-optimisée JPEG 114KB au lieu de 2MB)
    if (typeLower.includes('ing') || nomLower.includes('ing')) {
      return {
        bgImage: 'assets/images/ing.jpg',
        badgeColor: 'text-blue-300 border-blue-500/20',
        tag1Color: 'text-blue-300 border-blue-500/20',
        tag2Color: 'text-sky-300 border-sky-500/20',
        subColor: 'text-blue-200',
        actionPulse: 'text-blue-400',
        titleGrad: 'from-blue-600 to-indigo-600',
        borderBack: 'border-blue-200',
        badgeBack: 'bg-blue-50 text-blue-700 border-blue-200',
        iconColor: 'text-blue-500',
        descBg: 'from-blue-600/10 to-indigo-600/10 text-blue-800',
        btnGrad: 'from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500'
      };
    }

    // Préparatoire
    if (typeLower.includes('prépa') || nomLower.includes('prépa')) {
      return {
        bgImage: 'assets/images/prepa.jpg',
        badgeColor: 'text-amber-300 border-amber-500/20',
        tag1Color: 'text-amber-300 border-amber-500/20',
        tag2Color: 'text-orange-300 border-orange-500/20',
        subColor: 'text-amber-200',
        actionPulse: 'text-amber-400',
        titleGrad: 'from-amber-600 to-orange-600',
        borderBack: 'border-amber-200',
        badgeBack: 'bg-amber-50 text-amber-700 border-amber-200',
        iconColor: 'text-amber-500',
        descBg: 'from-amber-600/10 to-orange-600/10 text-amber-800',
        btnGrad: 'from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500'
      };
    }

    // Licence IIT par défaut (optimisé JPEG 45KB)
    return {
      bgImage: 'assets/images/licence.jpg',
      badgeColor: 'text-indigo-300 border-indigo-500/20',
      tag1Color: 'text-indigo-300 border-indigo-500/20',
      tag2Color: 'text-sky-300 border-sky-500/20',
      subColor: 'text-indigo-200',
      actionPulse: 'text-indigo-400',
      titleGrad: 'from-indigo-600 to-cyan-600',
      borderBack: 'border-indigo-200',
      badgeBack: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      iconColor: 'text-indigo-500',
      descBg: 'from-indigo-600/10 to-cyan-600/10 text-indigo-800',
      btnGrad: 'from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500'
    };
  }

  private scrollInterval: any = null;

  scrollLeft() {
    if (this.parcoursScrollContainer) {
      this.parcoursScrollContainer.nativeElement.scrollBy({ left: -420, behavior: 'smooth' });
    }
  }

  scrollRight() {
    if (this.parcoursScrollContainer) {
      this.parcoursScrollContainer.nativeElement.scrollBy({ left: 420, behavior: 'smooth' });
    }
  }

  startContinuousScroll(direction: 'left' | 'right') {
    this.stopContinuousScroll();
    const container = this.parcoursScrollContainer?.nativeElement;
    if (!container) return;

    const step = direction === 'left' ? -18 : 18;
    this.scrollInterval = setInterval(() => {
      container.scrollLeft += step;
    }, 16);
  }

  stopContinuousScroll() {
    if (this.scrollInterval) {
      clearInterval(this.scrollInterval);
      this.scrollInterval = null;
    }
  }

  filteredParcours = computed(() => {
    const uni = this.selectedUni();
    const query = this.searchQuery().toLowerCase().trim();

    return this.parcoursList().filter(p => {
      const matchUni = uni === 'TOUT' || p.universite === uni;
      const matchQuery = !query ||
        p.nom.toLowerCase().includes(query) ||
        p.description.toLowerCase().includes(query) ||
        p.debouches.some(d => d.toLowerCase().includes(query)) ||
        p.competences.some(c => c.toLowerCase().includes(query));
      return matchUni && matchQuery;
    });
  });

  openDetails(p: Parcours) {
    this.selectedParcoursForDetails.set(p);
  }

  closeDetails() {
    this.selectedParcoursForDetails.set(null);
  }

  openPreinscription(p: Parcours) {
    this.router.navigate(['/student/preinscription'], {
      queryParams: {
        filiere: p.nom,
        uni: p.universite
      }
    });
  }

  closePreinscription() {
    this.isPreinscriptionModalOpen.set(false);
    this.preinscriptionParcours.set(null);
  }

  soumettrePreinscription() {
    const p = this.preinscriptionParcours();
    if (!p) return;

    if (!this.formNom || !this.formEmail) {
      alert('Veuillez remplir votre nom et email.');
      return;
    }

    this.orientationService.enregistrerPreinscription({
      nom: this.formNom,
      email: this.formEmail,
      phone: this.formPhone,
      bac: this.formBac,
      universite: p.universite,
      filiere: p.nom
    });

    this.successMessage.set(`Préinscription validée avec succès pour ${p.nom} (${p.universite}) !`);
    setTimeout(() => {
      this.closePreinscription();
    }, 2000);
  }
}
