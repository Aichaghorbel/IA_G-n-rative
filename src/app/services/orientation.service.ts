import { Injectable, signal } from '@angular/core';

export interface Parcours {
  id: string;
  nom: string;
  universite: 'IIT' | 'ISB';
  type: 'Ingénierie' | 'Licence' | 'Master' | 'Management' | 'Architecture' | 'Préparatoire' | 'MBA';
  duree: string;
  description: string;
  debouches: string[];
  competences: string[];
  recommandePour: string[];
  placesDisponibles: number;
}

export interface QuestionQCM {
  id: number;
  universite: 'IIT' | 'ISB';
  question: string;
  domaine:
    | 'Logique & Math'
    | 'Algorithmique & Code'
    | 'Sciences & Technique'
    | 'Logique & Analyse'
    | 'Finance & Comptabilité'
    | 'Management & Stratégie';
  difficulte: 'Facile' | 'Moyen' | 'Difficile';
  options: string[];
  bonneReponseIndex: number;
  explication: string;
}

export interface ResultatQCM {
  candidatId: string;
  candidatNom: string;
  date: string;
  scoreGlobal: number; // sur 100
  scoreParDomaine: Record<string, number>;
  recommandationIA: string;
  filiereSuggeree: string;
  universiteSuggeree: 'IIT' | 'ISB';
  niveau: 'Débutant' | 'Intermédiaire' | 'Avancé' | 'Expert';
}

export interface Entretien {
  id: string;
  candidatId: string;
  candidatNom: string;
  candidatEmail: string;
  candidatPhone: string;
  date: string;
  heure: string;
  salleOuLien: string;
  enseignantNom: string;
  statut: 'Planifié' | 'En cours' | 'Terminé' | 'Annulé';
  notesEntretien?: string;
  avisEnseignant?: 'Favorable' | 'Défavorable';
  orientationFinale?: string;
}

export interface CandidatOrientation {
  id: string;
  nom: string;
  email: string;
  phone: string;
  bac: string;
  universiteSouhaitee: 'IIT' | 'ISB';
  filiereSouhaitee: string;
  statutPreinscription: 'En attente' | 'Validée' | 'À compléter';
  statutOrientation: 'En attente QCM' | 'En attente entretien' | 'Orientation validée' | 'Orientation ajustée';
  orientationValidee?: string;
  ajustementMotif?: string;
  qcmPasse: boolean;
  scoreQcm?: number;
  dateQcm?: string;
  reponsesQcm?: Record<number, number>;
  recommandationIA?: string;
  recoFiliere?: string;
  recoMatch?: number;
  dateInscription: string;
}

export interface NotificationCandidat {
  id: string;
  titre: string;
  message: string;
  date: string;
  lue: boolean;
  type: 'rdv' | 'qcm' | 'orientation' | 'info';
}

@Injectable({
  providedIn: 'root'
})
export class OrientationService {
  private readonly STORAGE_CANDIDATS = 'smartcampus_candidats';
  private readonly STORAGE_ENTRETIENS = 'smartcampus_entretiens';
  private readonly STORAGE_NOTIFS = 'smartcampus_notifs';

