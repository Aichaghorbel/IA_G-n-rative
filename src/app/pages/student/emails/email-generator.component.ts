import { Component, signal, inject, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../../services/auth.service';
import { animate, style, transition, trigger, query, stagger } from '@angular/animations';

@Component({
  selector: 'app-email-generator',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './email-generator.component.html',
  styleUrls: ['./email-generator.component.css']
})
export class EmailGeneratorComponent {
  private authService = inject(AuthService);

  user = this.authService.user;
  step = signal<number>(1);
  isGenerating = signal<boolean>(false);
  isCopied = signal<boolean>(false);
  generatedEmail = signal<string>('');

  formData = signal({
    type: '',
    recipient: '',
    motif: ''
  });

  emailTypes = [
    { value: '', label: "Sélectionnez un type d'email..." },
    { value: 'attestation', label: "Demande d'attestation de scolarité" },
    { value: 'rattrapage', label: 'Demande de rattrapage' },
    { value: 'stage', label: 'Demande de stage' },
    { value: 'info', label: "Demande d'information" },
    { value: 'reclamation', label: 'Réclamation' },
    { value: 'remerciement', label: 'Remerciement' }
  ];

  recipients = [
    { value: '', label: 'Sélectionnez un destinataire...' },
    { value: 'directeur', label: "Directeur de l'établissement" },
    { value: 'chef_dept', label: 'Chef de département' },
    { value: 'scolarite', label: 'Service scolarité' },
    { value: 'enseignant', label: 'Enseignant' }
  ];

  steps = [
    { id: 1, label: 'Type' },
    { id: 2, label: 'Destinataire' },
    { id: 3, label: 'Infos' },
    { id: 4, label: 'Aperçu' }
  ];

  emailBlocks = computed(() => {
    const email = this.generatedEmail();
    if (!email) return [];

    const studentName = this.user()?.name || 'Jean Dupont';
    const studentField = 'Informatique'; // Simplified for now

    return email.split('\n').map(line => {
      if (line.startsWith('À :') || line.startsWith('À:')) {
        return { type: 'header', content: line };
      }
      if (line.startsWith('Objet :') || line.startsWith('Objet:')) {
        return { type: 'subject', content: line };
      }
      if (line.trim() === '') {
        return { type: 'br' };
      }

      // Handle bold parts
      const parts = [];
      const boldTerms = [studentName, `2ème année ${studentField}`];
      let currentLine = line;

      // Simplistic splitting for demonstration
      // In a real app, use a more robust regex splitter
      parts.push({ text: line, bold: false });

      return { type: 'body', content: line, parts: parts };
    });
  });

  isStepValid(s: number): boolean {
    const data = this.formData();
    if (s === 1) return data.type !== '';
    if (s === 2) return data.recipient !== '';
    if (s === 3) return data.motif.trim() !== '';
    return true;
  }

  handleNext() {
    if (this.isStepValid(this.step())) {
      this.step.update(s => s + 1);
    }
  }

  handleBack() {
    if (this.step() > 1) {
      this.step.update(s => s - 1);
    }
  }

  reset() {
    this.step.set(1);
    this.formData.set({ type: '', recipient: '', motif: '' });
    this.generatedEmail.set('');
  }

  generate() {
    this.isGenerating.set(true);
    setTimeout(() => {
      const data = this.formData();
      const studentName = this.user()?.name || 'Jean Dupont';
      const studentEmail = this.user()?.email || 'jean.dupont@univ.tn';
      const studentField = 'Informatique';
      const studentId = '20240156';
      const year = '2024/2025';

      const recipientTitle = this.getRecipientTitle(data.recipient);
      const recipientFull = this.recipients.find(r => r.value === data.recipient)?.label || 'Destinataire';

      let body = '';
      if (data.type === 'attestation') {
        body = `À : ${recipientFull}\nObjet : Demande d'attestation de scolarité – Année ${year}\n\n${recipientTitle},\n\nJe soussigné(e) ${studentName}, étudiant(e) en 2ème année ${studentField} (N° étudiant : ${studentId}), me permets de solliciter auprès de vos services la délivrance d'une attestation de scolarité pour l'année universitaire en cours${data.motif ? ', nécessaire pour ' + data.motif : ''}.\n\nJe vous remercie de bien vouloir traiter cette demande dans les meilleurs délais.\n\nVeuillez agréer, ${recipientTitle}, l'expression de mes salutations distinguées.\n\n${studentName}\n${studentEmail} · ${studentId}`;
      } else {
        body = `À : ${recipientFull}\nObjet : Demande – Année ${year}\n\n${recipientTitle},\n\nJe soussigné(e) ${studentName}, étudiant(e) en 2ème année ${studentField} (N° étudiant : ${studentId}), me permets de vous écrire concernant ma demande${data.motif ? ': ' + data.motif : ''}.\n\nJe vous remercie par avance pour votre retour.\n\nCordialement,\n\n${studentName}\n${studentEmail} · ${studentId}`;
      }

      this.generatedEmail.set(body);
      this.isGenerating.set(false);
      this.step.set(4);
    }, 1200);
  }

  getRecipientTitle(r: string): string {
    if (r === 'directeur') return 'Monsieur le Directeur';
    if (r === 'chef_dept') return 'Monsieur le Chef de Département';
    if (r === 'scolarite') return 'Madame, Monsieur';
    if (r === 'enseignant') return 'Madame, Monsieur le Professeur';
    return 'Madame, Monsieur';
  }

  copyToClipboard() {
    navigator.clipboard.writeText(this.generatedEmail());
    this.isCopied.set(true);
    setTimeout(() => this.isCopied.set(false), 2000);
  }
}
