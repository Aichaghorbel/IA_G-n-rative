import {
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../services/auth.service';
import { ChatbotFabComponent } from '../../components/chatbot-fab/chatbot-fab.component';

export type NavSection =
  | 'accueil'
  | 'formations'
  | 'orientation'
  | 'preinscription'
  | 'demandes';

export type Universite = 'IIT' | 'ISB';

interface QuickAccessCard {
  id: NavSection;
  title: string;
  description: string;
  cta: string;
  icon: 'book' | 'graduation-cap' | 'clipboard';
}

interface SpotlightEvent {
  id: string;
  icon: 'sparkles' | 'rocket';
  title: string;
  summary: string;
  image: string;
  imageAlt: string;
}

interface OrientationTrack {
  id: string;
  label: string;
  previewBadge: string;
  previewQuote: string;
  highlightPrograms: string[];
  questions: string[];
}

@Component({
  selector: 'app-acceuil',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, ChatbotFabComponent],
  templateUrl: './acceuil.component.html',
  styleUrls: ['./acceuil.component.css'],
})
export class AcceuilComponent implements OnInit, OnDestroy {
  private readonly router = inject(Router);
  private readonly authService = inject(AuthService);
  private readonly cdr = inject(ChangeDetectorRef);

  protected readonly assets = {
    iitEngineeringLab: 'assets/images/ing.jpg',
    isbBusinessCampus: 'assets/images/isb_campus.webp',
    studioImage: 'assets/images/ai_orientation_studio.webp',
  };

  protected readonly totalFormations = 8;
  protected readonly iitCount = 5;
  protected readonly isbCount = 3;

  protected readonly userMode = computed<'etudiant' | 'visiteur'>(() =>
    this.authService.user()?.role === 'student' ? 'etudiant' : 'visiteur',
  );

  protected readonly profile = computed(() => {
    const u = this.authService.user();
    const prenom = u?.name ? u.name.split(' ')[0] : 'Candidat';
    return {
      prenom,
      dernierDiplome: 'Baccalauréat',
      anneeObtention: '2026',
    };
  });

  /* ── Quick Access Cards ── */
  protected readonly quickAccessCards: QuickAccessCard[] = [
    {
      id: 'formations',
      title: 'Découvrir les formations',
      description:
        'Explorez les cycles préparatoires, licences, diplômes d’ingénieur et mastères de l’IIT et de l’ISB.',
      cta: 'Parcourir le catalogue',
      icon: 'book',
    },
    {
      id: 'orientation',
      title: 'Orientation intelligente',
      description:
        'Obtenez des recommandations académiques personnalisées grâce à l’assistant IA.',
      cta: 'Démarrer l’orientation',
      icon: 'graduation-cap',
    },
    {
      id: 'preinscription',
      title: 'Préinscription',
      description:
        'Constituez votre dossier d’admission en ligne et devenez candidat officiel.',
      cta: 'Ouvrir le formulaire',
      icon: 'clipboard',
    },
  ];

  /* ── Campus Spotlight Slider ── */
  protected readonly spotlightEvents: SpotlightEvent[] = [
    {
      id: 'nau-canada-visit',
      icon: 'sparkles',
      title: 'Visite d’excellence au campus NAU',
      summary:
        'Le campus de la North American Private University a eu l’honneur d’accueillir Son Excellence Alexandre Bilodeau, Ambassadeur du Canada en Tunisie, à l’occasion de l’inauguration des nouvelles extensions du campus.',
      image: 'assets/images/nau_visit_canada.jpg',
      imageAlt:
        'Accueil de Son Excellence Alexandre Bilodeau, Ambassadeur du Canada en Tunisie, au campus NAU Sfax',
    },
    {
      id: 'nau-uk-visit',
      icon: 'sparkles',
      title: 'Visite officielle : renforcement des liens avec le Royaume-Uni',
      summary:
        'Le groupe NAU à Sfax a eu l’honneur d’accueillir Son Excellence M. Ruddy Drummond, Ambassadeur du Royaume-Uni en Tunisie, ainsi que Mme Jill Coates, Directrice du British Council Tunisia.',
      image: 'assets/images/nau_visit_uk.jpg',
      imageAlt:
        'Visite officielle de M. Ruddy Drummond, Ambassadeur du Royaume-Uni en Tunisie, au groupe NAU Sfax',
    },
    {
      id: 'nau-enet-aero-cup',
      icon: 'rocket',
      title:
        'Compétition Drone 2026 – ENET AERO CUP 5.0 : l’innovation prend son envol',
      summary:
        'Le campus NAU a accueilli une édition exceptionnelle de l’ENET AERO CUP 5.0, un événement où technologie, précision et créativité se rencontrent.',
      image: 'assets/images/nau_drone_cup.jpg',
      imageAlt:
        'Étudiant pilotant un drone lors de la compétition ENET AERO CUP 5.0 au campus NAU Sfax',
    },
    {
      id: 'iit-isb-portes-ouvertes',
      icon: 'sparkles',
      title:
        'Mettre l’intelligence artificielle en pratique, c’est transformer les idées en impact réel.',
      summary:
        'À travers plus de 80 projets, nos étudiants, accompagnés de partenaires académiques et industriels, ont donné vie à des solutions innovantes alliant créativité, rigueur et esprit de collaboration.',
      image: 'assets/images/hero_campus_iit.jpg',
      imageAlt: 'Campus universitaire moderne IIT & ISB à Sfax',
    },
  ];

