import { Component, signal, inject, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../../../app/services/auth.service';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-student-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, LucideAngularModule],
  templateUrl: './dashboard.component.html'
})
export class DashboardComponent implements AfterViewInit, OnDestroy {
  private authService = inject(AuthService);
  private router = inject(Router);

  user = this.authService.user;
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
    { id: 1, action: 'A posé une question au Chatbot IA', time: 'Il y a 2 heures', type: 'chat' },
    { id: 2, action: 'A généré un email "Demande de stage"', time: 'Hier à 14:30', type: 'email' },
    { id: 3, action: 'A consulté la FAQ - Inscription', time: 'Hier à 10:15', type: 'doc' },
    { id: 4, action: 'A mis à jour son profil', time: 'Il y a 3 jours', type: 'profile' },
    { id: 5, action: 'A demandé un résumé de cours', time: 'Il y a 4 jours', type: 'chat' }
  ];

  favoriteMessages = [
    { id: 1, text: 'La Révolution française (1789-1799) est une période de bouleversements...', source: 'Chatbot IA', time: 'Il y a 2h' },
    { id: 2, text: 'Pour vous inscrire au semestre 2, rendez-vous sur le portail étudiant...', source: 'Chatbot IA', time: 'Hier' },
    { id: 3, text: 'Les supports de cours sont disponibles sur la plateforme Moodle...', source: 'Chatbot IA', time: 'Il y a 2j' },
    { id: 4, text: 'Votre certificat de scolarité est disponible dans la section Documents...', source: 'Chatbot IA', time: 'Il y a 3j' },
    { id: 5, text: 'Les notes sont publiées sur le portail étudiant après délibération...', source: 'Chatbot IA', time: 'Il y a 5j' }
  ];

  progressionData = [
    { name: 'Questions', value: 124 },
    { name: 'Résumés', value: 45 },
    { name: 'Emails', value: 12 }
  ];

  progressionTab = signal<'bar' | 'pie'>('pie');
  private progChart: Chart | null = null;
  private PROGRESSION_COLORS = ['#1d4b99', '#8db2edff', '#bdd9f4ff'];

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

  getActivityIcon(type: string): string {
    switch (type) {
      case 'chat': return 'message-square';
      case 'email': return 'mail';
      case 'doc': return 'file-text';
      case 'profile': return 'user';
      default: return 'help-circle';
    }
  }

  getActivityColor(type: string): string {
    switch (type) {
      case 'chat': return 'text-[#1d4b99]';
      case 'email': return 'text-purple-500';
      case 'doc': return 'text-emerald-500';
      case 'profile': return 'text-slate-400';
      default: return 'text-slate-400';
    }
  }
}
