import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { animate, style, transition, trigger, state } from '@angular/animations';

interface Student {
  id: number;
  name: string;
  email: string;
  phone: string;
  birthDate: string;
  cin: string;
  passport: string;
  address: string;
  country: string;
  uni: string;
  field: string;
  level: string;
  courseTime: string;
  date: string;
  academicYear: string;
  lastDiploma: string;
  diplomaYear: string;
  knownBy: string;
  status: 'Actif' | 'Inactif' | 'En attente';
  studentId: string;
}

@Component({
  selector: 'app-students-list',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './students-list.component.html',
  animations: [
    trigger('fadeIn', [
      transition(':enter', [style({ opacity: 0 }), animate('200ms ease-out', style({ opacity: 1 }))]),
      transition(':leave', [animate('200ms ease-in', style({ opacity: 0 }))])
    ]),
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
export class StudentsListComponent {
  searchQuery = signal('');
  uniFilter = signal('');
  fieldFilter = signal('');
  statusFilter = signal('');
  isFilterOpen = signal(false);
  selectedStudent = signal<Student | null>(null);
  currentPage = signal(1);
  itemsPerPage = 5;

  mockStudents: Student[] = [
    { id: 1, name: 'Sophie Martin', email: 'sophie.m@example.com', phone: '+216 55 123 456', birthDate: '15/04/1999', cin: '12345678', passport: '-', address: '123 Rue de la République, Tunis', country: 'Tunisie', uni: 'ISB', field: 'Informatique', level: 'L3', courseTime: 'Cours de jour', date: '12/06/2024', academicYear: '2024 / 2025', lastDiploma: 'Informatique', diplomaYear: 'Informatique', knownBy: 'Réseaux sociaux', status: 'Actif', studentId: '20240156' },
    { id: 2, name: 'Lucas Bernard', email: 'lucas.b@example.com', phone: '+216 22 987 654', birthDate: '22/08/2000', cin: '87654321', passport: 'P1234567', address: '45 Avenue Habib Bourguiba, Sfax', country: 'Tunisie', uni: 'IIT', field: 'Génie Logiciel', level: 'M1', courseTime: 'Cours de soir', date: '11/06/2024', academicYear: '2024 / 2025', lastDiploma: 'Licence GL', diplomaYear: '2024', knownBy: 'Bouche à oreille', status: 'Inactif', studentId: '20240157' },
    { id: 3, name: 'Emma Petit', email: 'emma.p@example.com', phone: '+216 99 111 222', birthDate: '05/11/2001', cin: '11223344', passport: '-', address: '12 Rue des Jasmins, Sousse', country: 'Tunisie', uni: 'ISB', field: 'Biologie', level: 'L1', courseTime: 'Cours de jour', date: '10/06/2023', academicYear: '2023 / 2024', lastDiploma: 'Baccalauréat', diplomaYear: '2023', knownBy: 'Publicité en ligne', status: 'Actif', studentId: '20230158' },
    { id: 4, name: 'Hugo Dubois', email: 'hugo.d@example.com', phone: '+216 50 333 444', birthDate: '18/02/1998', cin: '99887766', passport: '-', address: '8 Avenue de Paris, Tunis', country: 'Tunisie', uni: 'IIT', field: 'Génie Civil', level: 'L2', courseTime: 'Cours de jour', date: '09/06/2025', academicYear: '2024 / 2025', lastDiploma: 'Licence GC', diplomaYear: '2024', knownBy: 'Réseaux sociaux', status: 'Actif', studentId: '20250159' },
    { id: 5, name: 'Léa Roux', email: 'lea.r@example.com', phone: '+216 21 555 666', birthDate: '30/09/1999', cin: '55667788', passport: '-', address: '22 Rue de la Liberté, Bizerte', country: 'Tunisie', uni: 'ISB', field: 'Gestion', level: 'M2', courseTime: 'Cours de soir', date: '08/06/2023', academicYear: '2023 / 2024', lastDiploma: 'Master 1', diplomaYear: '2022', knownBy: 'Site web', status: 'Actif', studentId: '20230160' },
    { id: 6, name: 'Thomas Moreau', email: 'thomas.m@example.com', phone: '+216 98 777 888', birthDate: '12/12/2002', cin: '33445566', passport: '-', address: '7 Rue des Orangers, Nabeul', country: 'Tunisie', uni: 'IIT', field: 'Informatique', level: 'L1', courseTime: 'Cours de jour', date: '05/06/2026', academicYear: '2026 / 2027', lastDiploma: 'Baccalauréat', diplomaYear: '2026', knownBy: 'Ami', status: 'Inactif', studentId: '20260161' },
    { id: 7, name: 'Julie Blanc', email: 'julie.b@example.com', phone: '+216 52 999 000', birthDate: '08/07/2000', cin: '12312312', passport: '-', address: '15 Avenue de Carthage, Tunis', country: 'Tunisie', uni: 'ISB', field: 'Marketing', level: 'L3', courseTime: 'Cours de jour', date: '01/06/2024', academicYear: '2024 / 2025', lastDiploma: 'Marketing L2', diplomaYear: '2023', knownBy: 'Réseaux sociaux', status: 'Actif', studentId: '20240162' },
    { id: 8, name: 'Antoine Leroy', email: 'antoine.l@example.com', phone: '+216 20 111 333', birthDate: '25/03/1997', cin: '98765432', passport: 'P9876543', address: '9 Rue d\'Alger, Sfax', country: 'Tunisie', uni: 'IIT', field: 'Mécanique', level: 'M1', courseTime: 'Cours de jour', date: '28/05/2025', academicYear: '2024 / 2025', lastDiploma: 'Licence Mécanique', diplomaYear: '2024', knownBy: 'Forum', status: 'Actif', studentId: '20250163' }
  ];

  fields = ['Informatique', 'Génie Logiciel', 'Génie Civil', 'Biologie', 'Gestion', 'Marketing', 'Mécanique'];

  filteredStudents = computed(() => {
    const q = this.searchQuery().toLowerCase();
    const uni = this.uniFilter();
    const field = this.fieldFilter();
    const status = this.statusFilter();

    return this.mockStudents.filter(s => {
      const matchesSearch = s.name.toLowerCase().includes(q) || s.email.toLowerCase().includes(q) || s.studentId.toLowerCase().includes(q);
      const matchesUni = !uni || s.uni === uni;
      const matchesField = !field || s.field === field;
      const matchesStatus = !status || s.status.toLowerCase() === status.toLowerCase();
      return matchesSearch && matchesUni && matchesField && matchesStatus;
    });
  });

  filteredCount = computed(() => this.filteredStudents().length);
  totalPages = computed(() => Math.ceil(this.filteredCount() / this.itemsPerPage));
  startIndex = computed(() => (this.currentPage() - 1) * this.itemsPerPage);
  endIndex = computed(() => Math.min(this.startIndex() + this.itemsPerPage, this.filteredCount()));
  
  paginatedStudents = computed(() => {
    const start = this.startIndex();
    return this.filteredStudents().slice(start, start + this.itemsPerPage);
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

  toggleFilter() { this.isFilterOpen.update(v => !v); }
  
  clearFilters() {
    this.uniFilter.set('');
    this.fieldFilter.set('');
    this.statusFilter.set('');
    this.isFilterOpen.set(false);
    this.currentPage.set(1);
  }

  prevPage() { if (this.currentPage() > 1) this.currentPage.update(v => v - 1); }
  nextPage() { if (this.currentPage() < this.totalPages()) this.currentPage.update(v => v + 1); }
  goToPage(p: number) { this.currentPage.set(p); }
  
  viewProfile(student: Student) {
    this.selectedStudent.set(student);
  }
}