  parcoursList = signal<Parcours[]>([
    {
      id: 'iit-archi',
      nom: 'Architecture',
      universite: 'IIT',
      type: 'Architecture',
      duree: '6 ans (2 ans 1er cycle + 4 ans 2ème cycle)',
      description: "Le cursus académique s’étale sur six (6) années réparties sur deux cycles d’étude (deux années au premier cycle et 4 années au deuxième cycle) qui seront couronnées par l’obtention du Diplôme National d’Architecte. A travers son département architecture “International School of Architecture (ISA)“, l’Institut International de Technologie de Sfax (IIT) assure une formation de haut niveau en architecture, agréée par le Ministère de l’enseignement supérieur et de la recherche scientifique.",
      debouches: ['Architecte DPLG / Diplômé National', 'Urbaniste & Aménageur du territoire', 'Architecte d’intérieur & Designer d’espace', 'Chef de projet agence d’architecture', 'Consultant patrimoine & éco-construction'],
      competences: ['Conception architecturale & Design', 'Logiciels CAO/DAO (AutoCAD, Revit, Rhino)', 'Histoire & Théorie de l’architecture', 'Urbanisme durable & Matériaux'],
      recommandePour: ['Créativité spatiale', 'Sensibilité esthétique & artistique', 'Esprit technique et constructif'],
      placesDisponibles: 40
    },
    {
      id: 'iit-ingenierie',
      nom: 'Ingénierie',
      universite: 'IIT',
      type: 'Ingénierie',
      duree: '3 ans (après Prépa/Licence) ou 5 ans intégré',
      description: "L’ingénieur est un professionnel apte à analyser des problèmes complexes, concevoir des plans ou des processus, exécuter et contrôler la réalisation des tâches selon des objectifs et besoins demandés. L’institut International de Technologie de Sfax propose à ses étudiants des formations solides en ingénierie dans les filières du Génie civil, Génie Informatique, Génie des Procédés, Génie Mécanique, Génie des Télécommunications et Génie Industriel. Ces formations sont bien développées et adaptées selon les besoins futurs du marché national et international et visent à préparer nos ingénieurs à confronter et résoudre les différents problèmes rencontrés. L’école d’ingénieur IIT offre à ses étudiants des formations en ingénierie de haut niveau. Ayant pour objectif l’enrichissement des compétences de ses étudiants, IIT organise des formations spécifiques et des évènements avec la collaboration de ses partenaires nationaux et internationaux.",
      debouches: ['Génie Logiciel / Informatique & IA', 'Génie Civil & BTP', 'Génie Mécanique & Robotique', 'Génie des Télécommunications & IoT', 'Génie des Procédés & Industriel'],
      competences: ['Résolution de problèmes complexes', 'Conception et calcul d’ingénierie avancée', 'Gestion de projets industriels & agiles', 'Innovation technologique & Industrie 4.0'],
      recommandePour: ['Esprit d’analyse', 'Innovation & R&D', 'Leadership technique', 'Passion industrielle'],
      placesDisponibles: 120
    },
    {
      id: 'iit-licence',
      nom: 'Licence en Technologie & Informatique',
      universite: 'IIT',
      type: 'Licence',
      duree: '3 ans',
      description: "Formation universitaire professionnalisante permettant d'acquérir les compétences fondamentales et appliquées en informatique, technologies numériques, développement web/mobile et systèmes d'information, préparant à une insertion professionnelle immédiate ou à la poursuite en cycle ingénieur.",
      debouches: ['Développeur d’Applications Web & Mobile', 'Administrateur Systèmes & Réseaux', 'Technicien Supérieur Informatique', 'Accès direct sur concours au Cycle Ingénieur'],
      competences: ['Développement Web & Mobile', 'Bases de données & SQL', 'Réseaux & Sécurité de base', 'Génie logiciel appliqué'],
      recommandePour: ['Bac Scientifique, Technique ou Économie', 'Goût pour la pratique informatique', 'Pragmatisme technique'],
      placesDisponibles: 60
    },
    {
      id: 'iit-prepa',
      nom: 'Cycle Préparatoire',
      universite: 'IIT',
      type: 'Préparatoire',
      duree: '2 ans',
      description: "Accessible à partir d’un baccalauréat scientifique (mathématiques, sciences expérimentales, informatique ou technique), le cycle préparatoire aux grandes écoles d’ingénieurs occupe une place de choix à l’IIT qui fournit à ses étudiants une formation scientifique solide et un encadrement rigoureux assurés par les professeurs les plus compétents de la région.",
      debouches: ['Admission aux Grandes Écoles d’Ingénieurs', 'Cycle Ingénieur Génie Logiciel / Informatique', 'Cycle Ingénieur Génie Civil', 'Cycle Ingénieur Génie Mécanique & Robotique', 'Cycle Ingénieur Télécommunications & Procédés'],
      competences: ['Mathématiques supérieures & Analyse', 'Physique générale & Mécanique', 'Algorithmique & C/Python', 'Sciences industrielles de l’ingénieur'],
      recommandePour: ['Bac Scientifique / Technique', 'Rigueur analytique', 'Capacité de travail soutenue', 'Ambition d’ingénierie'],
      placesDisponibles: 80
    },
    {
      id: 'isb-licence',
      nom: 'Licence',
      universite: 'ISB',
      type: 'Licence',
      duree: '3 ans',
      description: "La Licence à l’International School of Business (ISB) offre une formation d’excellence en sciences de gestion, finance d'entreprise, marketing digital, comptabilité et management. Elle développe l’esprit d’initiative, la rigueur analytique et prépare les futurs cadres aux défis du marché national et international.",
      debouches: ['Chargé de Clientèle Banque & Assurance', 'Responsable Marketing & Communication', 'Comptable & Contrôleur de Gestion Junior', 'Gestionnaire des Ressources Humaines', 'Poursuite d’études en Master Spécialisé ou MBA'],
      competences: ['Gestion d’entreprise & Management', 'Comptabilité financière & analytique', 'Stratégie marketing & vente', 'Analyse quantitative & Outils informatiques'],
      recommandePour: ['Bac Économie & Gestion, Scientifique ou Lettres', 'Sens de la communication & leadership', 'Goût pour le monde des affaires'],
      placesDisponibles: 80
    },
    {
      id: 'isb-master',
      nom: 'Master',
      universite: 'ISB',
      type: 'Master',
      duree: '2 ans',
      description: "Le cursus Master à l’ISB permet d'acquérir une haute expertise stratégique et opérationnelle dans les domaines de pointe : Finance d’entreprise et de marché, Audit et contrôle de gestion, Marketing Digital et Business Analytics. Il vise à propulser les diplômés vers des fonctions de direction et de conseil.",
      debouches: ['Auditeur Financier & Bancaire Senior', 'Directeur Marketing & E-Commerce', 'Consultant en Management & Organisation', 'Data Analyst & Responsable Business Intelligence', 'Directeur Administratif et Financier (DAF)'],
      competences: ['Modélisation & Ingénierie financière', 'Pilotage stratégique de la performance', 'Marketing omnicanal & Growth Hacking', 'Management agile & Prise de décision data-driven'],
      recommandePour: ['Titulaires de Licence en Gestion, Économie ou équivalent', 'Capacité de leadership et de synthèse', 'Ambition managériale et stratégique'],
      placesDisponibles: 50
    },
    {
      id: 'isb-mba',
      nom: 'MBA',
      universite: 'ISB',
      type: 'MBA',
      duree: '1 à 2 ans',
      description: "Le Master of Business Administration (MBA) de l’ISB est un programme d'élite destiné aux cadres, dirigeants et entrepreneurs. Axé sur le leadership global, la gouvernance d’entreprise, la négociation stratégique et l'innovation entrepreneuriale, il offre une vision 360° du management international.",
      debouches: ['Directeur Général (CEO) / Executive Manager', 'Entrepreneur & Fondateur de Startup', 'Senior Consultant en Stratégie Internationale', 'Directeur des Opérations (COO) & Business Developer', 'Leader de la Transformation Numérique'],
      competences: ['Leadership exécutif & Gouvernance d’entreprise', 'Stratégie globale & Fusions-Acquisitions', 'Négociation complexe & Management international', 'Innovation disruptive & Entrepreneuriat'],
      recommandePour: ['Professionnels, cadres d’entreprise et entrepreneurs', 'Diplômés à fort potentiel d’évolution', 'Volonté de piloter des projets d’envergure internationale'],
      placesDisponibles: 30
    }
  ]);

