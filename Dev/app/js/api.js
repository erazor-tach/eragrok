/**
 * THRESHOLD — Client API CGI
 * Appels vers le backend C++ via Apache CGI
 */
const API_BASE = '/cgi-bin/threshold.cgi';

const ThresholdAPI = {
    async call(action, params = {}) {
        const qs = new URLSearchParams({action, ...params});
        const resp = await fetch(`${API_BASE}?${qs}`);
        if (!resp.ok) throw new Error(`API error: ${resp.status}`);
        return resp.json();
    },

    // Profil
    getProfile(name)  { return this.call('profile_get', {name}); },
    listProfiles()    { return this.call('profile_list'); },

    // Nutrition
    getTDEE(name)     { return this.call('tdee_from_profile', {name}); },

    // Catalogue
    getFoodList()     { return this.call('food_list'); },

    // Exercices & Techniques
    getExerciseList() { return this.call('exercise_list'); },
    getTechniqueList(){ return this.call('technique_list'); },

    // Planning / Séances
    getPlanningToday(name) { return this.call('planning_today', {name}); },
    getPlanningRange(name, start, end) { return this.call('planning_range', {name, start, end}); },
    addPlanning(name, fields) { return this.call('planning_add', {name, ...fields}); },

    // Meal planner
    generateMeal(name, n_repas = 4) {
        return this.call('meal', {name, n_repas: String(n_repas)});
    },

    // Update profile
    updateProfile(old_name, fields) {
        return this.call('profile_update', {old_name, ...fields});
    },
};

// ── Active user management ───────────────────────────────────────────────
// Stores active user in sessionStorage so rename doesn't break navigation
const ThresholdUser = {
    get() {
        return sessionStorage.getItem('threshold_user') || 'Erazor';
    },
    set(name) {
        sessionStorage.setItem('threshold_user', name);
    },
    async init() {
        // If no user in session, pick the first one from DB
        let user = sessionStorage.getItem('threshold_user');
        if (!user) {
            try {
                const list = await ThresholdAPI.listProfiles();
                if (list.users && list.users.length > 0) {
                    user = list.users[0];
                    this.set(user);
                }
            } catch(e) { user = 'Erazor'; }
        }
        return user;
    }
};

// Auto-load profile initials + name on every page
(async function() {
    const USER = await ThresholdUser.init();
    try {
        const p = await ThresholdAPI.getProfile(USER);
        if (p.nom) {
            // Update session in case DB has a slightly different name
            ThresholdUser.set(p.nom);
            // Initiales en haut à droite
            const ini = document.getElementById('profile-initials');
            if (ini) {
                const parts = p.nom.trim().split(/\s+/);
                ini.textContent = parts.length > 1
                    ? (parts[0][0] + parts[parts.length-1][0]).toUpperCase()
                    : p.nom.substring(0, 2).toUpperCase();
            }
            // Nom dans le heading
            const nameEl = document.getElementById('user-name');
            if (nameEl) nameEl.textContent = p.nom;
        }
    } catch(e) { /* API offline — keep defaults */ }
})();
