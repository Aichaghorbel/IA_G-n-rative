import { ApplicationConfig, provideZoneChangeDetection, importProvidersFrom } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideAnimations } from '@angular/platform-browser/animations';
import { 
  LucideAngularModule, 
  Mail, Lock, Loader2, GraduationCap, LayoutDashboard, MessageSquare, 
  User, MailCheck, HelpCircle, Settings, FileText, Users, Shield, 
  LogOut, ChevronRight, Search, Bell, Menu, X, Plus, Filter, 
  Download, Trash2, Edit, Save, Check, AlertCircle, CheckCircle, XCircle,
  Edit2, Trash, ChevronDown, UploadCloud, Eye, Building, Clock, 
  Sun, Moon, Globe, Info, Palette, Camera, ChevronLeft, Send, Sparkles, Copy, RefreshCw, Paperclip,
  Contact, MapPin, Calendar, BookOpen, Phone, Layers, Megaphone, Star, Radio,
  MoreVertical, MoreHorizontal, Volume2, File, Coins, EyeOff, Folder
} from 'lucide-angular';

import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }), 
    provideRouter(routes),
    provideAnimations(),
    importProvidersFrom(LucideAngularModule.pick({ 
      Mail, Lock, Loader2, GraduationCap, LayoutDashboard, MessageSquare, 
      User, MailCheck, HelpCircle, Settings, FileText, Users, Shield, 
      LogOut, ChevronRight, Search, Bell, Menu, X, Plus, Filter, 
      Download, Trash2, Edit, Save, Check, AlertCircle, CheckCircle, XCircle,
      Edit2, Trash, ChevronDown, UploadCloud, Eye, Building, Clock, 
      Sun, Moon, Globe, Info, Palette, Camera, ChevronLeft, Send, Sparkles, Copy, RefreshCw, Paperclip,
      Contact, MapPin, Calendar, BookOpen, Phone, Layers, Megaphone, Star, Radio,
      MoreVertical, MoreHorizontal, Volume2, File, Coins, EyeOff, Folder
    }))
  ]
};