  questionsIIT: QuestionQCM[] = [
    {
      id: 1,
      universite: 'IIT',
      question: "Quelle est la structure de données la plus appropriée pour implémenter un mécanisme FIFO (First In, First Out) ?",
      domaine: 'Algorithmique & Code',
      difficulte: 'Facile',
      options: ['Une Pile (Stack)', 'Une File (Queue)', 'Un Arbre binaire', 'Un Tableau statique'],
      bonneReponseIndex: 1,
      explication: 'Une File (Queue) fonctionne sur le principe FIFO : le premier élément inséré est le premier retiré.'
    },
    {
      id: 2,
      universite: 'IIT',
      question: "Dans le cadre d'un calcul de résistance de structure, que caractérise le module de Young d'un matériau ?",
      domaine: 'Sciences & Technique',
      difficulte: 'Moyen',
      options: ['Sa résistance thermique', 'Son élasticité linéaire sous traction', 'Sa conductivité électrique', 'Son point de fusion'],
      bonneReponseIndex: 1,
      explication: 'Le module de Young mesure la rigidité d’un matériau élastique isotrope.'
    },
    {
      id: 3,
      universite: 'IIT',
      question: "Quelle complexité temporelle algorithmique minimale caractérise un tri par comparaison optimal dans le pire des cas ?",
      domaine: 'Algorithmique & Code',
      difficulte: 'Difficile',
      options: ['O(N)', 'O(N log N)', 'O(N²)', 'O(log N)'],
      bonneReponseIndex: 1,
      explication: 'La borne inférieure d’un tri par comparaison est mathématiquement prouvée égale à Ω(N log N).'
    },
    {
      id: 4,
      universite: 'IIT',
      question: "Si trois machines identiques fabriquent 18 pièces en 6 heures, combien de pièces 5 machines fabriqueront-elles en 4 heures ?",
      domaine: 'Logique & Math',
      difficulte: 'Moyen',
      options: ['20 pièces', '25 pièces', '18 pièces', '30 pièces'],
      bonneReponseIndex: 0,
      explication: '1 machine fait 1 pièce/heure (18 / (3x6)). En 4h, 5 machines font : 5 x 4 x 1 = 20 pièces.'
    },
    {
      id: 5,
      universite: 'IIT',
      question: "En réseaux informatiques, quel protocole garantit une transmission fiable des données avec contrôle d'erreur et accusé de réception ?",
      domaine: 'Sciences & Technique',
      difficulte: 'Moyen',
      options: ['UDP', 'TCP', 'ICMP', 'ARP'],
      bonneReponseIndex: 1,
      explication: 'TCP (Transmission Control Protocol) assure la fiabilité, l’ordonnancement et l’accusé de réception des paquets.'
    }
  ];

