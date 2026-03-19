/**
 * THRESHOLD — Navigation inter-pages
 * Gère les clics sur la bottom-nav pour naviguer entre les 6 pages.
 */
(function() {
  const pages = [
    'dashboard.html',
    'workouts.html',
    'nutrition.html',
    'progres.html',
    'cycle.html',
    'settings.html'
  ];

  document.querySelectorAll('.bottom-nav .nav-item').forEach(function(item, index) {
    item.addEventListener('click', function() {
      if (!item.classList.contains('active')) {
        window.location.href = pages[index];
      }
    });
    item.style.cursor = 'pointer';
  });
})();
