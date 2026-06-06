import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { animate, style, transition, trigger, state } from '@angular/animations';

interface Document {
  id: number;
  title: string;
  category: string;
  date: string;
  size: string;
}

@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  templateUrl: './documents.component.html',
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
export class DocumentsComponent {
  documents = signal<Document[]>([
    { id: 1, title: 'Syllabus Mathématiques L1', category: 'Syllabus', date: '12/06/2023', size: '2.4 MB' },
    { id: 2, title: 'Règlement intérieur 2023-2024', category: 'Administration', date: '10/06/2023', size: '1.1 MB' },
    { id: 3, title: 'Planning des examens S1', category: 'Examens', date: '05/06/2023', size: '0.8 MB' },
    { id: 4, title: "Guide de l'étudiant international", category: 'Guide', date: '01/06/2023', size: '5.2 MB' },
    { id: 5, title: 'Formulaire demande de bourse', category: 'Administration', date: '28/05/2023', size: '0.5 MB' },
    { id: 6, title: 'Support de cours - Introduction au Droit', category: 'Cours', date: '25/05/2023', size: '3.7 MB' }
  ]);

  searchQuery = signal('');
  categoryFilter = signal('');
  isFilterOpen = signal(false);
  isModalOpen = signal(false);
  isDeleteModalOpen = signal(false);
  editingDoc = signal<Document | null>(null);
  currentPage = signal(1);
  itemsPerPage = 5;

  formData = { title: '', category: 'Syllabus' };
  categories = ['Syllabus', 'Administration', 'Examens', 'Cours', 'Guide'];

  filteredDocs = computed(() => {
    const q = this.searchQuery().toLowerCase();
    const cat = this.categoryFilter();
    return this.documents().filter(d => {
      const ms = d.title.toLowerCase().includes(q) || d.category.toLowerCase().includes(q);
      const mc = !cat || d.category === cat;
      return ms && mc;
    });
  });

  filteredCount = computed(() => this.filteredDocs().length);
  totalPages = computed(() => Math.ceil(this.filteredCount() / this.itemsPerPage));
  startIndex = computed(() => (this.currentPage() - 1) * this.itemsPerPage);
  endIndex = computed(() => Math.min(this.startIndex() + this.itemsPerPage, this.filteredCount()));

  paginatedDocs = computed(() => {
    const start = this.startIndex();
    return this.filteredDocs().slice(start, start + this.itemsPerPage);
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
    this.categoryFilter.set('');
    this.isFilterOpen.set(false);
    this.currentPage.set(1);
  }

  openAddModal() {
    this.editingDoc.set(null);
    this.formData = { title: '', category: 'Syllabus' };
    this.isModalOpen.set(true);
  }

  openEditModal(doc: Document) {
    this.editingDoc.set(doc);
    this.formData = { title: doc.title, category: doc.category };
    this.isModalOpen.set(true);
  }

  openDeleteModal(doc: Document) {
    this.editingDoc.set(doc);
    this.isDeleteModalOpen.set(true);
  }

  handleSave() {
    if (this.editingDoc()) {
      this.documents.update(docs => docs.map(d => 
        d.id === this.editingDoc()!.id ? { ...d, title: this.formData.title, category: this.formData.category } : d
      ));
    } else {
      const newDoc: Document = {
        id: Date.now(),
        title: this.formData.title || 'Nouveau Document',
        category: this.formData.category,
        date: new Date().toLocaleDateString('fr-FR'),
        size: '1.5 MB'
      };
      this.documents.update(docs => [newDoc, ...docs]);
    }
    this.isModalOpen.set(false);
  }

  handleDelete() {
    if (this.editingDoc()) {
      this.documents.update(docs => docs.filter(d => d.id !== this.editingDoc()!.id));
    }
    this.isDeleteModalOpen.set(false);
  }

  prevPage() { if (this.currentPage() > 1) this.currentPage.update(v => v - 1); }
  nextPage() { if (this.currentPage() < this.totalPages()) this.currentPage.update(v => v + 1); }
  goToPage(p: number) { this.currentPage.set(p); }
}
