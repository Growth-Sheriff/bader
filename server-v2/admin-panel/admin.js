// BADER Süper Admin Panel - JavaScript
const API_URL = window.location.origin + '/api/admin/api';

function adminApp() {
    return {
        // State
        loading: true,
        admin: null,
        token: null,
        currentPage: 'dashboard',
        
        // Login
        loginForm: { username: '', password: '' },
        loginLoading: false,
        loginError: '',
        
        // Dashboard
        dashboard: { stats: {}, license_distribution: {}, recent_activity: [] },
        
        // Customers
        customers: [],
        customerSearch: '',
        customerFilter: { type: '', status: '' },
        customerModal: false,
        editingCustomer: null,
        customerForm: {
            organization_name: '',
            contact_name: '',
            contact_email: '',
            contact_phone: '',
            license_type: 'DEMO',
            monthly_fee: 0,
            notes: ''
        },
        
        // Licenses
        licenseForm: {
            license_type: 'LOCAL',
            organization_name: '',
            contact_name: '',
            contact_email: '',
            contact_phone: '',
            license_days: 365,
            max_users: 5,
            max_members: 500
        },
        generatedLicense: null,
        expiringLicenses: [],
        
        // Versions
        versions: [],
        versionModal: false,
        versionForm: {
            version: '',
            platform: 'all',
            download_url: '',
            release_notes: '',
            is_mandatory: false
        },
        
        // Stats
        revenueStats: null,
        usageStats: null,
        
        // Logs
        logs: [],
        
        // Toast
        toast: { show: false, message: '', type: 'success' },
        
        // Init
        async init() {
            const session = localStorage.getItem('bader_admin_session');
            if (session) {
                try {
                    const data = JSON.parse(session);
                    this.token = data.token;
                    this.admin = data.admin;
                    await this.loadDashboard();
                } catch (e) {
                    localStorage.removeItem('bader_admin_session');
                }
            }
            this.loading = false;
        },
        
        // API Helper
        async api(endpoint, method = 'GET', body = null) {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json'
                }
            };
            
            if (this.token) {
                options.headers['Authorization'] = `Bearer ${this.token}`;
            }
            
            if (body) {
                options.body = JSON.stringify(body);
            }
            
            const response = await fetch(`${API_URL}${endpoint}`, options);
            
            if (response.status === 401) {
                this.logout();
                throw new Error('Oturum süresi doldu');
            }
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Bir hata oluştu');
            }
            
            return data;
        },
        
        // Auth
        async login() {
            this.loginLoading = true;
            this.loginError = '';
            
            try {
                const res = await this.api('/auth/login', 'POST', this.loginForm);
                this.token = res.token;
                this.admin = res.admin;
                localStorage.setItem('bader_admin_session', JSON.stringify({ token: this.token, admin: this.admin }));
                await this.loadDashboard();
            } catch (error) {
                this.loginError = error.message;
            }
            
            this.loginLoading = false;
        },
        
        logout() {
            this.admin = null;
            this.token = null;
            localStorage.removeItem('bader_admin_session');
            this.currentPage = 'dashboard';
        },
        
        // Dashboard
        async loadDashboard() {
            try {
                this.dashboard = await this.api('/dashboard');
            } catch (error) {
                console.error('Dashboard error:', error);
            }
        },
        
        // Customers
        async loadCustomers() {
            try {
                const params = new URLSearchParams();
                if (this.customerFilter.type) params.append('license_type', this.customerFilter.type);
                if (this.customerFilter.status) params.append('license_status', this.customerFilter.status);
                if (this.customerSearch) params.append('search', this.customerSearch);
                
                const res = await this.api(`/customers?${params}`);
                this.customers = res.customers || [];
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        filterCustomers() {
            // Client-side filtering is already done in loadCustomers
            this.loadCustomers();
        },
        
        openNewCustomerModal() {
            this.editingCustomer = null;
            this.customerForm = {
                organization_name: '',
                contact_name: '',
                contact_email: '',
                contact_phone: '',
                license_type: 'DEMO',
                license_days: 365,
                monthly_fee: 0,
                notes: ''
            };
            this.customerModal = true;
        },
        
        editCustomer(customer) {
            this.editingCustomer = customer;
            this.customerForm = { ...customer };
            this.customerModal = true;
        },
        
        async saveCustomer() {
            try {
                if (this.editingCustomer) {
                    await this.api(`/customers/${this.editingCustomer.customer_id}`, 'PUT', this.customerForm);
                    this.showToast('Müşteri güncellendi', 'success');
                } else {
                    await this.api('/customers', 'POST', this.customerForm);
                    this.showToast('Müşteri oluşturuldu', 'success');
                }
                this.customerModal = false;
                await this.loadCustomers();
                await this.loadDashboard();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async viewCustomer(customer) {
            try {
                const res = await this.api(`/customers/${customer.customer_id}`);
                alert(JSON.stringify(res.customer, null, 2));
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async extendLicense(customer) {
            const days = prompt('Kaç gün uzatılsın?', '365');
            if (!days) return;
            
            try {
                await this.api(`/licenses/${customer.customer_id}/extend?days=${days}`, 'PUT');
                this.showToast('Lisans uzatıldı', 'success');
                await this.loadCustomers();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async extendLicenseById(customerId) {
            const days = prompt('Kaç gün uzatılsın?', '365');
            if (!days) return;
            
            try {
                await this.api(`/licenses/${customerId}/extend?days=${days}`, 'PUT');
                this.showToast('Lisans uzatıldı', 'success');
                await this.loadExpiringLicenses();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async suspendLicense(customer) {
            if (!confirm(`${customer.organization_name} lisansı askıya alınsın mı?`)) return;
            
            try {
                await this.api(`/licenses/${customer.customer_id}/suspend`, 'PUT');
                this.showToast('Lisans askıya alındı', 'success');
                await this.loadCustomers();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async activateLicense(customer) {
            try {
                await this.api(`/licenses/${customer.customer_id}/activate`, 'PUT');
                this.showToast('Lisans aktifleştirildi', 'success');
                await this.loadCustomers();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // Licenses
        async generateLicense() {
            try {
                const res = await this.api('/licenses/generate', 'POST', this.licenseForm);
                this.generatedLicense = res.license;
                this.showToast('Lisans oluşturuldu', 'success');
                await this.loadDashboard();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        copyLicense() {
            if (this.generatedLicense) {
                navigator.clipboard.writeText(this.generatedLicense.customer_id);
                this.showToast('Lisans kodu kopyalandı', 'success');
            }
        },
        
        async loadExpiringLicenses() {
            try {
                const res = await this.api('/licenses/expiring?days=30');
                this.expiringLicenses = res.customers || [];
            } catch (error) {
                console.error('Expiring licenses error:', error);
            }
        },
        
        // Versions
        async loadVersions() {
            try {
                const res = await this.api('/versions');
                this.versions = res.versions || [];
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        openVersionModal() {
            this.versionForm = {
                version: '',
                platform: 'all',
                download_url: '',
                release_notes: '',
                is_mandatory: false
            };
            this.versionModal = true;
        },
        
        async saveVersion() {
            try {
                await this.api('/versions', 'POST', this.versionForm);
                this.showToast('Versiyon eklendi', 'success');
                this.versionModal = false;
                await this.loadVersions();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        async deleteVersion(id) {
            if (!confirm('Bu versiyon silinsin mi?')) return;
            
            try {
                await this.api(`/versions/${id}`, 'DELETE');
                this.showToast('Versiyon silindi', 'success');
                await this.loadVersions();
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // Stats
        async loadStats() {
            try {
                this.revenueStats = await this.api('/stats/revenue');
                this.usageStats = await this.api('/stats/usage?days=30');
            } catch (error) {
                console.error('Stats error:', error);
            }
        },
        
        // Logs
        async loadLogs() {
            try {
                const res = await this.api('/logs?limit=100');
                this.logs = res.logs || [];
            } catch (error) {
                this.showToast('Hata: ' + error.message, 'error');
            }
        },
        
        // Utilities
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
        }
    };
}