  questionsISB: QuestionQCM[] = [
    {
      id: 101,
      universite: 'ISB',
      question: "Une entreprise réalise un chiffre d'affaires de 200 000 DT avec des charges fixes de 50 000 DT et une marge sur coût variable de 40%. Quel est son résultat d'exploitation ?",
      domaine: 'Finance & Comptabilité',
      difficulte: 'Moyen',
      options: ['30 000 DT', '50 000 DT', '80 000 DT', '20 000 DT'],
      bonneReponseIndex: 0,
      explication: 'Marge = 200 000 x 40% = 80 000 DT. Résultat = 80 000 - 50 000 = 30 000 DT.'
    },
    {
      id: 102,
      universite: 'ISB',
      question: "Dans une matrice d'analyse stratégique SWOT, que représente la lettre « O » ?",
      domaine: 'Management & Stratégie',
      difficulte: 'Facile',
      options: ['Objectifs internes', 'Opportunités externes', 'Opérations financières', 'Optimisation des coûts'],
      bonneReponseIndex: 1,
      explication: 'SWOT signifie Strengths (Forces), Weaknesses (Faiblesses), Opportunities (Opportunités) et Threats (Menaces).'
    },
    {
      id: 103,
      universite: 'ISB',
      question: "Quel ratio financier mesure la rentabilité nette générée par rapport aux capitaux propres investis par les actionnaires ?",
      domaine: 'Finance & Comptabilité',
      difficulte: 'Moyen',
      options: ['ROE (Return on Equity)', 'EBITDA', 'BFR (Besoin en Fonds de Roulement)', 'VAN'],
      bonneReponseIndex: 0,
      explication: 'Le ROE (Return on Equity) rapporte le résultat net au montant des capitaux propres.'
    },
    {
      id: 104,
      universite: 'ISB',
      question: "En marketing digital et e-commerce, que désigne l'indicateur « CAC » ?",
      domaine: 'Management & Stratégie',
      difficulte: 'Moyen',
      options: ['Chiffre d’Affaires Consolidé', 'Coût d’Acquisition Client', 'Capacité d’Autofinancement', 'Crédit Accordé au Client'],
      bonneReponseIndex: 1,
      explication: 'Le CAC mesure le coût moyen dépensé en marketing et ventes pour acquérir un nouveau client.'
    },
    {
      id: 105,
      universite: 'ISB',
      question: "Un article est vendu 120 DT après une remise de 20%. Quel était son prix initial avant la remise ?",
      domaine: 'Logique & Analyse',
      difficulte: 'Moyen',
      options: ['144 DT', '150 DT', '140 DT', '160 DT'],
      bonneReponseIndex: 1,
      explication: 'Prix après remise = Prix initial x 0,80 = 120 DT, donc Prix initial = 120 / 0,80 = 150 DT.'
    }
  ];

  get questionsQCM(): QuestionQCM[] {
    return [...this.questionsIIT, ...this.questionsISB];
  }

  getQuestionsForUniversite(uni: 'IIT' | 'ISB'): QuestionQCM[] {
    return uni === 'ISB' ? this.questionsISB : this.questionsIIT;
  }

  getModulesForUniversite(uni: 'IIT' | 'ISB'): { key: string; label: string }[] {
    if (uni === 'ISB') {
      return [
        { key: 'Logique & Analyse', label: 'Logique & Analyse' },
        { key: 'Finance & Comptabilité', label: 'Finance & Compta' },
        { key: 'Management & Stratégie', label: 'Management & Stratégie' }
      ];
    }
    return [
      { key: 'Logique & Math', label: 'Logique & Math' },
      { key: 'Algorithmique & Code', label: 'Algo & Code' },
      { key: 'Sciences & Technique', label: 'Sciences & Tech' }
    ];
  }

  candidats = signal<CandidatOrientation[]>([]);
  entretiens = signal<Entretien[]>([]);
  notifications = signal<NotificationCandidat[]>([]);
  dernierResultatQCM = signal<ResultatQCM | null>(null);
  selectedEntretienModal = signal<Entretien | null>(null);

  ouvrirModalEntretien(entretien?: Entretien | null) {
    if (entretien) {
      this.selectedEntretienModal.set(entretien);
    } else {
      const list = this.entretiens();
      const ent = list.find(e => e.candidatEmail === 'student@test.com' || e.candidatNom.toLowerCase().includes('sophie')) || list[0] || null;
      this.selectedEntretienModal.set(ent);
    }
  }

  fermerModalEntretien() {
    this.selectedEntretienModal.set(null);
  }

  constructor() {
    this.initialiserDonnees();
  }

