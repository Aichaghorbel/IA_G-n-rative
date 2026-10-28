import { Component, signal, AfterViewInit, OnDestroy, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { animate, style, transition, trigger } from '@angular/animations';
import { RouterLink } from '@angular/router';
import { Chart, registerables } from 'chart.js';
import { DashboardService } from '../../../services/dashboard.service';

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

})
export class AdminDashboardComponent {
}
