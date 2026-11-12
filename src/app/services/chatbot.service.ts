import { Injectable, signal, computed } from '@angular/core';

/* ─── Types ─────────────────────────────────────────────────────────────── */
export type MessageType = 'normal' | 'question' | 'resume' | 'form';
export type FormType = 'attestation' | 'reclamation' | 'stage' | 'absence';

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'email' | 'number' | 'date' | 'select' | 'textarea';
  placeholder?: string;
  options?: string[];
  required?: boolean;
}

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  type?: MessageType;
  source?: string;
  suggestions?: string[];
  formType?: FormType;
  formFields?: FormField[];
  formSubmitted?: boolean;
  formData?: Record<string, string>;
}

export interface Conversation {
  id: string;
  title: string;
  date: string;
  isFavorite?: boolean;
  messages: Message[];
}

/* ─── Pure helpers ──────────────────────────────────────────────────────── */
export function getSuggestions(type: MessageType): string[] {
  if (type === 'question' || type === 'form')
    return ['Quels documents fournir ?', 'Quelles sont les dates limites ?', 'Qui contacter ?'];
  return ['Aide avec mes devoirs', 'Question administrative', 'Résumer un document'];
}

export function getSource(type: MessageType): string {
  if (type === 'question' || type === 'form') return 'Source : Règlement intérieur, Art. 15';
  if (type === 'resume') return "Source : Guide de l'étudiant, p. 42";
  return 'Source : Base de connaissances UniHelp';
}

export function getFormFields(type: FormType): FormField[] {
  switch (type) {
    case 'attestation':
      return [
        { name: 'nom',        label: 'Nom complet',           type: 'text',     required: true, placeholder: 'Ex: Jean Dupont' },
        { name: 'filiere',    label: 'Filière',               type: 'text',     required: true, placeholder: 'Ex: Informatique L3' },
        { name: 'annee',      label: 'Année universitaire',   type: 'select',   required: true, options: ['2023-2024','2024-2025','2025-2026'] },
        { name: 'numEtudiant',label: 'N° étudiant',           type: 'text',     required: true, placeholder: 'Ex: 20240156' },
        { name: 'motif',      label: 'Motif',                 type: 'textarea', required: true, placeholder: 'Pourquoi avez-vous besoin de cette attestation ?' },
      ];
    case 'reclamation':
      return [
        { name: 'nom',         label: 'Nom complet',          type: 'text',     required: true },
        { name: 'matiere',     label: 'Matière',              type: 'text',     required: true },
        { name: 'typeEval',    label: "Type d'évaluation",    type: 'select',   required: true, options: ['Examen','Contrôle continu','TP','TD'] },
        { name: 'dateEpreuve', label: "Date de l'épreuve",    type: 'date',     required: true },
        { name: 'noteObtenue', label: 'Note obtenue',         type: 'number',   required: true },
        { name: 'noteAttendue',label: 'Note attendue',        type: 'number',   required: true },
        { name: 'motif',       label: 'Motif de réclamation', type: 'textarea', required: true, placeholder: 'Expliquez précisément les raisons...' },
      ];
    case 'stage':
      return [
        { name: 'nom',        label: 'Nom complet',           type: 'text',     required: true },
        { name: 'filiere',    label: 'Filière',               type: 'text',     required: true },
        { name: 'entreprise', label: 'Entreprise / Organisme',type: 'text',     required: true },
        { name: 'periode',    label: 'Période souhaitée',     type: 'text',     required: true, placeholder: 'Ex: du 01/06 au 31/08' },
        { name: 'objet',      label: 'Objet / Description',   type: 'textarea', required: true, placeholder: 'Décrivez brièvement le stage...' },
      ];
    case 'absence':
      return [
        { name: 'nom',     label: 'Nom complet',             type: 'text',     required: true },
        { name: 'dates',   label: "Date(s) d'absence",       type: 'text',     required: true, placeholder: 'Ex: 12 et 13 Octobre' },
        { name: 'matieres',label: 'Matière(s) concernée(s)', type: 'text',     required: true },
        { name: 'motif',   label: 'Motif',                   type: 'select',   required: true, options: ['Maladie','Raison familiale','Convocation officielle','Autre'] },
        { name: 'details', label: 'Détails supplémentaires', type: 'textarea', required: true },
      ];
    default:
      return [];
  }
}

