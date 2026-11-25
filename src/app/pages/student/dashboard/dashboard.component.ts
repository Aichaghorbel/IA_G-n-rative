import { Component, signal, inject, AfterViewInit, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../../../app/services/auth.service';
import { DashboardService } from '../../../../app/services/dashboard.service';
import { OrientationService, Entretien, CandidatOrientation, NotificationCandidat } from '../../../../app/services/orientation.service';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-student-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, LucideAngularModule],
  templateUrl: './dashboard.component.html'
})
export class DashboardComponent implements OnInit, AfterViewInit, OnDestroy {
  private authService = inject(AuthService);
  private dashboardService = inject(DashboardService);
  private orientationService = inject(OrientationService);
  private router = inject(Router);

  user = this.authService.user;
  candidats = this.orientationService.candidats;
  entretiens = this.orientationService.entretiens;
  notifications = this.orientationService.notifications;
  dernierQCM = this.orientationService.dernierResultatQCM;

  // Récupère les données du candidat connecté
  monCandidat = (): CandidatOrientation | null => {
    const u = this.user();
    if (!u) return null;
    return this.candidats().find(c => c.email.toLowerCase() === u.email.toLowerCase()) || this.candidats()[0] || null;
  };

  // Récupère le prochain entretien du candidat
  monRendezVous = (): Entretien | null => {
    const cand = this.monCandidat();
    if (!cand) return this.entretiens()[0] || null;
    return this.entretiens().find(e => e.candidatEmail.toLowerCase() === cand.email.toLowerCase()) || this.entretiens()[0] || null;
  };

  handleNotifClick(notif: NotificationCandidat) {
    const titreLower = notif.titre.toLowerCase();
    const msgLower = notif.message.toLowerCase();

    if (notif.type === 'rdv' || titreLower.includes('entretien') || msgLower.includes('entretien') || msgLower.includes('rendez-vous')) {
      this.orientationService.ouvrirModalEntretien();
    } else if (notif.type === 'qcm' || titreLower.includes('qcm')) {
      this.router.navigate(['/student/qcm']);
    }
  }
  chartTab = signal<'semaine' | 'mois'>('semaine');
  private chart: Chart | null = null;
  
  weeklyData = [
    { day: 'Lun', messages: 18, activite: 45 },
    { day: 'Mar', messages: 25, activite: 62 },
    { day: 'Mer', messages: 12, activite: 35 },
    { day: 'Jeu', messages: 30, activite: 78 },
    { day: 'Ven', messages: 22, activite: 55 },
    { day: 'Sam', messages: 8, activite: 20 },
    { day: 'Dim', messages: 15, activite: 40 }
  ];

  monthlyData = [
    { day: 'Jan', messages: 120, activite: 350 },
    { day: 'Fév', messages: 150, activite: 420 },
    { day: 'Mar', messages: 180, activite: 510 },
    { day: 'Avr', messages: 140, activite: 390 },
    { day: 'Mai', messages: 210, activite: 580 },
    { day: 'Juin', messages: 250, activite: 650 },
    { day: 'Juil', messages: 280, activite: 720 },
    { day: 'Août', messages: 100, activite: 290 },
    { day: 'Sep', messages: 320, activite: 810 },
    { day: 'Oct', messages: 350, activite: 880 },
    { day: 'Nov', messages: 310, activite: 840 },
    { day: 'Déc', messages: 400, activite: 950 }
  ];

  activityData = this.weeklyData;

  recentActivity = [
    { id: 1, action: 'A posé une question au Chatbot IA SmartCampus', time: 'Il y a 2 heures', type: 'chat' },
    { id: 2, action: 'A complété le QCM adaptatif d’orientation', time: 'Hier à 14:30', type: 'qcm' },
    { id: 3, action: 'A consulté le catalogue des formations IIT & ISB', time: 'Hier à 10:15', type: 'doc' },
    { id: 4, action: 'A mis à jour son dossier de préinscription', time: 'Il y a 3 jours', type: 'profile' },
    { id: 5, action: 'Entretien pédagogique planifié', time: 'Il y a 4 jours', type: 'rdv' }
  ];

  favoriteMessages = [
    { id: 1, text: 'Le Cycle Préparatoire Intégré de l’IIT (2 ans) donne accès direct au Cycle Ingénieur sans concours externe.', source: 'SmartCampus AI', time: 'Il y a 2h' },
    { id: 2, text: 'La Licence Business Intelligence de l’ISB combine gestion, data analytics et parcours bilingue.', source: 'SmartCampus AI', time: 'Hier' },
    { id: 3, text: 'Votre entretien d’orientation permet de valider votre choix de filière avec un enseignant conseiller.', source: 'SmartCampus AI', time: 'Il y a 2j' },
    { id: 4, text: 'Les dossiers de préinscription IIT & ISB sont suivis en temps réel depuis votre tableau de bord.', source: 'SmartCampus AI', time: 'Il y a 3j' }
  ];

  progressionData = [
    { name: 'Questions IA', value: 18 },
    { name: 'Parcours consultés', value: 6 },
    { name: 'QCM & Tests', value: 4 }
  ];

  progressionTab = signal<'bar' | 'pie'>('pie');
  private progChart: Chart | null = null;
  private PROGRESSION_COLORS = ['#1d4b99', '#8db2edff', '#bdd9f4ff'];

