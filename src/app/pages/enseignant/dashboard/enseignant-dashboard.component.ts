import { Component, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { AuthService } from '../../../services/auth.service';
import { DashboardService } from '../../../services/dashboard.service';

interface Course {
  id: string;
  code: string;
  name: string;
  studentsCount: number;
  schedule: string;
  room: string;
}

@Component({
  selector: 'app-enseignant-dashboard',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  templateUrl: './enseignant-dashboard.component.html'
})
export class EnseignantDashboardComponent implements OnInit {
  user = this.authService.user;

  stats = [
    { label: 'Mes Cours', value: '4', icon: 'book-open', color: 'text-blue-600', bg: 'bg-blue-50' },
    { label: 'Total Étudiants', value: '185', icon: 'users', color: 'text-emerald-600', bg: 'bg-emerald-50' },
    { label: 'Devoirs à corriger', value: '12', icon: 'file-check', color: 'text-amber-600', bg: 'bg-amber-50' },
    { label: 'Heures / semaine', value: '18h', icon: 'clock', color: 'text-purple-600', bg: 'bg-purple-50' }
  ];

  courses: Course[] = [
    { id: '1', code: 'INFO101', name: 'Algorithmique & Structures de données', studentsCount: 65, schedule: 'Lun 08:30 - 10:30', room: 'Amphi A' },
    { id: '2', code: 'INFO203', name: 'Développement Web Moderne (Angular)', studentsCount: 45, schedule: 'Mar 10:45 - 12:45', room: 'Labo 3' },
    { id: '3', code: 'INFO305', name: 'Bases de Données Relationnelles & SQL', studentsCount: 40, schedule: 'Jeu 14:00 - 16:00', room: 'Salle 204' },
    { id: '4', code: 'INFO402', name: 'Génie Logiciel & Architecture', studentsCount: 35, schedule: 'Ven 09:00 - 12:00', room: 'Amphi B' }
  ];

  constructor(
    private authService: AuthService,
    private dashboardService: DashboardService
  ) {}

  ngOnInit() {
    this.dashboardService.getEnseignantDashboard().subscribe(data => {
      if (data) {
        if (data.courses && data.courses.length > 0) {
          this.courses = data.courses;
        }
        if (data.stats && data.stats.length > 0) {
          this.stats = this.stats.map(s => {
            const apiStat = data.stats.find((item: any) => item.label === s.label);
            return apiStat ? { ...s, value: apiStat.value } : s;
          });
        }
      }
    });
  }
}
