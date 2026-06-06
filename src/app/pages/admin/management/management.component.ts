import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { animate, style, transition, trigger, state } from '@angular/animations';

interface Admin {
  id: number;
  name: string;
  prenom: string;
  email: string;
  password: string;
  phone: string;
  role: string;
  department: string;
  status: string;
  lastLogin: string;
}

@Component({
  selector: 'app-admin-management',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './management.component.html',
  animations: [
    trigger('modalSlide', [
      transition(':enter', [
        style({ transform: 'scale(0.95) translateY(20px)', opacity: 0 }),
        animate('300ms cubic-bezier(0.34, 1.56, 0.64, 1)', style({ transform: 'scale(1) translateY(0)', opacity: 1 }))
      ]),
      transition(':leave', [
        animate('200ms ease-in', style({ transform: 'scale(0.95) translateY(20px)', opacity: 0 }))
      ])
    ])
  ]
})
export class ManagementComponent {
  admins = signal<Admin[]>([
    { id: 1, name: 'Marie', prenom: 'Dubois', email: 'marie.d@eduportal.com', password: '123', phone: '71 234 567', role: 'Admin', department: 'Scolarité', status: 'Actif', lastLogin: 'Hier à 14:30' },
    { id: 2, name: 'Paul', prenom: 'Leroy', email: 'paul.l@eduportal.com', password: '123', phone: '71 234 568', role: 'Admin', department: 'Examens', status: 'Actif', lastLogin: 'Il y a 3 jours' }
  ]);

  searchQuery = signal('');
  isModalOpen = signal(false);
  isDeleteModalOpen = signal(false);
  viewingAdmin = signal<Admin | null>(null);

  formData = { name: '', prenom: '', email: '', password: '', phone: '', department: 'Scolarité' };
  departments = ['Scolarité', 'Examens', 'Direction', 'Ressources Humaines'];

  filteredAdmins = computed(() => {
    const q = this.searchQuery().toLowerCase();
    return this.admins().filter(a => a.name.toLowerCase().includes(q) || a.email.toLowerCase().includes(q));
  });

  currentPage = signal(1);
  itemsPerPage = 5;

  filteredCount = computed(() => this.filteredAdmins().length);
  totalPages = computed(() => Math.ceil(this.filteredCount() / this.itemsPerPage));
  startIndex = computed(() => (this.currentPage() - 1) * this.itemsPerPage);
  endIndex = computed(() => Math.min(this.startIndex() + this.itemsPerPage, this.filteredCount()));

  paginatedAdmins = computed(() => {
    const start = this.startIndex();
    return this.filteredAdmins().slice(start, start + this.itemsPerPage);
  });

  pageNumbers = computed(() => {
    const total = this.totalPages();
    const current = this.currentPage();
    let start = Math.max(1, current - 2);
    let end = Math.min(total, start + 4);
    if (end - start < 4) {
      start = Math.max(1, end - 4);
    }
    return Array.from({ length: Math.max(0, end - start + 1) }, (_, i) => start + i);
  });

  openAddModal() {
    this.viewingAdmin.set(null);
    this.formData = { name: '', prenom: '', email: '', password: '', phone: '', department: 'Scolarité' };
    this.isModalOpen.set(true);
  }

  openViewModal(admin: Admin) {
    this.viewingAdmin.set(admin);
    this.isModalOpen.set(true);
  }

  openDeleteModal(admin: Admin) {
    this.viewingAdmin.set(admin);
    this.isDeleteModalOpen.set(true);
  }

  handleSave() {
    if (this.formData.name && this.formData.email) {
      const newAdmin: Admin = {
        id: Date.now(),
        name: this.formData.name,
        prenom: this.formData.prenom,
        email: this.formData.email,
        password: this.formData.password,
        phone: this.formData.phone,
        role: 'Admin',
        department: this.formData.department,
        status: 'Actif',
        lastLogin: 'Jamais'
      };
      this.admins.update(list => [...list, newAdmin]);
      this.isModalOpen.set(false);
    }
  }

  handleDelete() {
    if (this.viewingAdmin()) {
      this.admins.update(list => list.filter(a => a.id !== this.viewingAdmin()!.id));
    }
    this.isDeleteModalOpen.set(false);
  }

  prevPage() { if (this.currentPage() > 1) this.currentPage.update(v => v - 1); }
  nextPage() { if (this.currentPage() < this.totalPages()) this.currentPage.update(v => v + 1); }
  goToPage(p: number) { this.currentPage.set(p); }
}
