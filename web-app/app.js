/**
 * BADER Web Application v2.0
 * Full Featured Alpine.js SPA
 */

const API_URL = window.location.hostname === 'localhost' 
    ? 'http://157.90.154.48:8080/api'
    : '/api';

function app() {
    return {
        // State
        loading: true,
        user: null,
        token: null,
        customerId: null,
        sidebarOpen: false,
        currentPage: 'dashboard',
        
        // Login
        loginForm: { customer_id: '', username: '', password: '' },
        loginLoading: false,
        loginError: '',
        
        // Menu
        menuItems: [
            { id: 'dashboard', label: 'Dashboard', icon: 'fas fa-home' },
            { id: 'members', label: 'Üyeler', icon: 'fas fa-users' },
            { id: 'inactive', label: 'Ayrılan Üyeler', icon: 'fas fa-user-minus' },
            { id: 'incomes', label: 'Gelirler', icon: 'fas fa-arrow-up' },
            { id: 'expenses', label: 'Giderler', icon: 'fas fa-arrow-down' },
            { id: 'transfers', label: 'Virman', icon: 'fas fa-exchange-alt' },
            { id: 'dues', label: 'Aidat Takip', icon: 'fas fa-calendar-check' },
            { id: 'cash', label: 'Kasa', icon: 'fas fa-wallet' },
            { id: 'devir', label: 'Devir', icon: 'fas fa-forward' },
            { id: 'events', label: 'Etkinlikler', icon: 'fas fa-calendar-alt' },
            { id: 'meetings', label: 'Toplantılar', icon: 'fas fa-handshake' },
            { id: 'tahakkuk', label: 'Tahakkuk Rapor', icon: 'fas fa-file-invoice-dollar' },
            { id: 'budget', label: 'Bütçe', icon: 'fas fa-calculator' },
            { id: 'reports', label: 'Raporlar', icon: 'fas fa-chart-bar' },
            { id: 'export', label: 'Excel/PDF Export', icon: 'fas fa-file-export' },
            { id: 'documents', label: 'Belgeler', icon: 'fas fa-folder-open' },
            { id: 'ocr', label: 'OCR Tarama', icon: 'fas fa-camera' },
            { id: 'users', label: 'Kullanıcılar', icon: 'fas fa-user-cog' },
            { id: 'village', label: 'Köy İşlemleri', icon: 'fas fa-tree', submenu: true },
            { id: 'settings', label: 'Ayarlar', icon: 'fas fa-cog' },
        ],
        
        // Data
        stats: { totalMembers: 0, totalIncome: 0, totalExpense: 0, balance: 0 },
        members: [],
        filteredMembers: [],
        memberSearch: '',
        inactiveMembers: [],
        incomes: [],
        recentIncomes: [],
        expenses: [],
        recentExpenses: [],
        dues: [],
        duesStats: { expected: 0, collected: 0, remaining: 0 },
        cashAccounts: [],
        transfers: [],
        events: [],
        meetings: [],
        users: [],
        documents: [],
        budgetItems: [],
        tahakkukData: { stats: {}, members: [] },
        devirData: { previous_balance: 0, current_year: 2025 },
        monthlyReport: [],
        categoryReport: [],
        settings: { organization_name: '', yearly_dues: 100 },
        
        // Village Data
        villageIncomes: [],
        villageExpenses: [],
        villageCash: [],
        villageTransfers: [],
        villageStats: { totalIncome: 0, totalExpense: 0, balance: 0 },
        villageTab: 'incomes',
        
        // Member Detail
        selectedMember: null,
        memberDetailModal: false,
        memberDetail: { member: {}, incomes: [], dues: [] },
        
        // Filters
        incomeFilter: { year: '2025', category: '' },
        expenseFilter: { year: '2025', category: '' },
        duesYear: '2025',
        transferYear: '2025',
        
        // Modals
        memberModal: false,
        incomeModal: false,
        expenseModal: false,
        transferModal: false,
        eventModal: false,
        meetingModal: false,
        userModal: false,
        budgetModal: false,
        documentModal: false,
        devirModal: false,
        villageIncomeModal: false,
        villageExpenseModal: false,
        villageTransferModal: false,
        editingMember: null,
        editingIncome: null,
        editingExpense: null,
        editingTransfer: null,
        editingEvent: null,
        editingMeeting: null,
        editingUser: null,
        editingBudget: null,
        editingDocument: null,
        memberForm: { full_name: '', phone: '', tc_no: '', email: '', address: '', status: 'Aktif' },
        incomeForm: { date: '', category: 'AİDAT', amount: '', description: '', cash_account: 'Ana Kasa' },
        expenseForm: { date: '', category: 'DİĞER', amount: '', description: '', vendor: '', cash_account: 'Ana Kasa' },
        transferForm: { from_account: 'Ana Kasa', to_account: 'Banka', amount: '', date: '', description: '' },
        eventForm: { title: '', event_type: 'Genel', description: '', start_date: '', end_date: '', location: '', budget: 0, status: 'Planlanan' },
        meetingForm: { title: '', meeting_date: '', location: '', agenda: '', attendees: '', decisions: '', minutes: '', status: 'Planlanan' },
        userForm: { username: '', password: '', full_name: '', email: '', phone: '', role: 'member' },
        budgetForm: { year: 2025, category: '', type: 'expense', planned_amount: 0, notes: '' },
        documentForm: { filename: '', category: 'Genel', description: '' },
        devirForm: { year: 2024, amount: 0, notes: '' },
        villageIncomeForm: { date: '', category: '', amount: '', description: '', cash_account: 'Köy Kasası' },
        villageExpenseForm: { date: '', category: '', amount: '', description: '', cash_account: 'Köy Kasası' },
        villageTransferForm: { from_account: 'Ana Kasa', to_account: 'Köy Kasası', amount: '', date: '', description: '' },
        
        // OCR
        ocrResult: null,
        ocrProcessing: false,
        
        // Toast
        toast: { show: false, message: '', type: 'success' },
        
        // Initialize
        async init() {
            const stored = localStorage.getItem('bader_session');
            if (stored) {
                try {
                    const session = JSON.parse(stored);
                    this.token = session.token;
                    this.user = session.user;
                    this.customerId = session.customer_id;
                    await this.loadDashboard();
                } catch (e) {
                    localStorage.removeItem('bader_session');
                }
            }
            this.loading = false;
        },
        
        // API Helper
        async api(endpoint, method = 'GET', data = null) {
            const headers = { 'Content-Type': 'application/json' };
            if (this.token) headers['Authorization'] = `Bearer ${this.token}`;
            if (this.customerId) headers['X-Customer-ID'] = this.customerId;
            
            const options = { method, headers };
            if (data) options.body = JSON.stringify(data);
            
            try {
                const response = await fetch(`${API_URL}${endpoint}`, options);
                if (response.status === 401) {
                    this.logout();
                    throw new Error('Oturum süresi doldu');
                }
                return await response.json();
            } catch (error) {
                console.error('API Error:', error);
                throw error;
            }
        },
        
        // Login
        async login() {
            this.loginLoading = true;
            this.loginError = '';
            
            try {
                const result = await this.api('/auth/login', 'POST', this.loginForm);
                if (result.success) {
                    this.token = result.token;
                    this.user = result.user;
                    this.customerId = this.loginForm.customer_id;
                    localStorage.setItem('bader_session', JSON.stringify({
                        token: this.token, user: this.user, customer_id: this.customerId
                    }));
                    await this.loadDashboard();
                    this.showToast('Giriş başarılı!', 'success');
                } else {
                    this.loginError = result.detail || 'Giriş başarısız';
                }
            } catch (error) {
                this.loginError = error.message || 'Bağlantı hatası';
            }
            this.loginLoading = false;
        },
        
        logout() {
            this.user = null;
            this.token = null;
            this.customerId = null;
            localStorage.removeItem('bader_session');
            this.currentPage = 'dashboard';
        },
        
        // Load Dashboard Data
        async loadDashboard() {
            try {
                const [membersRes, incomesRes, expensesRes] = await Promise.all([
                    this.api('/web/members'),
                    this.api('/web/incomes?year=2025'),
                    this.api('/web/expenses?year=2025')
                ]);
                
                this.members = membersRes.members || [];
                this.filteredMembers = [...this.members];
                this.incomes = incomesRes.incomes || [];
                this.recentIncomes = [...this.incomes].slice(0, 5);
                this.expenses = expensesRes.expenses || [];
                this.recentExpenses = [...this.expenses].slice(0, 5);
                
                this.stats.totalMembers = this.members.filter(m => m.status === 'Aktif').length;
                this.stats.totalIncome = this.incomes.reduce((a, b) => a + parseFloat(b.amount || 0), 0);
                this.stats.totalExpense = this.expenses.reduce((a, b) => a + parseFloat(b.amount || 0), 0);
                this.stats.balance = this.stats.totalIncome - this.stats.totalExpense;
                
                try {
                    const cashRes = await this.api('/web/cash-accounts');
                    this.cashAccounts = cashRes.accounts || [];
                } catch (e) {
                    this.cashAccounts = [
                        { id: 1, name: 'Ana Kasa', type: 'Nakit', balance: this.stats.balance },
                        { id: 2, name: 'Banka', type: 'Banka', balance: 0 }
                    ];
                }
            } catch (error) {
                console.error('Dashboard load error:', error);
            }
        },
        
        // ==================== MEMBERS ====================
        filterMembers() {
            const search = this.memberSearch.toLowerCase();
            this.filteredMembers = this.members.filter(m => 
                m.full_name?.toLowerCase().includes(search) ||
                m.phone?.includes(search) ||
                m.member_no?.toString().includes(search)
            );
        },
        
        openMemberModal() {
            this.editingMember = null;
            this.memberForm = { full_name: '', phone: '', tc_no: '', email: '', address: '', status: 'Aktif' };
            this.memberModal = true;
        },
        
        editMember(member) {
            this.editingMember = member;
            this.memberForm = { ...member };
            this.memberModal = true;
        },
        
        async saveMember() {
            try {
                if (this.editingMember) {
                    await this.api(`/web/members/${this.editingMember.id}`, 'PUT', this.memberForm);
                    this.showToast('Üye güncellendi', 'success');
                } else {
                    await this.api('/web/members', 'POST', this.memberForm);
                    this.showToast('Üye eklendi', 'success');
                }
                this.memberModal = false;
                await this.loadDashboard();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async deleteMember(member) {
            if (!confirm(`${member.full_name} silinsin mi?`)) return;
            try {
                await this.api(`/web/members/${member.id}`, 'DELETE');
                this.showToast('Üye ayrılanlar listesine taşındı', 'success');
                await this.loadDashboard();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async openMemberDetail(member) {
            try {
                const res = await this.api(`/web/members/${member.id}/detail`);
                this.memberDetail = res;
                this.memberDetailModal = true;
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== INACTIVE MEMBERS ====================
        async loadInactiveMembers() {
            try {
                const res = await this.api('/web/members/inactive');
                this.inactiveMembers = res.members || [];
            } catch (error) {
                console.error('Load inactive members error:', error);
            }
        },
        
        async reactivateMember(member) {
            if (!confirm(`${member.full_name} tekrar aktif edilsin mi?`)) return;
            try {
                await this.api(`/web/members/${member.id}/activate`, 'POST');
                this.showToast('Üye aktif edildi', 'success');
                await this.loadInactiveMembers();
                await this.loadDashboard();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== INCOMES ====================
        async loadIncomes() {
            try {
                const params = new URLSearchParams({ year: this.incomeFilter.year });
                if (this.incomeFilter.category) params.append('category', this.incomeFilter.category);
                const res = await this.api(`/web/incomes?${params}`);
                this.incomes = res.incomes || [];
            } catch (error) {
                console.error('Load incomes error:', error);
            }
        },
        
        openIncomeModal() {
            this.editingIncome = null;
            this.incomeForm = { date: new Date().toISOString().split('T')[0], category: 'AİDAT', amount: '', description: '', cash_account: 'Ana Kasa' };
            this.incomeModal = true;
        },
        
        editIncome(income) {
            this.editingIncome = income;
            this.incomeForm = { ...income };
            this.incomeModal = true;
        },
        
        async saveIncome() {
            try {
                if (this.editingIncome) {
                    await this.api(`/web/incomes/${this.editingIncome.id}`, 'PUT', this.incomeForm);
                    this.showToast('Gelir güncellendi', 'success');
                } else {
                    await this.api('/web/incomes', 'POST', this.incomeForm);
                    this.showToast('Gelir eklendi', 'success');
                }
                this.incomeModal = false;
                await this.loadIncomes();
                await this.loadDashboard();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async deleteIncome(income) {
            if (!confirm('Bu gelir kaydı silinsin mi?')) return;
            try {
                await this.api(`/web/incomes/${income.id}`, 'DELETE');
                this.showToast('Gelir silindi', 'success');
                await this.loadIncomes();
                await this.loadDashboard();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== EXPENSES ====================
        async loadExpenses() {
            try {
                const params = new URLSearchParams({ year: this.expenseFilter.year });
                if (this.expenseFilter.category) params.append('category', this.expenseFilter.category);
                const res = await this.api(`/web/expenses?${params}`);
                this.expenses = res.expenses || [];
            } catch (error) {
                console.error('Load expenses error:', error);
            }
        },
        
        openExpenseModal() {
            this.editingExpense = null;
            this.expenseForm = { date: new Date().toISOString().split('T')[0], category: 'DİĞER', amount: '', description: '', vendor: '', cash_account: 'Ana Kasa' };
            this.expenseModal = true;
        },
        
        editExpense(expense) {
            this.editingExpense = expense;
            this.expenseForm = { ...expense };
            this.expenseModal = true;
        },
        
        async saveExpense() {
            try {
                if (this.editingExpense) {
                    await this.api(`/web/expenses/${this.editingExpense.id}`, 'PUT', this.expenseForm);
                    this.showToast('Gider güncellendi', 'success');
                } else {
                    await this.api('/web/expenses', 'POST', this.expenseForm);
                    this.showToast('Gider eklendi', 'success');
                }
                this.expenseModal = false;
                await this.loadExpenses();
                await this.loadDashboard();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async deleteExpense(expense) {
            if (!confirm('Bu gider kaydı silinsin mi?')) return;
            try {
                await this.api(`/web/expenses/${expense.id}`, 'DELETE');
                this.showToast('Gider silindi', 'success');
                await this.loadExpenses();
                await this.loadDashboard();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== TRANSFERS ====================
        async loadTransfers() {
            try {
                const res = await this.api(`/web/transfers?year=${this.transferYear}`);
                this.transfers = res.transfers || [];
            } catch (error) {
                console.error('Load transfers error:', error);
            }
        },
        
        openTransferModal() {
            this.editingTransfer = null;
            this.transferForm = { from_account: 'Ana Kasa', to_account: 'Banka', amount: '', date: new Date().toISOString().split('T')[0], description: '' };
            this.transferModal = true;
        },
        
        async saveTransfer() {
            try {
                await this.api('/web/transfers', 'POST', this.transferForm);
                this.showToast('Virman oluşturuldu', 'success');
                this.transferModal = false;
                await this.loadTransfers();
                await this.loadDashboard();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async deleteTransfer(transfer) {
            if (!confirm('Bu virman silinsin mi?')) return;
            try {
                await this.api(`/web/transfers/${transfer.id}`, 'DELETE');
                this.showToast('Virman silindi', 'success');
                await this.loadTransfers();
                await this.loadDashboard();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== EVENTS ====================
        async loadEvents() {
            try {
                const res = await this.api('/web/events');
                this.events = res.events || [];
            } catch (error) {
                console.error('Load events error:', error);
            }
        },
        
        openEventModal() {
            this.editingEvent = null;
            this.eventForm = { title: '', event_type: 'Genel', description: '', start_date: '', end_date: '', location: '', budget: 0, status: 'Planlanan' };
            this.eventModal = true;
        },
        
        editEvent(event) {
            this.editingEvent = event;
            this.eventForm = { ...event };
            this.eventModal = true;
        },
        
        async saveEvent() {
            try {
                if (this.editingEvent) {
                    await this.api(`/web/events/${this.editingEvent.id}`, 'PUT', this.eventForm);
                    this.showToast('Etkinlik güncellendi', 'success');
                } else {
                    await this.api('/web/events', 'POST', this.eventForm);
                    this.showToast('Etkinlik oluşturuldu', 'success');
                }
                this.eventModal = false;
                await this.loadEvents();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async deleteEvent(event) {
            if (!confirm('Bu etkinlik silinsin mi?')) return;
            try {
                await this.api(`/web/events/${event.id}`, 'DELETE');
                this.showToast('Etkinlik silindi', 'success');
                await this.loadEvents();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== MEETINGS ====================
        async loadMeetings() {
            try {
                const res = await this.api('/web/meetings');
                this.meetings = res.meetings || [];
            } catch (error) {
                console.error('Load meetings error:', error);
            }
        },
        
        openMeetingModal() {
            this.editingMeeting = null;
            this.meetingForm = { title: '', meeting_date: '', location: '', agenda: '', attendees: '', decisions: '', minutes: '', status: 'Planlanan' };
            this.meetingModal = true;
        },
        
        editMeeting(meeting) {
            this.editingMeeting = meeting;
            this.meetingForm = { 
                ...meeting,
                agenda: Array.isArray(meeting.agenda) ? meeting.agenda.join('\n') : meeting.agenda,
                attendees: Array.isArray(meeting.attendees) ? meeting.attendees.join('\n') : meeting.attendees,
                decisions: Array.isArray(meeting.decisions) ? meeting.decisions.join('\n') : meeting.decisions
            };
            this.meetingModal = true;
        },
        
        async saveMeeting() {
            try {
                const data = {
                    ...this.meetingForm,
                    agenda: this.meetingForm.agenda ? this.meetingForm.agenda.split('\n').filter(x => x.trim()) : [],
                    attendees: this.meetingForm.attendees ? this.meetingForm.attendees.split('\n').filter(x => x.trim()) : [],
                    decisions: this.meetingForm.decisions ? this.meetingForm.decisions.split('\n').filter(x => x.trim()) : []
                };
                
                if (this.editingMeeting) {
                    await this.api(`/web/meetings/${this.editingMeeting.id}`, 'PUT', data);
                    this.showToast('Toplantı güncellendi', 'success');
                } else {
                    await this.api('/web/meetings', 'POST', data);
                    this.showToast('Toplantı oluşturuldu', 'success');
                }
                this.meetingModal = false;
                await this.loadMeetings();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async deleteMeeting(meeting) {
            if (!confirm('Bu toplantı silinsin mi?')) return;
            try {
                await this.api(`/web/meetings/${meeting.id}`, 'DELETE');
                this.showToast('Toplantı silindi', 'success');
                await this.loadMeetings();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== USERS ====================
        async loadUsers() {
            try {
                const res = await this.api('/web/users');
                this.users = res.users || [];
            } catch (error) {
                console.error('Load users error:', error);
            }
        },
        
        openUserModal() {
            this.editingUser = null;
            this.userForm = { username: '', password: '', full_name: '', email: '', phone: '', role: 'member' };
            this.userModal = true;
        },
        
        editUser(user) {
            this.editingUser = user;
            this.userForm = { ...user, password: '' };
            this.userModal = true;
        },
        
        async saveUser() {
            try {
                if (this.editingUser) {
                    await this.api(`/web/users/${this.editingUser.id}`, 'PUT', this.userForm);
                    this.showToast('Kullanıcı güncellendi', 'success');
                } else {
                    await this.api('/web/users', 'POST', this.userForm);
                    this.showToast('Kullanıcı oluşturuldu', 'success');
                }
                this.userModal = false;
                await this.loadUsers();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async deleteUser(user) {
            if (!confirm(`${user.full_name} silinsin mi?`)) return;
            try {
                await this.api(`/web/users/${user.id}`, 'DELETE');
                this.showToast('Kullanıcı silindi', 'success');
                await this.loadUsers();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== DUES ====================
        async loadDues() {
            try {
                const res = await this.api(`/web/dues?year=${this.duesYear}`);
                this.dues = res.dues || [];
                this.duesStats = res.stats || { expected: 0, collected: 0, remaining: 0 };
            } catch (error) {
                this.dues = this.members.slice(0, 10).map((m, i) => ({
                    id: i + 1,
                    member_name: m.full_name,
                    yearly_amount: 100,
                    paid_amount: i % 3 === 0 ? 100 : (i % 3 === 1 ? 50 : 0),
                    remaining: i % 3 === 0 ? 0 : (i % 3 === 1 ? 50 : 100),
                    status: i % 3 === 0 ? 'Tamamlandı' : (i % 3 === 1 ? 'Kısmi' : 'Bekliyor')
                }));
            }
        },
        
        async payDue(due) {
            const amount = prompt(`${due.member_name} için ödeme tutarı (Kalan: ₺${due.remaining}):`, due.remaining);
            if (!amount) return;
            try {
                await this.api('/web/dues/payment', 'POST', { due_id: due.id, amount: parseFloat(amount) });
                this.showToast('Ödeme kaydedildi', 'success');
                await this.loadDues();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== REPORTS ====================
        async loadReports() {
            try {
                const [monthly, category] = await Promise.all([
                    this.api('/web/reports/monthly?year=2025'),
                    this.api('/web/reports/category?year=2025&type=expense')
                ]);
                this.monthlyReport = monthly.months || [];
                this.categoryReport = category.categories || [];
            } catch (error) {
                console.error('Load reports error:', error);
            }
        },
        
        // ==================== EXPORT ====================
        async exportData(type) {
            try {
                const res = await this.api(`/web/export/${type}?year=2025`);
                this.downloadCSV(res.data, res.filename);
                this.showToast('Export tamamlandı', 'success');
            } catch (error) {
                this.showToast('Export hatası: ' + error.message, 'error');
            }
        },
        
        downloadCSV(data, filename) {
            if (!data || data.length === 0) {
                this.showToast('Veri bulunamadı', 'error');
                return;
            }
            const headers = Object.keys(data[0]);
            const csv = [
                headers.join(','),
                ...data.map(row => headers.map(h => `"${row[h] || ''}"`).join(','))
            ].join('\n');
            
            const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = filename;
            link.click();
        },
        
        // ==================== SETTINGS ====================
        async saveSettings() {
            try {
                await this.api('/web/settings', 'PUT', this.settings);
                this.showToast('Ayarlar kaydedildi', 'success');
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== TAHAKKUK RAPOR ====================
        async loadTahakkuk() {
            try {
                const res = await this.api(`/web/reports/dues?year=${this.duesYear}`);
                this.tahakkukData = res;
            } catch (error) {
                console.error('Load tahakkuk error:', error);
            }
        },
        
        // ==================== BUDGET ====================
        async loadBudget() {
            try {
                const res = await this.api(`/web/budget?year=2025`);
                this.budgetItems = res.items || [];
            } catch (error) {
                this.budgetItems = [];
            }
        },
        
        openBudgetModal() {
            this.editingBudget = null;
            this.budgetForm = { year: 2025, category: '', type: 'expense', planned_amount: 0, notes: '' };
            this.budgetModal = true;
        },
        
        async saveBudget() {
            try {
                if (this.editingBudget) {
                    await this.api(`/web/budget/${this.editingBudget.id}`, 'PUT', this.budgetForm);
                } else {
                    await this.api('/web/budget', 'POST', this.budgetForm);
                }
                this.showToast('Bütçe kaydedildi', 'success');
                this.budgetModal = false;
                await this.loadBudget();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== DOCUMENTS ====================
        async loadDocuments() {
            try {
                const res = await this.api('/web/documents');
                this.documents = res.documents || [];
            } catch (error) {
                this.documents = [];
            }
        },
        
        async uploadDocument(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            formData.append('category', this.documentForm.category || 'Genel');
            
            try {
                const response = await fetch(`${API_URL}/web/documents/upload`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'X-Customer-ID': this.customerId
                    },
                    body: formData
                });
                const result = await response.json();
                if (result.success) {
                    this.showToast('Belge yüklendi', 'success');
                    await this.loadDocuments();
                }
            } catch (error) {
                this.showToast('Yükleme hatası: ' + error.message, 'error');
            }
        },
        
        async deleteDocument(doc) {
            if (!confirm('Bu belge silinsin mi?')) return;
            try {
                await this.api(`/web/documents/${doc.id}`, 'DELETE');
                this.showToast('Belge silindi', 'success');
                await this.loadDocuments();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== OCR ====================
        async processOCR(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            this.ocrProcessing = true;
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch(`${API_URL}/web/ocr/scan`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.token}`,
                        'X-Customer-ID': this.customerId
                    },
                    body: formData
                });
                const result = await response.json();
                this.ocrResult = result;
                this.showToast('OCR tamamlandı', 'success');
            } catch (error) {
                this.showToast('OCR hatası: ' + error.message, 'error');
            }
            this.ocrProcessing = false;
        },
        
        async saveOCRAsExpense() {
            if (!this.ocrResult) return;
            try {
                this.expenseForm = {
                    date: this.ocrResult.date || new Date().toISOString().split('T')[0],
                    category: this.ocrResult.category || 'DİĞER',
                    amount: this.ocrResult.amount || 0,
                    description: this.ocrResult.description || '',
                    vendor: this.ocrResult.vendor || '',
                    cash_account: 'Ana Kasa'
                };
                await this.api('/web/expenses', 'POST', this.expenseForm);
                this.showToast('Gider olarak kaydedildi', 'success');
                this.ocrResult = null;
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== DEVIR ====================
        async loadDevir() {
            try {
                const res = await this.api('/web/devir/calculate?year=2024');
                this.devirData = res;
            } catch (error) {
                this.devirData = { previous_balance: 0, current_year: 2025 };
            }
        },
        
        async createDevir() {
            if (!confirm('2024 yılı devri oluşturulsun mu?')) return;
            try {
                await this.api('/web/devir', 'POST', { year: 2024, amount: this.devirData.previous_balance });
                this.showToast('Devir oluşturuldu', 'success');
                await this.loadDevir();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== VILLAGE ====================
        async loadVillage() {
            try {
                const [incomes, expenses, cash, transfers] = await Promise.all([
                    this.api('/web/village/incomes?year=2025'),
                    this.api('/web/village/expenses?year=2025'),
                    this.api('/web/village/cash-accounts'),
                    this.api('/web/village/transfers?year=2025')
                ]);
                this.villageIncomes = incomes.incomes || [];
                this.villageExpenses = expenses.expenses || [];
                this.villageCash = cash.accounts || [];
                this.villageTransfers = transfers.transfers || [];
                
                const totalIncome = this.villageIncomes.reduce((a, b) => a + parseFloat(b.amount || 0), 0);
                const totalExpense = this.villageExpenses.reduce((a, b) => a + parseFloat(b.amount || 0), 0);
                this.villageStats = { totalIncome, totalExpense, balance: totalIncome - totalExpense };
            } catch (error) {
                console.error('Load village error:', error);
            }
        },
        
        openVillageIncomeModal() {
            this.villageIncomeForm = { date: new Date().toISOString().split('T')[0], category: '', amount: '', description: '', cash_account: 'Köy Kasası' };
            this.villageIncomeModal = true;
        },
        
        async saveVillageIncome() {
            try {
                await this.api('/web/village/incomes', 'POST', this.villageIncomeForm);
                this.showToast('Köy geliri eklendi', 'success');
                this.villageIncomeModal = false;
                await this.loadVillage();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        openVillageExpenseModal() {
            this.villageExpenseForm = { date: new Date().toISOString().split('T')[0], category: '', amount: '', description: '', cash_account: 'Köy Kasası' };
            this.villageExpenseModal = true;
        },
        
        async saveVillageExpense() {
            try {
                await this.api('/web/village/expenses', 'POST', this.villageExpenseForm);
                this.showToast('Köy gideri eklendi', 'success');
                this.villageExpenseModal = false;
                await this.loadVillage();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        openVillageTransferModal() {
            this.villageTransferForm = { from_account: 'Ana Kasa', to_account: 'Köy Kasası', amount: '', date: new Date().toISOString().split('T')[0], description: '' };
            this.villageTransferModal = true;
        },
        
        async saveVillageTransfer() {
            try {
                await this.api('/web/village/transfers', 'POST', this.villageTransferForm);
                this.showToast('Köy virmanı oluşturuldu', 'success');
                this.villageTransferModal = false;
                await this.loadVillage();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // ==================== UTILITIES ====================
        formatMoney(amount) {
            return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(amount || 0);
        },
        
        formatDate(dateStr) {
            if (!dateStr) return '-';
            try { return new Date(dateStr).toLocaleDateString('tr-TR'); } catch { return dateStr; }
        },
        
        formatDateTime(dateStr) {
            if (!dateStr) return '-';
            try { return new Date(dateStr).toLocaleString('tr-TR'); } catch { return dateStr; }
        },
        
        showToast(message, type = 'success') {
            this.toast = { show: true, message, type };
            setTimeout(() => { this.toast.show = false; }, 3000);
        },
        
        getStatusColor(status) {
            const colors = {
                'Planlanan': 'bg-blue-100 text-blue-700',
                'Devam Ediyor': 'bg-yellow-100 text-yellow-700',
                'Tamamlandı': 'bg-green-100 text-green-700',
                'İptal': 'bg-red-100 text-red-700'
            };
            return colors[status] || 'bg-gray-100 text-gray-700';
        },
        
        getRoleLabel(role) {
            const roles = { admin: 'Yönetici', manager: 'Müdür', member: 'Üye' };
            return roles[role] || role;
        }
    };
}