export function generateDocument(formType: FormType, data: Record<string, string>): string {
  if (formType === 'attestation') {
    return `Voici votre demande d'attestation de scolarité formatée :\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nObjet : Demande d'attestation de scolarité\n\nMadame, Monsieur,\n\nJe soussigné(e) ${data['nom'] || '[Nom]'}, étudiant(e) en ${data['annee'] || '[Année]'} ${data['filiere'] || '[Filière]'} (N° étudiant : ${data['numEtudiant'] || '[N°]'}), me permets de solliciter auprès de vos services la délivrance d'une attestation de scolarité pour l'année universitaire en cours.\n\nCette attestation m'est nécessaire pour : ${data['motif'] || '[motif]'}.\n\nJe vous remercie de bien vouloir traiter cette demande dans les meilleurs délais.\n\nVeuillez agréer, Madame, Monsieur, l'expression de mes salutations distinguées.\n\n${data['nom'] || '[Nom]'}\nN° Étudiant: ${data['numEtudiant'] || '[N°]'}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nVous pouvez copier ce modèle et l'envoyer au secrétariat.`;
  } else if (formType === 'reclamation') {
    return `Voici votre formulaire de réclamation de note :\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nFORMULAIRE DE RÉCLAMATION DE NOTE\n\nObjet : Réclamation concernant une note d'examen\n\nMadame, Monsieur,\n\nJe soussigné(e) ${data['nom'] || '[Nom]'}, souhaite formuler une réclamation concernant :\n\n• Matière : ${data['matiere'] || '[Matière]'}\n• Type d'évaluation : ${data['typeEval'] || '[Type]'}\n• Date de l'épreuve : ${data['dateEpreuve'] || '[Date]'}\n• Note obtenue : ${data['noteObtenue'] || '[Note]'}\n• Note attendue : ${data['noteAttendue'] || '[Note]'}\n\nMotif de la réclamation :\n${data['motif'] || '[Motif]'}\n\nCordialement,\n\n${data['nom'] || '[Nom]'}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nVous pouvez copier ce modèle et l'envoyer à votre professeur ou au secrétariat.`;
  } else if (formType === 'stage') {
    return `Voici votre demande de stage formatée :\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nObjet : Demande de convention de stage - ${data['entreprise'] || '[Entreprise]'}\n\nMadame, Monsieur,\n\nJe soussigné(e) ${data['nom'] || '[Nom]'}, étudiant(e) en ${data['filiere'] || '[Filière]'}, vous informe avoir trouvé un stage au sein de l'entreprise ${data['entreprise'] || '[Entreprise]'}.\n\nCe stage se déroulera sur la période suivante : ${data['periode'] || '[Période]'}.\n\nDescription du stage :\n${data['objet'] || '[Description]'}\n\nCordialement,\n\n${data['nom'] || '[Nom]'}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;
  } else if (formType === 'absence') {
    return `Voici votre justification d'absence formatée :\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\nObjet : Justification d'absence - ${data['nom'] || '[Nom]'}\n\nMadame, Monsieur,\n\nJe vous prie de bien vouloir excuser mon absence du ${data['dates'] || '[Dates]'} concernant le(s) cours de ${data['matieres'] || '[Matières]'}.\n\nCette absence est due à la raison suivante : ${data['motif'] || '[Motif]'}.\n\nDétails : ${data['details'] || '[Détails]'}\n\nCordialement,\n\n${data['nom'] || '[Nom]'}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━`;
  }
  return '';
}

/* ─── Mock history ───────────────────────────────────────────────────────── */
const MOCK_HISTORY: Conversation[] = [
  {
    id: '1',
    title: "Résumé du cours d'histoire",
    date: "Aujourd'hui",
    isFavorite: true,
    messages: [
      {
        id: 'm1',
        text: 'Peux-tu me résumer le cours sur la Révolution Française ?',
        sender: 'user',
        timestamp: new Date(new Date().setHours(14, 30)),
      },
      {
        id: 'm2',
        text: "Bien sûr ! La Révolution française (1789-1799) est une période de bouleversements sociaux et politiques majeurs en France. Elle débute avec la prise de la Bastille et mène à la fin de la monarchie absolue, l'adoption de la Déclaration des droits de l'homme et du citoyen, et l'instauration de la République.",
        sender: 'ai',
        timestamp: new Date(new Date().setHours(14, 31)),
        type: 'resume',
        source: "Source : Cours d'Histoire Moderne, Chapitre 3",
        suggestions: ["Résumer un autre chapitre", "Expliquer un concept clé", "Générer des questions de révision"],
      },
    ],
  },
  {
    id: '2',
    title: "Procédure d'inscription",
    date: 'Hier',
    messages: [
      {
        id: 'm3',
        text: "Comment je fais pour m'inscrire au semestre 2 ?",
        sender: 'user',
        timestamp: new Date(new Date().setHours(10, 15)),
      },
      {
        id: 'm4',
        text: 'Pour vous inscrire au semestre 2, vous devez vous rendre sur le portail étudiant, section "Inscriptions pédagogiques", et sélectionner vos modules avant le 15 janvier.',
        sender: 'ai',
        timestamp: new Date(new Date().setHours(10, 16)),
        type: 'question',
        source: 'Source : Règlement intérieur, Art. 24',
        suggestions: ['Quels documents fournir ?', 'Quelles sont les dates limites ?', 'Qui contacter ?'],
      },
    ],
  },
];

@Injectable({
  providedIn: 'root'
})
export class ChatbotService {
  conversations = signal<Conversation[]>(MOCK_HISTORY);
  activeConvId = signal<string | null>(null);
  isTyping = signal<boolean>(false);
  searchQuery = signal<string>('');

  /* ── Computed state ── */
  activeConversation = computed(() =>
    this.conversations().find(c => c.id === this.activeConvId())
  );

  messages = computed(() => this.activeConversation()?.messages || []);

  filteredConversations = computed(() => {
    const q = this.searchQuery().toLowerCase();
    return this.conversations().filter(c => c.title.toLowerCase().includes(q));
  });

  favoriteConversations = computed(() =>
    this.filteredConversations().filter(c => c.isFavorite)
  );

  todayConversations = computed(() =>
    this.filteredConversations().filter(c => c.date === "Aujourd'hui" && !c.isFavorite)
  );

  hierConversations = computed(() =>
    this.filteredConversations().filter(c => c.date === 'Hier' && !c.isFavorite)
  );

  showEmptyState = computed(() =>
    !this.activeConvId() && this.messages().length === 0
  );

  /* ── Actions ── */
  startNewConversation() {
    this.activeConvId.set(null);
  }

  setActiveConv(id: string) {
    this.activeConvId.set(id);
  }

  deleteConversation(id: string) {
    this.conversations.update(list => list.filter(c => c.id !== id));
    if (this.activeConvId() === id) this.activeConvId.set(null);
  }

  toggleFavorite(id: string) {
    this.conversations.update(list =>
      list.map(c => c.id === id ? { ...c, isFavorite: !c.isFavorite } : c)
    );
  }

  renameConversation(id: string, newTitle: string) {
    this.conversations.update(list =>
      list.map(c => c.id === id ? { ...c, title: newTitle } : c)
    );
  }

  detectFormType(text: string): FormType | null {
    const l = text.toLowerCase();
    if (l.includes('attestation') || l.includes('scolarité') || l.includes('scolaire')) return 'attestation';
    if (l.includes('réclam') || l.includes('reclam') || l.includes('note')) return 'reclamation';
    if (l.includes('stage') || l.includes('convention')) return 'stage';
    if (l.includes('absence') || l.includes('justif')) return 'absence';
    return null;
  }

  detectType(text: string): MessageType {
    const l = text.toLowerCase();
    if (l.includes('résume') || l.includes('synthèse') || l.includes('résumé')) return 'resume';
    if (l.includes('comment') || l.includes('pourquoi') || l.includes('quel') || text.includes('?')) return 'question';
    return 'normal';
  }

  sendMessage(text: string) {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      text: text.trim(),
      sender: 'user',
      timestamp: new Date(),
    };

    let currentConvId = this.activeConvId();

    if (!currentConvId) {
      const newConv: Conversation = {
        id: Date.now().toString(),
        title: text.trim().substring(0, 30) + (text.trim().length > 30 ? '...' : ''),
        date: "Aujourd'hui",
        messages: [userMsg],
      };
      this.conversations.update(list => [newConv, ...list]);
      this.activeConvId.set(newConv.id);
      currentConvId = newConv.id;
    } else {
      this.addMessageToConv(currentConvId, userMsg);
    }

    this.isTyping.set(true);

    setTimeout(() => {
      const formType = this.detectFormType(userMsg.text);
      const detectedType: MessageType = formType ? 'form' : this.detectType(userMsg.text);

      let aiText = '';
      let fields: FormField[] | undefined;

      if (detectedType === 'form' && formType) {
        aiText = "J'ai détecté que vous souhaitez effectuer une démarche administrative. Veuillez remplir le formulaire ci-dessous pour que je puisse générer votre document :";
        fields = getFormFields(formType);
      } else if (detectedType === 'resume') {
        aiText = "Voici un résumé basé sur votre demande. Ce document aborde les points clés suivants :\n\n1. Introduction au concept principal\n2. Développement des idées et arguments\n3. Conclusion et perspectives d'application";
      } else if (detectedType === 'question') {
        aiText = 'Pour répondre à votre question, la procédure habituelle consiste à vérifier vos documents sur le portail étudiant, puis à les soumettre via la section dédiée avant la date limite indiquée.';
      } else {
        aiText = 'Je comprends votre demande. Comment puis-je vous aider davantage avec vos études ou vos démarches administratives ?';
      }

      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        text: aiText,
        sender: 'ai',
        timestamp: new Date(),
        type: detectedType,
        source: getSource(detectedType),
        suggestions: detectedType !== 'form' ? getSuggestions(detectedType) : undefined,
        formType: formType || undefined,
        formFields: fields,
        formData: fields ? {} : undefined,
      };

      this.addMessageToConv(currentConvId!, aiMsg);
      this.isTyping.set(false);
    }, 300);
  }

  submitEdit(msgId: string, text: string) {
    const activeId = this.activeConvId();
    if (!activeId || !text.trim()) return;

    this.conversations.update(list =>
      list.map(c => {
        if (c.id !== activeId) return c;
        const msgIndex = c.messages.findIndex(m => m.id === msgId);
        if (msgIndex === -1) return c;

        const updatedMessage = { ...c.messages[msgIndex], text: text.trim() };
        const updatedMessages = [...c.messages.slice(0, msgIndex), updatedMessage];

        return { ...c, messages: updatedMessages };
      })
    );

    this.isTyping.set(true);

    setTimeout(() => {
      const messages = this.messages();
      const lastUserMsg = messages[messages.length - 1];
      
      const formType = this.detectFormType(lastUserMsg.text);
      const detectedType: MessageType = formType ? 'form' : this.detectType(lastUserMsg.text);

      let aiText = '';
      let fields: FormField[] | undefined;

      if (detectedType === 'form' && formType) {
        aiText = "J'ai détecté que vous souhaitez effectuer une démarche administrative. Veuillez remplir le formulaire ci-dessous pour que je puisse générer votre document :";
        fields = getFormFields(formType);
      } else if (detectedType === 'resume') {
        aiText = "Voici un résumé basé sur votre demande. Ce document aborde les points clés suivants :\n\n1. Introduction au concept principal\n2. Développement des idées et arguments\n3. Conclusion et perspectives d'application";
      } else if (detectedType === 'question') {
        aiText = 'Pour répondre à votre question, la procédure habituelle consiste à vérifier vos documents sur le portail étudiant, puis à les soumettre via la section dédiée avant la date limite indiquée.';
      } else {
        aiText = 'Je comprends votre demande. Comment puis-je vous aider davantage avec vos études ou vos démarches administratives ?';
      }

      const aiMsg: Message = {
        id: Date.now().toString(),
        text: aiText,
        sender: 'ai',
        timestamp: new Date(),
        type: detectedType,
        source: getSource(detectedType),
        suggestions: detectedType !== 'form' ? getSuggestions(detectedType) : undefined,
        formType: formType || undefined,
        formFields: fields,
        formData: fields ? {} : undefined,
      };

      this.addMessageToConv(activeId, aiMsg);
      this.isTyping.set(false);
    }, 300);
  }

  regenerateMessage(msgId: string) {
    const activeId = this.activeConvId();
    if (!activeId) return;

    this.conversations.update(list =>
      list.map(c => {
        if (c.id !== activeId) return c;
        const msgIndex = c.messages.findIndex(m => m.id === msgId);
        if (msgIndex === -1) return c;

        // Find the preceding user message
        let userText = '';
        for (let i = msgIndex - 1; i >= 0; i--) {
          if (c.messages[i].sender === 'user') {
            userText = c.messages[i].text;
            break;
          }
        }

        if (!userText) {
          userText = "Aide";
        }

        this.isTyping.set(true);

        // Remove the regenerated AI message
        const updatedMessages = c.messages.filter(m => m.id !== msgId);

        setTimeout(() => {
          const formType = this.detectFormType(userText);
          const detectedType: MessageType = formType ? 'form' : this.detectType(userText);

          let aiText = '';
          let fields: FormField[] | undefined;
          const variant = Math.floor(Math.random() * 2);

          if (detectedType === 'form' && formType) {
            aiText = variant === 0 
              ? "J'ai détecté une démarche administrative. Veuillez remplir ce formulaire pour générer votre document :"
              : "Pour votre demande administrative, merci de renseigner les informations suivantes ci-dessous :";
            fields = getFormFields(formType);
          } else if (detectedType === 'resume') {
            aiText = variant === 0
              ? "Voici une version synthétisée de votre document :\n\n• Point 1 : Analyse des fondements principaux.\n• Point 2 : Présentation des arguments clés.\n• Point 3 : Conclusion et recommandations."
              : "Voici la synthèse actualisée :\n\n1. Aperçu général du document.\n2. Principales conclusions identifiées.\n3. Solutions proposées.";
          } else if (detectedType === 'question') {
            aiText = variant === 0
              ? "D'après les règlements de l'université, vous devez soumettre vos documents directement sur l'espace étudiant."
              : "Pour répondre à cela, la procédure exige le dépôt de vos justificatifs signés via le secrétariat en ligne.";
          } else {
            aiText = variant === 0
              ? "Je reste à votre disposition. Avez-vous d'autres questions sur vos cours ou vos démarches ?"
              : "Je suis là pour vous aider. N'hésitez pas à me poser d'autres questions.";
          }

          const newAiMsg: Message = {
            id: Date.now().toString(),
            text: aiText,
            sender: 'ai',
            timestamp: new Date(),
            type: detectedType,
            source: getSource(detectedType),
            suggestions: detectedType !== 'form' ? getSuggestions(detectedType) : undefined,
            formType: formType || undefined,
            formFields: fields,
            formData: fields ? {} : undefined,
          };

          this.conversations.update(latestList =>
            latestList.map(conv => {
              if (conv.id !== activeId) return conv;
              return { ...conv, messages: [...conv.messages, newAiMsg] };
            })
          );

          this.isTyping.set(false);
        }, 400);

        return { ...c, messages: updatedMessages };
      })
    );
  }

  private addMessageToConv(convId: string, msg: Message) {
    this.conversations.update(list =>
      list.map(c => c.id === convId ? { ...c, messages: [...c.messages, msg] } : c)
    );
  }

  updateFormField(msgId: string, fieldName: string, value: string) {
    this.conversations.update(list =>
      list.map(c =>
        c.id === this.activeConvId()
          ? {
              ...c,
              messages: c.messages.map(m =>
                m.id === msgId
                  ? { ...m, formData: { ...(m.formData || {}), [fieldName]: value } }
                  : m
              ),
            }
          : c
      )
    );
  }

  getFormData(msgId: string): Record<string, string> {
    return (
      this.messages().find(m => m.id === msgId)?.formData || {}
    );
  }

  submitForm(msg: Message) {
    if (!msg.formType) return;

    // Mark submitted
    this.conversations.update(list =>
      list.map(c =>
        c.id === this.activeConvId()
          ? { ...c, messages: c.messages.map(m => m.id === msg.id ? { ...m, formSubmitted: true } : m) }
          : c
      )
    );

    this.isTyping.set(true);
    setTimeout(() => {
      const data = this.getFormData(msg.id);
      const generatedText = generateDocument(msg.formType!, data);

      const aiMsg: Message = {
        id: Date.now().toString(),
        text: generatedText,
        sender: 'ai',
        timestamp: new Date(),
        type: 'normal',
        source: 'Générateur de documents UniHelp',
        suggestions: ['Générer un autre document', 'Question administrative'],
      };

      this.addMessageToConv(this.activeConvId()!, aiMsg);
      this.isTyping.set(false);
    }, 1500);
  }
}
