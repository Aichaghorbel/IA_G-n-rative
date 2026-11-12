import { Component, signal, inject, computed, ElementRef, ViewChild, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, NavigationEnd } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { filter } from 'rxjs/operators';
import { FormsModule } from '@angular/forms';
import { ChatbotService, Message, MessageType, FormType } from '../../services/chatbot.service';

// Web Speech API type declarations
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

@Component({
  selector: 'app-chatbot-fab',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, FormsModule],
  templateUrl: './chatbot-fab.component.html',
  styleUrls: ['./chatbot-fab.component.css']
})
export class ChatbotFabComponent implements OnDestroy {
  private router = inject(Router);
  private chatbotService = inject(ChatbotService);

  isOnChatbotPage = signal<boolean>(false);
  isHovered = signal<boolean>(false);
  isOpen = signal<boolean>(false);
  inputText: string = '';
  toast = signal<string | null>(null);

  /* ── Voice Recording State ── */
  isRecording = signal<boolean>(false);
  recordingDuration = signal<number>(0);
  voiceTranscript = signal<string>('');
  private recognition: any = null;
  private recordingTimer: any = null;
  private _recordingTranscript = '';   // plain string (same as chatbot page)

  /* ── Edit Message State ── */
  editingMessageId = signal<string | null>(null);
  editingText = '';

  /* ── Delegated signals/computed ── */
  isTyping = this.chatbotService.isTyping;

  messages = computed(() => {
    const list = this.chatbotService.messages();
    if (list.length === 0) {
      // simulated welcome message when discussion is brand new
      return [{
        id: 'welcome-msg',
        text: 'Bonjour ! Je suis votre assistant SmartCampus. Comment puis-je vous aider ?',
        sender: 'ai' as const,
        timestamp: new Date()
      } as Message];
    }
    return list;
  });

  constructor() {
    // Check initial route
    this.isOnChatbotPage.set(this.router.url.includes('/student/chatbot'));

    // Listen for route changes
    this.router.events.pipe(
      filter((event): event is NavigationEnd => event instanceof NavigationEnd)
    ).subscribe((event) => {
      this.isOnChatbotPage.set(event.urlAfterRedirects.includes('/student/chatbot'));
    });
  }

  goToChatbot() {
    this.isOpen.set(false);
    this.router.navigate(['/student/chatbot']);
  }

  toggleChat() {
    this.isOpen.update(v => !v);
    if (this.isOpen()) {
      this.isHovered.set(false);
      this.scrollToBottom();
    }
  }

  onMouseEnter() {
    this.isHovered.set(true);
  }

  onMouseLeave() {
    this.isHovered.set(false);
  }

  sendMessage(text?: string) {
    const messageText = text || this.inputText.trim();
    if (!messageText) return;

    this.chatbotService.sendMessage(messageText);

    if (!text) {
      this.inputText = '';
    }

    this.scrollToBottom();
  }

