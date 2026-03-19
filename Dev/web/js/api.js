/**
 * THRESHOLD - API Client
 * Appelle le backend C++ via Apache CGI
 */

const API_BASE = 'http://localhost/cgi-bin/threshold.cgi';

/**
 * Calculer TDEE et macros
 */
async function calculateTDEE(age, poids, taille, sexe, activite) {
    const url = `${API_BASE}?action=tdee&age=${age}&poids=${poids}&taille=${taille}&sexe=${sexe}&activite=${activite}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Erreur API TDEE:', error);
        return null;
    }
}

/**
 * Générer plan repas
 */
async function generateMealPlan(nbRepas, targetCalories) {
    const url = `${API_BASE}?action=meal&nb_repas=${nbRepas}&calories=${targetCalories}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Erreur API Meal:', error);
        return null;
    }
}

/**
 * Exemple d'utilisation
 */
async function testAPI() {
    console.log('🧪 Test API Backend C++...');
    
    // Test TDEE
    const result = await calculateTDEE(30, 85, 180, 'homme', 'actif');
    console.log('TDEE Result:', result);
    
    if (result && !result.error) {
        console.log(`✅ TDEE: ${result.tdee} kcal`);
        console.log(`✅ Calories: ${result.calories} kcal`);
        console.log(`✅ Protéines: ${result.proteines}g`);
        console.log(`✅ Glucides: ${result.glucides}g`);
        console.log(`✅ Lipides: ${result.lipides}g`);
    } else {
        console.error('❌ Erreur:', result?.error || 'Unknown error');
    }
}

// Export pour utilisation dans d'autres fichiers
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { calculateTDEE, generateMealPlan };
}