  protected currentSlideIndex = 0;
  protected isSpotlightPaused = false;
  protected failedSpotlightImages = new Set<string>();
  private autoplayTimer?: ReturnType<typeof setInterval>;

  protected get activeSlide(): SpotlightEvent {
    return this.spotlightEvents[this.currentSlideIndex];
  }

  protected get totalSlides(): number {
    return this.spotlightEvents.length;
  }

  /* ── AI Orientation FAQ ── */
  protected readonly tracks: OrientationTrack[] = [
    {
      id: 'architecture',
      label: 'Architecture',
      previewBadge: 'Formation Architecture · IIT (6 ans)',
      previewQuote:
        'Le cursus Architecture de l’IIT (6 ans) forme des architectes créatifs en ateliers de conception, urbanisme méditerranéen, patrimoine et éco-conception bioclimatique.',
      highlightPrograms: ['Diplôme National d’Architecte (6 ans)', 'Ateliers & BIM'],
      questions: [
        'Comment se déroule le programme d’Architecture sur 6 ans à l’IIT ?',
        'Quelles sont les conditions d’admission et frais de scolarité en Architecture ?',
        'Quels sont les débouchés et ateliers pratiques disponibles en Architecture ?',
      ],
    },
    {
      id: 'ingenierie',
      label: 'Ingénierie',
      previewBadge: 'Formation Ingénierie · Cycle Ingénieur IIT (3 ans)',
      previewQuote:
        'Accrédité EUR-ACE, le Cycle Ingénieur de l’IIT couvre Génie Informatique, Génie Industriel, Génie Civil et Télécommunications, en cours de jour ou de soir.',
      highlightPrograms: ['Génie Informatique EUR-ACE', 'Génie Industriel & Civil'],
      questions: [
        'Quelles sont les spécialités du Cycle Ingénieur à l’IIT (jour et soir) ?',
        'Comment accéder au Cycle Ingénieur après une Licence ou un Cycle Préparatoire ?',
        'Quels sont les débouchés en IA, Cloud, BIM et Industrie 4.0 à l’IIT ?',
      ],
    },
    {
      id: 'licence',
      label: 'Licence',
      previewBadge: 'Formation Licence · IIT & ISB (3 ans · LMD)',
      previewQuote:
        'Nos Licences Nationales couvrent l’Informatique (GLSI), la Business Intelligence (Bilingue), le BBA (100 % Anglophone), Business Economics with AI et le Droit des Affaires.',
      highlightPrograms: ['Licence GLSI (IIT)', 'BBA (ENG) & BI (ISB)'],
      questions: [
        'Quelle différence entre Licence GLSI (IIT) et Business Intelligence (ISB) ?',
        'Quelles Licences anglophones ou bilingues propose l’ISB après le Bac ?',
        'Peut-on intégrer le Cycle Ingénieur ou un Mastère après une Licence ?',
      ],
    },
    {
      id: 'mastere',
      label: 'Mastère',
      previewBadge: 'Formation Mastère · MSc & MBA (2 ans · Soir)',
      previewQuote:
        'Conçus en cours de soir pour diplômés et professionnels : Master Industrie 4.0 (IIT), MSc in Finance (ENG) et Mastère en Marketing Digital (ISB).',
      highlightPrograms: [
        'Master Industrie 4.0 (IIT)',
        'MSc Finance & Marketing Digital (ISB)',
      ],
      questions: [
        'Quels Mastères professionnels (FR et ENG) sont proposés en cours de soir ?',
        'Quelles sont les conditions d’admission et tarifs pour le MSc Finance ou Industrie 4.0 ?',
        'Les Mastères IIT & ISB sont-ils compatibles avec une activité professionnelle ?',
      ],
    },
    {
      id: 'preparatoire',
      label: 'Préparatoire',
      previewBadge: 'Formation Préparatoire · Cycle Préparatoire Intégré IIT (2 ans)',
      previewQuote:
        'Le Cycle Préparatoire Intégré (2 ans) offre des fondements rigoureux en mathématiques, physique et algorithmique avec accès direct au Cycle Ingénieur sans concours externe.',
      highlightPrograms: ['Cycle Préparatoire Intégré (2 ans)', 'Accès direct Ingénieur'],
      questions: [
        'Comment intégrer le Cycle Préparatoire Intégré de l’IIT sans concours national ?',
        'Quelles sections du Baccalauréat sont acceptées en Cycle Préparatoire ?',
        'Quelles spécialités d’ingénierie sont accessibles après les 2 ans de Préparatoire ?',
      ],
    },
  ];