  private initialiserDonnees() {
    // 1. Candidats
    const savedCandidats = localStorage.getItem(this.STORAGE_CANDIDATS);
    if (savedCandidats) {
      try {
        const parsed: CandidatOrientation[] = JSON.parse(savedCandidats);
        // Assurer que les candidats ont les champs de recommandation ou initialiser la liste
        if (parsed.length >= 4 && parsed.some(c => c.recoFiliere)) {
          // Nettoyer d'anciennes réponses IIT (id < 100) si le candidat est ISB
          const normalized = parsed.map(c => {
            if (c.universiteSouhaitee === 'ISB' && c.reponsesQcm) {
              const hasOldKeys = Object.keys(c.reponsesQcm).some(k => Number(k) < 100);
              if (hasOldKeys) {
                const { reponsesQcm, ...rest } = c;
                return rest as CandidatOrientation;
              }
            }
            return c;
          });
          this.candidats.set(normalized);
        } else {
          this.resetMockCandidats();
        }
      } catch {
        this.resetMockCandidats();
      }
    } else {
      this.resetMockCandidats();
    }

    // 2. Entretiens
    const savedEntretiens = localStorage.getItem(this.STORAGE_ENTRETIENS);
    if (savedEntretiens) {
      try {
        const parsedEntretiens: Entretien[] = JSON.parse(savedEntretiens);
        const normalizedEntretiens = parsedEntretiens.map(e =>
          (e.avisEnseignant as string) === 'À réorienter'
            ? { ...e, avisEnseignant: 'Favorable' as const }
            : e
        );
        this.entretiens.set(normalizedEntretiens);
        if (normalizedEntretiens.some((e, i) => e !== parsedEntretiens[i])) {
          this.sauvegarderEntretiens();
        }
      } catch {
        this.resetMockEntretiens();
      }
    } else {
      this.resetMockEntretiens();
    }

    // 3. Notifications
    const savedNotifs = localStorage.getItem(this.STORAGE_NOTIFS);
    if (savedNotifs) {
      try {
        this.notifications.set(JSON.parse(savedNotifs));
      } catch {
        this.resetMockNotifications();
      }
    } else {
      this.resetMockNotifications();
    }
  }

  private resetMockCandidats() {
    const list: CandidatOrientation[] = [
      {
        id: 'cand-001',
        nom: 'Sophie Martin',
        email: 'student@test.com',
        phone: '+216 55 123 456',
        bac: 'Baccalauréat Mathématiques (Mention Très Bien)',
        universiteSouhaitee: 'IIT',
        filiereSouhaitee: 'Génie Logiciel & Informatique',
        statutPreinscription: 'Validée',
        statutOrientation: 'Orientation validée',
        orientationValidee: 'Data Science & IA (IIT)',
        qcmPasse: true,
        scoreQcm: 82,
        reponsesQcm: { 1: 1, 2: 0, 3: 1, 4: 0, 5: 1 },
        recoFiliere: 'Data Science & IA',
        recoMatch: 87,
        recommandationIA: 'Excellente aptitude en algorithmique et analyse quantitative. Parcours Data Science & IA recommandé.',
        dateInscription: '10/06/2024'
      },
      {
        id: 'cand-002',
        nom: 'Lucas Bernard',
        email: 'lucas.b@example.com',
        phone: '+216 22 987 654',
        bac: 'Baccalauréat Sciences Expérimentales',
        universiteSouhaitee: 'ISB',
        filiereSouhaitee: 'Finance, Banque & Fintech',
        statutPreinscription: 'Validée',
        statutOrientation: 'Orientation validée',
        orientationValidee: 'Finance, Banque & Fintech (ISB)',
        qcmPasse: true,
        scoreQcm: 76,
        reponsesQcm: { 101: 0, 102: 1, 103: 0, 104: 0, 105: 1 },
        recoFiliere: 'Finance',
        recoMatch: 81,
        recommandationIA: 'Profil analytique solide avec excellente prédisposition financière.',
        dateInscription: '11/06/2024'
      },
      {
        id: 'cand-003',
        nom: 'Hugo Dubois',
        email: 'hugo.d@example.com',
        phone: '+216 50 333 444',
        bac: 'Baccalauréat Technique',
        universiteSouhaitee: 'IIT',
        filiereSouhaitee: 'Génie Civil',
        statutPreinscription: 'Validée',
        statutOrientation: 'En attente entretien',
        qcmPasse: true,
        scoreQcm: 64,
        reponsesQcm: { 1: 1, 2: 1, 3: 2, 4: 1, 5: 1 },
        recoFiliere: 'Génie Civil',
        recoMatch: 68,
        recommandationIA: 'Bases solides en calculs de structure et modélisation.',
        dateInscription: '13/06/2024'
      },
      {
        id: 'cand-004',
        nom: 'Farah Trabelsi',
        email: 'farah.t@example.com',
        phone: '+216 20 444 555',
        bac: 'Baccalauréat Informatique',
        universiteSouhaitee: 'IIT',
        filiereSouhaitee: 'Génie Logiciel & Informatique',
        statutPreinscription: 'Validée',
        statutOrientation: 'Orientation validée',
        orientationValidee: 'Génie Logiciel & Informatique (IIT)',
        qcmPasse: true,
        scoreQcm: 89,
        reponsesQcm: { 1: 1, 2: 1, 3: 1, 4: 0, 5: 1 },
        recoFiliere: 'Génie Logiciel',
        recoMatch: 91,
        recommandationIA: 'Excellente maîtrise du génie logiciel et de la conception architecturale.',
        dateInscription: '14/06/2024'
      },
      {
        id: 'cand-005',
        nom: 'Youssef Mezni',
        email: 'youssef.m@example.com',
        phone: '+216 98 777 888',
        bac: 'Baccalauréat Économie & Gestion',
        universiteSouhaitee: 'ISB',
        filiereSouhaitee: 'Business Analytics & Big Data',
        statutPreinscription: 'Validée',
        statutOrientation: 'Orientation ajustée',
        orientationValidee: 'Management International (ISB)',
        ajustementMotif: 'Orientation ajustée vers Management International au vu du profil managérial et relationnel.',
        qcmPasse: true,
        scoreQcm: 42,
        reponsesQcm: { 101: 1, 102: 1, 103: 2, 104: 1, 105: 0 },
        recoFiliere: 'Management International',
        recoMatch: 74,
        recommandationIA: 'Bonne fibre managériale, consolidation requise en analyse mathématique.',
        dateInscription: '15/06/2024'
      },
      {
        id: 'cand-006',
        nom: 'Amine Chaabane',
        email: 'amine.c@example.com',
        phone: '+216 54 111 333',
        bac: 'Baccalauréat Technique',
        universiteSouhaitee: 'IIT',
        filiereSouhaitee: 'Génie Mécanique & Robotique',
        statutPreinscription: 'Validée',
        statutOrientation: 'En attente entretien',
        qcmPasse: true,
        scoreQcm: 69,
        reponsesQcm: { 1: 0, 2: 1, 3: 1, 4: 0, 5: 0 },
        recoFiliere: 'Mécatronique',
        recoMatch: 77,
        recommandationIA: 'Aptitude marquée pour les systèmes embarqués et l’automatisme.',
        dateInscription: '16/06/2024'
      },
      {
        id: 'cand-007',
        nom: 'Sami Ayari',
        email: 'sami.a@example.com',
        phone: '+216 28 999 111',
        bac: 'Baccalauréat Lettres',
        universiteSouhaitee: 'ISB',
        filiereSouhaitee: 'Marketing Digital & E-Commerce',
        statutPreinscription: 'À compléter',
        statutOrientation: 'Orientation ajustée',
        ajustementMotif: 'Remise à niveau recommandée avant réorientation.',
        qcmPasse: true,
        scoreQcm: 15,
        reponsesQcm: { 101: 1, 102: 0, 103: 1, 104: 0, 105: 1 },
        recoFiliere: 'Bases Digital & Gestion',
        recoMatch: 35,
        recommandationIA: 'Score insuffisant pour admission directe. Module préparatoire nécessaire.',
        dateInscription: '17/06/2024'
      },
      {
        id: 'cand-008',
        nom: 'Emma Petit',
        email: 'emma.p@example.com',
        phone: '+216 99 111 222',
        bac: 'Baccalauréat Économie & Gestion',
        universiteSouhaitee: 'ISB',
        filiereSouhaitee: 'Finance, Banque & Fintech',
        statutPreinscription: 'En attente',
        statutOrientation: 'En attente QCM',
        qcmPasse: false,
        recommandationIA: 'En attente de complétion du QCM adaptatif pour analyse des compétences.',
        dateInscription: '18/06/2024'
      }
    ];
    this.candidats.set(list);
    this.sauvegarderCandidats();
  }

