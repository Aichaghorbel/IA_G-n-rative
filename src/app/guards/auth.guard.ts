import { inject } from '@angular/core';
import { Router, CanActivateFn, ActivatedRouteSnapshot } from '@angular/router';
import { AuthService, Role } from '../services/auth.service';

export const authGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const user = authService.user();
  
  // Wait for loading to finish if necessary (though in this simple mock it's sync on init)
  if (!user) {
    return router.parseUrl('/login');
  }

  const allowedRole = route.data['role'] as Role | undefined;
  
  if (allowedRole && user.role !== allowedRole) {
    const redirectPath = user.role === 'admin' 
      ? '/admin/dashboard' 
      : (user.role === 'enseignant' ? '/enseignant/dashboard' : '/student/dashboard');
    return router.parseUrl(redirectPath);
  }

  return true;
};
