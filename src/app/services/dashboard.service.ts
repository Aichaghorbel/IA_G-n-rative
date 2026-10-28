import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class DashboardService {
  private http = inject(HttpClient);

  getStudentDashboard(): Observable<any> {
    return this.http.get<any>(`${environment.apiUrl}/student/dashboard`).pipe(
      catchError(err => {
        console.warn('Could not fetch student dashboard from API, using fallback data', err);
        return of(null);
      })
    );
  }

  getAdminDashboard(): Observable<any> {
    return this.http.get<any>(`${environment.apiUrl}/admin/dashboard`).pipe(
      catchError(err => {
        console.warn('Could not fetch admin dashboard from API, using fallback data', err);
        return of(null);
      })
    );
  }

  getEnseignantDashboard(): Observable<any> {
    return this.http.get<any>(`${environment.apiUrl}/enseignant/dashboard`).pipe(
      catchError(err => {
        console.warn('Could not fetch enseignant dashboard from API, using fallback data', err);
        return of(null);
      })
    );
  }
}

