import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';
import { LoginComponent } from './pages/login/login.component';
import { ShellComponent } from './pages/layout/shell.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { TicketListComponent } from './pages/tickets/ticket-list.component';
import { TicketDetailComponent } from './pages/tickets/ticket-detail.component';
import { TicketStatusComponent } from './pages/ticket-status/ticket-status.component';
import { ChatComponent } from './pages/chat/chat.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  {
    path: '',
    component: ShellComponent,
    canActivate: [authGuard],
    children: [
      { path: 'dashboard', component: DashboardComponent },
      { path: 'ticket-status', component: TicketStatusComponent },
      { path: 'tickets', component: TicketListComponent },
      { path: 'tickets/:id', component: TicketDetailComponent },
      { path: 'assistant', component: ChatComponent },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
    ]
  },
  { path: '**', redirectTo: 'login' }
];