  private resetMockEntretiens() {
    const list: Entretien[] = [
      {
        id: 'ent-1',
        candidatId: 'cand-001',
        candidatNom: 'Sophie Martin',
        candidatEmail: 'student@test.com',
        candidatPhone: '+216 55 123 456',
        date: '15/06/2024',
        heure: '10:30',
        salleOuLien: 'Salle B12 - Campus IIT / Lien Visio Google Meet',
        enseignantNom: 'Prof. Dupont',
        statut: 'Terminé',
        notesEntretien: 'Candidate très motivée, a déjà réalisé des projets Angular/Python personnels.',
        avisEnseignant: 'Favorable',
        orientationFinale: 'Génie Logiciel & Informatique (IIT)'
      },
      {
        id: 'ent-2',
        candidatId: 'cand-002',
        candidatNom: 'Lucas Bernard',
        candidatEmail: 'lucas.b@example.com',
        candidatPhone: '+216 22 987 654',
        date: '18/06/2024',
        heure: '14:00',
        salleOuLien: 'Bureau Orientation 2 - Campus ISB',
        enseignantNom: 'Prof. Dupont',
        statut: 'Planifié'
      }
    ];
    this.entretiens.set(list);
    this.sauvegarderEntretiens();
  }

  private resetMockNotifications() {
    const list: NotificationCandidat[] = [
      {
        id: 'notif-1',
        titre: 'Entretien d’orientation confirmé',
        message: 'Votre entretien avec Prof. Dupont est programmé pour le 15/06/2024 à 10:30 (Salle B12 / Visio).',
        date: 'Il y a 2 jours',
        lue: false,
        type: 'rdv'
      },
      {
        id: 'notif-2',
        titre: 'Résultats de votre QCM adaptatif',
        message: 'Félicitations ! Vous avez obtenu 85/100. Vos recommandations personnalisées sont prêtes.',
        date: 'Il y a 3 jours',
        lue: true,
        type: 'qcm'
      },
      {
        id: 'notif-3',
        titre: 'Préinscription bien reçue',
        message: 'Votre dossier de préinscription pour SmartCampus IIT/ISB a été enregistré avec succès.',
        date: 'Il y a 5 jours',
        lue: true,
        type: 'info'
      }
    ];
    this.notifications.set(list);
    this.sauvegarderNotifs();
  }

