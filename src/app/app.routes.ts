import { Routes } from '@angular/router';
import { AuthLayoutComponent } from './layouts/auth-layout/auth-layout.component';
import { StudentLayoutComponent } from './layouts/student-layout/student-layout.component';
import { AdminLayoutComponent } from './layouts/admin-layout/admin-layout.component';
import { EnseignantLayoutComponent } from './layouts/enseignant-layout/enseignant-layout.component';
import { LoginComponent } from './pages/auth/login/login.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'login'
  },
  {
    path: '',
    component: AuthLayoutComponent,
    children: [
      {
        path: 'login',
        component: LoginComponent
      }
    ]
  },
  {
    path: 'register',
    loadComponent: () => import('./pages/auth/register/register.component').then(m => m.RegisterComponent)
  },
  {
    path: 'register-enseignant',
    loadComponent: () => import('./pages/auth/register-enseignant/register-enseignant.component').then(m => m.RegisterEnseignantComponent)
  },
  {
    path: 'student',
    component: StudentLayoutComponent,
    canActivate: [authGuard],
    data: { role: 'student' },
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/student/dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'parcours',
        loadComponent: () => import('./pages/student/parcours/parcours.component').then(m => m.ParcoursComponent)
      },
      {
        path: 'preinscription',
        loadComponent: () => import('./pages/student/preinscription/preinscription.component').then(m => m.PreinscriptionComponent)
      },
      {
        path: 'qcm',
        loadComponent: () => import('./pages/student/qcm/qcm.component').then(m => m.QcmComponent)
      },
      {
        path: 'chatbot',
        loadComponent: () => import('./pages/student/chatbot/chatbot.component').then(m => m.ChatbotComponent)
      },
      {
        path: 'profile',
        loadComponent: () => import('./pages/student/profile/profile.component').then(m => m.ProfileComponent)
      },
      {
        path: 'settings',
        loadComponent: () => import('./pages/student/settings/settings.component').then(m => m.SettingsComponent)
      },
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard'
      }
    ]
  },
  {
    path: 'admin',
    component: AdminLayoutComponent,
    canActivate: [authGuard],
    data: { role: 'admin' },
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/admin/dashboard/admin-dashboard.component').then(m => m.AdminDashboardComponent)
      },
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard'
      }
    ]
  },
  {
    path: 'enseignant',
    component: EnseignantLayoutComponent,
    canActivate: [authGuard],
    data: { role: 'enseignant' },
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/enseignant/dashboard/enseignant-dashboard.component').then(m => m.EnseignantDashboardComponent)
      }, {
        path: 'entretiens',
        loadComponent: () => import('./pages/enseignant/entretiens/entretiens.component').then(m => m.EntretiensComponent)
      },
      {
        path: 'students',
        loadComponent: () => import('./pages/enseignant/students/students-list.component').then(m => m.StudentsListComponent)
      },
      {
        path: 'results',
        loadComponent: () => import('./pages/enseignant/results/results.component').then(m => m.ResultsComponent)
      },
      {
        path: 'profile',
        loadComponent: () => import('./pages/enseignant/profile/profile.component').then(m => m.EnseignantProfileComponent)
      },
      {
        path: 'settings',
        loadComponent: () => import('./pages/enseignant/settings/settings.component').then(m => m.SettingsComponent)
      },

      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard'
      }
    ]
  },
  {
    path: '**',
    redirectTo: 'login'
  }
];