  protected selectedTrackId = signal<string>('architecture');
  protected studioImageFailed = false;

  protected readonly activeTrack = computed(
    () =>
      this.tracks.find((track) => track.id === this.selectedTrackId()) ??
      this.tracks[0],
  );

  /* ── Footer Links ── */
  protected readonly footerNavLinks: { id: NavSection; label: string }[] = [
    { id: 'accueil', label: 'Accueil' },
    { id: 'formations', label: 'Catalogue des formations' },
    { id: 'orientation', label: 'Orientation intelligente & QCM' },
    { id: 'preinscription', label: 'Préinscription en ligne' },
  ];

  ngOnInit(): void {
    this.startAutoplay();
  }

  ngOnDestroy(): void {
    this.stopAutoplay();
  }

  /* ── Spotlight Controls ── */
  protected setSpotlightPaused(paused: boolean): void {
    this.isSpotlightPaused = paused;
    if (paused) {
      this.stopAutoplay();
    } else {
      this.startAutoplay();
    }
  }

  protected prevSlide(): void {
    this.currentSlideIndex =
      this.currentSlideIndex === 0
        ? this.totalSlides - 1
        : this.currentSlideIndex - 1;
    this.restartAutoplay();
  }

  protected nextSlide(): void {
    this.currentSlideIndex =
      this.currentSlideIndex === this.totalSlides - 1
        ? 0
        : this.currentSlideIndex + 1;
    this.restartAutoplay();
  }

  protected goToSlide(index: number): void {
    this.currentSlideIndex = index;
    this.restartAutoplay();
  }

  protected onSpotlightKeydown(event: KeyboardEvent): void {
    if (event.key === 'ArrowLeft') this.prevSlide();
    if (event.key === 'ArrowRight') this.nextSlide();
  }

  protected onSpotlightImageError(slideId: string): void {
    this.failedSpotlightImages.add(slideId);
  }

  private startAutoplay(): void {
    this.stopAutoplay();
    if (
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ) {
      return;
    }
    if (this.isSpotlightPaused) return;

    this.autoplayTimer = setInterval(() => {
      this.currentSlideIndex =
        this.currentSlideIndex === this.totalSlides - 1
          ? 0
          : this.currentSlideIndex + 1;
      this.cdr.markForCheck();
    }, 6500);
  }

  private stopAutoplay(): void {
    if (this.autoplayTimer) {
      clearInterval(this.autoplayTimer);
      this.autoplayTimer = undefined;
    }
  }

  private restartAutoplay(): void {
    if (!this.isSpotlightPaused) {
      this.startAutoplay();
    }
  }

  /* ── Navigation & Assistant ── */
  protected onNavigate(section: NavSection): void {
    const isStudent = this.userMode() === 'etudiant';
    const routeMap: Record<NavSection, string> = {
      accueil: '/',
      formations: '/formations',
      orientation: isStudent ? '/student/chatbot' : '/chatbot',
      preinscription: isStudent ? '/student/preinscription' : '/preinscription',
      demandes: '/student/dashboard',
    };
    this.router.navigate([routeMap[section]]);
  }

  protected onFilterUniversity(univ: Universite): void {
    this.router.navigate(['/formations'], { queryParams: { univ } });
  }

  protected onOpenAssistant(starterPrompt?: string): void {
    const target =
      this.userMode() === 'etudiant' ? '/student/chatbot' : '/chatbot';
    this.router.navigate(
      [target],
      starterPrompt ? { queryParams: { prompt: starterPrompt } } : undefined,
    );
  }

  protected askAboutActiveTrack(): void {
    const t = this.activeTrack();
    this.onOpenAssistant(
      `Je suis intéressé(e) par la formation « ${t.label} » (${t.highlightPrograms.join(', ')}). Peux-tu m’orienter ?`,
    );
  }

  protected onOpenAuthModal(): void {
    this.router.navigate(['/login']);
  }
}