  // Action Candidat : Faire la préinscription
  enregistrerPreinscription(data: {
    nom: string;
    email: string;
    phone: string;
    bac: string;
    universite: 'IIT' | 'ISB';
    filiere: string;
  }) {
    const newCand: CandidatOrientation = {
      id: 'cand-' + Date.now(),
      nom: data.nom,
      email: data.email,
      phone: data.phone,
      bac: data.bac,
      universiteSouhaitee: data.universite,
      filiereSouhaitee: data.filiere,
      statutPreinscription: 'Validée',
      statutOrientation: 'En attente QCM',
      qcmPasse: false,
      dateInscription: new Date().toLocaleDateString('fr-FR')
    };

    this.candidats.update(list => [newCand, ...list]);
    this.sauvegarderCandidats();

    // Notif candidat
    this.ajouterNotification({
      titre: 'Préinscription validée',
      message: `Votre candidature pour le parcours ${data.filiere} (${data.universite}) est bien enregistrée. Passez maintenant le QCM adaptatif !`,
      type: 'info'
    });
  }

  // Action Candidat : Soumettre le QCM adaptatif selon l'université souhaitée
  soumettreQCM(reponses: Record<number, number>, nomCandidat: string, universite: 'IIT' | 'ISB' = 'IIT'): ResultatQCM {
    const questions = this.getQuestionsForUniversite(universite);
    let score = 0;
    const scoresDomaine: Record<string, { total: number; reussi: number }> = {};

    questions.forEach(q => {
      if (!scoresDomaine[q.domaine]) {
        scoresDomaine[q.domaine] = { total: 0, reussi: 0 };
      }
      scoresDomaine[q.domaine].total += 1;

      if (reponses[q.id] === q.bonneReponseIndex) {
        score += Math.round(100 / questions.length);
        scoresDomaine[q.domaine].reussi += 1;
      }
    });

    const domaineStats: Record<string, number> = {};
    Object.keys(scoresDomaine).forEach(d => {
      domaineStats[d] = Math.round((scoresDomaine[d].reussi / scoresDomaine[d].total) * 100);
    });

    let recommandation = '';
    let filiereSuggeree = universite === 'IIT' ? 'Génie Logiciel & Informatique' : 'Finance, Banque & Fintech';
    let universiteSuggeree: 'IIT' | 'ISB' = universite;

    if (universite === 'IIT') {
      if (score >= 80) {
        recommandation = 'Excellentes aptitudes analytiques et logiques. Profil idéal pour les filières d’Ingénierie avancée (Génie Logiciel / IA / Robotique) à l’IIT.';
        filiereSuggeree = 'Génie Logiciel & Informatique';
      } else if (score >= 50) {
        recommandation = 'Bon socle technique et scientifique. Adapté aux parcours Licence ou Cycle Préparatoire à l’IIT.';
        filiereSuggeree = 'Licence en Technologie & Informatique';
      } else {
        recommandation = 'Consolidation recommandée en mathématiques et algorithmique pour intégrer sereinement l’IIT.';
        filiereSuggeree = 'Cycle Préparatoire IIT';
      }
    } else {
      if (score >= 80) {
        recommandation = 'Très fort potentiel analytique, financier et managérial. Idéal pour les filières Master, Finance ou Business Analytics à l’ISB.';
        filiereSuggeree = 'Finance, Banque & Fintech';
      } else if (score >= 50) {
        recommandation = 'Bon équilibre gestion et stratégie. Adapté aux parcours Licence en Management ou Marketing Digital à l’ISB.';
        filiereSuggeree = 'Management International';
      } else {
        recommandation = 'Bon potentiel relationnel. Recommandé pour un parcours Licence en Gestion à l’ISB avec accompagnement méthodologique.';
        filiereSuggeree = 'Licence en Gestion';
      }
    }

    const resultat: ResultatQCM = {
      candidatId: 'cand-current',
      candidatNom: nomCandidat,
      date: new Date().toLocaleDateString('fr-FR'),
      scoreGlobal: score,
      scoreParDomaine: domaineStats,
      recommandationIA: recommandation,
      filiereSuggeree,
      universiteSuggeree,
      niveau: score >= 80 ? 'Avancé' : (score >= 50 ? 'Intermédiaire' : 'Débutant')
    };

    this.dernierResultatQCM.set(resultat);

    // Mettre à jour si candidat existant
    this.candidats.update(list => list.map(c => {
      if (c.email.toLowerCase().includes('student') || c.nom.toLowerCase().includes(nomCandidat.toLowerCase())) {
        return {
          ...c,
          qcmPasse: true,
          scoreQcm: score,
          dateQcm: resultat.date,
          reponsesQcm: { ...reponses },
          recommandationIA: recommandation,
          statutOrientation: 'En attente entretien'
        };
      }
      return c;
    }));
    this.sauvegarderCandidats();

    this.ajouterNotification({
      titre: `QCM complété - Score: ${score}%`,
      message: `Votre test est analysé par l’IA. Filière recommandée : ${filiereSuggeree} (${universiteSuggeree}).`,
      type: 'qcm'
    });

    return resultat;
  }