  ngOnInit() {
    this.dashboardService.getStudentDashboard().subscribe(data => {
      if (data) {
        if (data.weeklyData) {
          this.weeklyData = data.weeklyData.map((w: any) => ({ day: w.name, messages: w.messages, activite: w.activite }));
        }
        if (data.monthlyData) {
          this.monthlyData = data.monthlyData.map((m: any) => ({ day: m.name, messages: m.messages, activite: m.activite }));
        }
        if (data.progressionData) {
          this.progressionData = data.progressionData;
        }
        if (data.recentActivity && data.recentActivity.length > 0) {
          this.recentActivity = data.recentActivity;
        }
        if (data.favoriteMessages && data.favoriteMessages.length > 0) {
          this.favoriteMessages = data.favoriteMessages;
        }
        this.renderChart();
        this.renderProgressionChart();
      }
    });
  }

  ngAfterViewInit() {
    this.renderChart();
    this.renderProgressionChart();
  }

  ngOnDestroy() {
    if (this.chart) {
      this.chart.destroy();
    }
    if (this.progChart) {
      this.progChart.destroy();
    }
  }

  activeData() {
    return this.chartTab() === 'semaine' ? this.weeklyData : this.monthlyData;
  }

  renderChart() {
    const canvas = document.getElementById('activityChart') as HTMLCanvasElement;
    if (!canvas) return;

    if (this.chart) {
      this.chart.destroy();
    }

    const data = this.activeData();

    this.chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: data.map(d => d.day),
        datasets: [{
          label: 'Activité',
          data: data.map(d => d.activite),
          borderColor: '#1d4b99',
          backgroundColor: 'rgba(29, 75, 153, 0.1)',
          borderWidth: 3,
          fill: true,
          tension: 0.4,
          pointBackgroundColor: '#1d4b99',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 5,
          pointHoverRadius: 7
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#ffffff',
            titleColor: '#64748b',
            bodyColor: '#1e293b',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: 12,
            cornerRadius: 12,
            callbacks: {
              label: (ctx: any) => ` ${ctx.parsed.y} action(s)`
            }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#94a3b8', font: { size: 12 } }
          },
          y: {
            beginAtZero: true,
            grid: { color: '#f1f5f9' },
            ticks: {
              color: '#94a3b8',
              font: { size: 12 },
              maxTicksLimit: 6,
              callback: (v: any) => Number.isInteger(v) ? v : ''
            }
          }
        }
      }
    });
  }

  setChartTab(tab: 'semaine' | 'mois') {
    this.chartTab.set(tab);
    setTimeout(() => this.renderChart(), 0);
  }

  setProgressionTab(tab: 'bar' | 'pie') {
    this.progressionTab.set(tab);
    setTimeout(() => this.renderProgressionChart(), 0);
  }

  renderProgressionChart() {
    const canvas = document.getElementById('progressionChart') as HTMLCanvasElement;
    if (!canvas) return;

    if (this.progChart) {
      this.progChart.destroy();
    }

    const type = this.progressionTab() === 'bar' ? 'bar' : 'pie';
    
    this.progChart = new Chart(canvas, {
      type: type,
      data: {
        labels: this.progressionData.map(d => d.name),
        datasets: [{
          data: this.progressionData.map(d => d.value),
          backgroundColor: this.PROGRESSION_COLORS,
          borderRadius: type === 'bar' ? 8 : 0,
          borderWidth: type === 'pie' ? 2 : 0,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { 
            display: type === 'pie',
            position: 'bottom',
            labels: {
              usePointStyle: true,
              padding: 20,
              font: { size: 12 }
            }
          },
          tooltip: {
            backgroundColor: '#ffffff',
            titleColor: '#64748b',
            bodyColor: '#1e293b',
            borderColor: '#e2e8f0',
            borderWidth: 1,
            padding: 12,
            cornerRadius: 12
          }
        },
        scales: type === 'bar' ? {
          x: {
            grid: { display: false },
            ticks: { font: { size: 12 } }
          },
          y: {
            beginAtZero: true,
            grid: { color: '#f1f5f9' },
            ticks: {
              display: true,
              color: '#94a3b8',
              font: { size: 12 },
              stepSize: 35
            }
          }
        } : {
          x: { display: false },
          y: { display: false }
        }
      }
    });
  }

  firstName() {
    const name = this.user()?.name;
    return name ? name.split(' ')[0] : 'Étudiant';
  }

  navigateToChat() {
    this.router.navigate(['/student/chatbot']);
  }

  ouvrirMonRendezVous() {
    const rdv = this.monRendezVous();
    if (rdv) {
      this.orientationService.ouvrirModalEntretien(rdv);
    }
  }

  getActivityIcon(type: string): string {
    switch (type) {
      case 'chat': return 'message-square';
      case 'qcm': return 'sparkles';
      case 'doc': return 'book-open';
      case 'profile': return 'user';
      case 'rdv': return 'calendar';
      default: return 'help-circle';
    }
  }

  getActivityColor(type: string): string {
    switch (type) {
      case 'chat': return 'text-[#1d4b99]';
      case 'qcm': return 'text-amber-500';
      case 'doc': return 'text-emerald-500';
      case 'profile': return 'text-slate-400';
      case 'rdv': return 'text-purple-500';
      default: return 'text-slate-400';
    }
  }
}
