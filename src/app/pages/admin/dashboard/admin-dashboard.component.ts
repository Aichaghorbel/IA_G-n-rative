import { Component, signal, AfterViewInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { animate, style, transition, trigger } from '@angular/animations';
import { RouterLink } from '@angular/router';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

interface Stat {
  label: string;
  value: string;
  icon: string;
  color: string;
  bg: string;
  fill?: boolean;
}

interface ChartData {
  name: string;
  inscrits: number;
}

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, RouterLink],
  templateUrl: './admin-dashboard.component.html',
  animations: [
    trigger('fadeInUp', [
      transition(':enter', [
        style({ opacity: 0, transform: 'translateY(10px)' }),
        animate('300ms ease-out', style({ opacity: 1, transform: 'translateY(0)' }))
      ])
    ])
  ]
})
export class AdminDashboardComponent implements AfterViewInit, OnDestroy {
  chartTab = signal<'semaine' | 'mois'>('semaine');
  private chart: Chart | null = null;

  stats: Stat[] = [
    { label: 'Étudiants', value: '1,248', icon: 'users', color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Documents', value: '342', icon: 'file-text', color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Emails', value: '45', icon: 'star', color: 'text-amber-500', bg: 'bg-amber-50', fill: true },
    { label: 'Administrateurs', value: '12', icon: 'shield', color: 'text-purple-600', bg: 'bg-purple-50' }
  ];

  weeklyData: ChartData[] = [
    { name: 'Lun', inscrits: 12 }, { name: 'Mar', inscrits: 18 }, { name: 'Mer', inscrits: 15 },
    { name: 'Jeu', inscrits: 25 }, { name: 'Ven', inscrits: 30 }, { name: 'Sam', inscrits: 10 }, { name: 'Dim', inscrits: 5 }
  ];

  monthlyData: ChartData[] = [
    { name: 'Jan', inscrits: 40 }, { name: 'Fév', inscrits: 30 }, { name: 'Mar', inscrits: 45 },
    { name: 'Avr', inscrits: 50 }, { name: 'Mai', inscrits: 65 }, { name: 'Juin', inscrits: 85 },
    { name: 'Juil', inscrits: 90 }, { name: 'Août', inscrits: 60 }, { name: 'Sep', inscrits: 110 },
    { name: 'Oct', inscrits: 125 }, { name: 'Nov', inscrits: 115 }, { name: 'Déc', inscrits: 135 }
  ];

  recentStudents = [
    { id: 1, name: 'Sophie Martin', field: 'Informatique', status: 'Actif' },
    { id: 2, name: 'Lucas Bernard', field: 'Droit', status: 'Actif' },
    { id: 3, name: 'Emma Petit', field: 'Médecine', status: 'Actif' },
    { id: 4, name: 'Hugo Dubois', field: 'Économie', status: 'Actif' },
    { id: 5, name: 'Léa Roux', field: 'Lettres', status: 'Inactif' }
  ];

  topQuestions = [
    { text: 'Certificat de scolarité', count: 312, icon: 'file', color: 'text-blue-500', bg: 'bg-blue-50' },
    { text: 'Calendrier des examens', count: 287, icon: 'calendar', color: 'text-indigo-500', bg: 'bg-indigo-50' },
    { text: 'Bourse & aides', count: 241, icon: 'coins', color: 'text-amber-500', bg: 'bg-amber-50' },
    { text: "Justification d'absence", count: 198, icon: 'x-circle', color: 'text-red-500', bg: 'bg-red-50' }
  ];

  categories = [
    { name: 'Scolarité', percent: 38, color: 'bg-slate-800' },
    { name: 'Examens', percent: 25, color: 'bg-amber-500' },
    { name: 'Bourses', percent: 20, color: 'bg-blue-500' },
    { name: 'Absences', percent: 10, color: 'bg-emerald-500' }
  ];

  activeData() {
    return this.chartTab() === 'semaine' ? this.weeklyData : this.monthlyData;
  }

  ngAfterViewInit() {
    this.renderChart();
  }

  ngOnDestroy() {
    if (this.chart) {
      this.chart.destroy();
    }
  }

  renderChart() {
    const canvas = document.getElementById('inscriptionsChart') as HTMLCanvasElement;
    if (!canvas) return;

    if (this.chart) {
      this.chart.destroy();
    }

    const data = this.activeData();

    this.chart = new Chart(canvas, {
      type: 'line',
      data: {
        labels: data.map(d => d.name),
        datasets: [{
          label: 'Inscriptions',
          data: data.map(d => d.inscrits),
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
              label: (ctx: any) => ` ${ctx.parsed.y} inscription(s)`
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
              stepSize: 25,
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
}