  // Action Enseignant : Valider l'orientation
  validerOrientation(candidatId: string, filiereChoisie: string) {
    this.candidats.update(list => list.map(c => {
      if (c.id === candidatId) {
        return {
          ...c,
          statutOrientation: 'Orientation validée',
          orientationValidee: filiereChoisie
        };
      }
      return c;
    }));
    this.sauvegarderCandidats();

    this.ajouterNotification({
      titre: 'Orientation confirmée par l’enseignant',
      message: `Votre orientation définitive en ${filiereChoisie} a été validée avec succès.`,
      type: 'orientation'
    });
  }

  // Action Enseignant : Ajuster l'orientation
  ajusterOrientation(candidatId: string, nouvelleFiliere: string, motif: string) {
    this.candidats.update(list => list.map(c => {
      if (c.id === candidatId) {
        return {
          ...c,
          statutOrientation: 'Orientation ajustée',
          orientationValidee: nouvelleFiliere,
          ajustementMotif: motif
        };
      }
      return c;
    }));
    this.sauvegarderCandidats();

    this.ajouterNotification({
      titre: 'Orientation réajustée',
      message: `Votre orientation a été optimisée vers ${nouvelleFiliere}. Conseil de l'enseignant : ${motif}`,
      type: 'orientation'
    });
  }

  // Action Enseignant : Planifier un entretien
  planifierEntretien(candidat: CandidatOrientation, date: string, heure: string, lieu: string, enseignant: string) {
    const nouvelEntretien: Entretien = {
      id: 'ent-' + Date.now(),
      candidatId: candidat.id,
      candidatNom: candidat.nom,
      candidatEmail: candidat.email,
      candidatPhone: candidat.phone,
      date,
      heure,
      salleOuLien: lieu,
      enseignantNom: enseignant,
      statut: 'Planifié'
    };

    this.entretiens.update(list => [nouvelEntretien, ...list]);
    this.sauvegarderEntretiens();

    this.ajouterNotification({
      titre: 'Nouveau rendez-vous planifié',
      message: `Entretien d’orientation fixé au ${date} à ${heure} (${lieu}) avec ${enseignant}.`,
      type: 'rdv'
    });
  }

  // Action Enseignant : Mener et clôturer l'entretien
  conclureEntretien(entretienId: string, avis: 'Favorable' | 'Défavorable', notes: string, orientationFinale: string) {
    let candId = '';
    this.entretiens.update(list => list.map(e => {
      if (e.id === entretienId) {
        candId = e.candidatId;
        return {
          ...e,
          statut: 'Terminé',
          avisEnseignant: avis,
          notesEntretien: notes,
          orientationFinale
        };
      }
      return e;
    }));
    this.sauvegarderEntretiens();

    if (candId && avis === 'Favorable') {
      this.validerOrientation(candId, orientationFinale);
    }
  }

  ajouterNotification(n: { titre: string; message: string; type: 'rdv' | 'qcm' | 'orientation' | 'info' }) {
    const nouvelle: NotificationCandidat = {
      id: 'notif-' + Date.now(),
      titre: n.titre,
      message: n.message,
      date: "À l'instant",
      lue: false,
      type: n.type
    };
    this.notifications.update(list => [nouvelle, ...list]);
    this.sauvegarderNotifs();
  }

  marquerNotifLue(id: string) {
    this.notifications.update(list => list.map(notif => notif.id === id ? { ...notif, lue: true } : notif));
    this.sauvegarderNotifs();
  }

  marquerToutesNotifsLues() {
    this.notifications.update(list => list.map(n => ({ ...n, lue: true })));
    this.sauvegarderNotifs();
  }

  private sauvegarderCandidats() {
    localStorage.setItem(this.STORAGE_CANDIDATS, JSON.stringify(this.candidats()));
  }

  private sauvegarderEntretiens() {
    localStorage.setItem(this.STORAGE_ENTRETIENS, JSON.stringify(this.entretiens()));
  }

  private sauvegarderNotifs() {
    localStorage.setItem(this.STORAGE_NOTIFS, JSON.stringify(this.notifications()));
  }
}

