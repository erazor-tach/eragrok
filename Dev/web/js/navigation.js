/**
 * THRESHOLD - Navigation système
 * Gère la navigation entre les pages de l'app
 */

(function() {
  'use strict';

  // Mapping des pages
  const pageMap = {
    'index.html': 0,      // Dashboard
    'workout.html': 1,    // Workouts
    'nutrition.html': 2,  // Nutrition
    'progres.html': 3,    // Progrès
    'cycle.html': 4,      // Cycle
    'settings.html': 5    // Settings
  };

  const pages = [
    'index.html',
    'workout.html',
    'nutrition.html',
    'progres.html',
    'cycle.html',
    'settings.html'
  ];

  // Initialiser la navigation
  function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    
    if (!navItems || navItems.length === 0) {
      console.warn('Navigation items not found');
      return;
    }

    // Déterminer la page actuelle
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const currentIndex = pageMap[currentPage] !== undefined ? pageMap[currentPage] : 0;

    // Marquer la page active
    navItems.forEach((item, index) => {
      // Retirer active de tous
      item.classList.remove('active');
      
      // Ajouter active à la page courante
      if (index === currentIndex) {
        item.classList.add('active');
      }

      // Ajouter les événements de clic
      item.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Navigation vers la page
        if (index < pages.length) {
          window.location.href = pages[index];
        }
      });
    });

    console.log(`✅ Navigation initialisée - Page active: ${currentPage} (index ${currentIndex})`);
  }

  // Démarrer quand le DOM est prêt
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNavigation);
  } else {
    initNavigation();
  }
})();