  copyMessage(text: string) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        this.showToast('Copié !');
      }).catch(err => {
        this.fallbackCopyText(text);
      });
    } else {
      this.fallbackCopyText(text);
    }
  }

  fallbackCopyText(text: string) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand('copy');
      this.showToast('Copié !');
    } catch (err) {
      console.error('Fallback copy failed', err);
      this.showToast('Erreur lors de la copie');
    }
    document.body.removeChild(textArea);
  }

  readAloud() {
    this.showToast('Lecture audio...');
  }

  refreshMessage(msgId: string) {
    this.chatbotService.regenerateMessage(msgId);
    this.showToast("Régénération du message...");
  }

  /* ── Form actions ── */
  updateFormField(msgId: string, fieldName: string, value: string) {
    this.chatbotService.updateFormField(msgId, fieldName, value);
  }

  submitForm(msg: Message) {
    this.chatbotService.submitForm(msg);
    this.scrollToBottom();
  }

  getFormTitle(formType: FormType | undefined): string {
    if (formType === 'attestation') return "Demande d'attestation";
    if (formType === 'reclamation') return 'Réclamation de note';
    if (formType === 'stage')       return 'Demande de stage';
    if (formType === 'absence')     return "Justification d'absence";
    return 'Formulaire';
  }

  /* ── Edit Message actions ── */
  editMessage(msg: Message) {
    this.editingMessageId.set(msg.id);
    this.editingText = msg.text;
  }

  cancelEdit() {
    this.editingMessageId.set(null);
    this.editingText = '';
  }

  submitEdit(msgId: string) {
    if (!this.editingText.trim()) return;
    this.chatbotService.submitEdit(msgId, this.editingText);
    this.cancelEdit();
    this.scrollToBottom();
  }

  showToast(msg: string) {
    this.toast.set(msg);
    setTimeout(() => this.toast.set(null), 2000);
  }

  /* ── Voice Recording ── */
  toggleVoiceRecording() {
    if (this.isRecording()) {
      this.stopRecording();
    } else {
      this.startRecording();
    }
  }

  startRecording() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      this.showToast('Enregistrement vocal non supporté par ce navigateur');
      return;
    }

    this.recognition = new SpeechRecognition();
    this.recognition.lang = 'fr-FR';
    this.recognition.continuous = true;
    this.recognition.interimResults = true;

    this._recordingTranscript = '';
    this.voiceTranscript.set('');
    this.isRecording.set(true);
    this.recordingDuration.set(0);

    // Timer for duration display
    this.recordingTimer = setInterval(() => {
      this.recordingDuration.update(d => d + 1);
    }, 1000);

    // ✅ Accumulate ALL results (interim + final) — same as chatbot page
    this.recognition.onresult = (event: any) => {
      let text = '';
      for (let i = 0; i < event.results.length; i++) {
        text += event.results[i][0].transcript + ' ';
      }
      this._recordingTranscript = text.trim();
      this.voiceTranscript.set(this._recordingTranscript);
    };

    this.recognition.onerror = () => {};

    this.recognition.onend = () => {
      if (this.isRecording()) {
        // Auto-restart if still recording (continuous mode)
        try { this.recognition?.start(); } catch {}
      }
    };

    try {
      this.recognition.start();
      this.showToast('Enregistrement audio en cours...');
    } catch (err) {
      this.showToast('Erreur microphone');
      this.isRecording.set(false);
    }
  }

  stopRecording() {
    const duration = this.recordingDuration();
    const transcript = this._recordingTranscript.trim();

    this.isRecording.set(false);
    if (this.recordingTimer) {
      clearInterval(this.recordingTimer);
      this.recordingTimer = null;
    }
    if (this.recognition) {
      this.recognition.onend = null;
      try { this.recognition.stop(); } catch {}
      this.recognition = null;
    }

    // ✅ Always send — use default text if transcript empty (same as chatbot page)
    const durationStr = this.formatRecordingTime(duration);
    const voiceMessage = transcript
      ? `🎤 Message vocal (${durationStr}) : "${transcript}"`
      : `🎤 Message vocal (${durationStr}) : Demande d'information sur les filières et l'orientation SmartCampus.`;

    this.sendMessage(voiceMessage);
    this._recordingTranscript = '';
    this.voiceTranscript.set('');
    this.recordingDuration.set(0);
    this.showToast('Message vocal envoyé !');
  }

  cancelVoice() {
    this.isRecording.set(false);
    if (this.recordingTimer) {
      clearInterval(this.recordingTimer);
      this.recordingTimer = null;
    }
    if (this.recognition) {
      this.recognition.onend = null;
      try { this.recognition.stop(); } catch {}
      this.recognition = null;
    }
    this._recordingTranscript = '';
    this.voiceTranscript.set('');
    this.recordingDuration.set(0);
    this.showToast('Enregistrement annulé');
  }

  formatRecordingTime(seconds: number): string {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${String(s).padStart(2, '0')}`;
  }

  ngOnDestroy() {
    if (this.recognition) {
      this.recognition.onend = null;
      this.recognition.stop();
    }
    if (this.recordingTimer) {
      clearInterval(this.recordingTimer);
    }
  }

  getTypeBadgeClass(type: MessageType | undefined): string {
    if (type === 'resume') return 'badge-resume';
    if (type === 'question') return 'badge-question';
    if (type === 'form') return 'badge-form';
    return 'badge-normal';
  }

  getTypeBadgeLabel(type: MessageType | undefined): string {
    if (type === 'resume') return 'RÉSUMÉ DÉTECTÉ';
    if (type === 'question') return 'QUESTION DÉTECTÉE';
    if (type === 'form') return 'FORMULAIRE DÉTECTÉ';
    return '';
  }

  formatTime(date: Date | any): string {
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  private scrollToBottom() {
    // Single scroll after the next tick to allow the DOM to render new messages.
    setTimeout(() => {
      const chatContainer = document.querySelector('.chat-messages');
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    }, 0);
  }
}
