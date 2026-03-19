/**
 * MODULE SessionHelper - Logique JavaScript
 * Aide pour la séance (chrono + compteur)
 */

class SessionHelper {
  constructor() {
    // État chronomètre (DÉCOMPTE depuis 90s)
    this.chrono = {
      seconds: 90,
      running: false,
      interval: null
    };

    // État compteur
    this.sets = {
      current: 0,
      total: 12
    };

    // Éléments DOM
    this.initElements();
    this.initEvents();
    this.updateRingProgress();
  }

  initElements() {
    // Chronomètre
    this.chronoDisplay = document.getElementById('chronoDisplay');
    this.chronoPlay = document.getElementById('chronoPlay');
    this.chronoPause = document.getElementById('chronoPause');
    this.chronoReset = document.getElementById('chronoReset');

    // Compteur
    this.setCount = document.getElementById('setCount');
    this.setTotal = document.getElementById('setTotal');
    this.setMinus = document.getElementById('setMinus');
    this.setPlus = document.getElementById('setPlus');

    // Ring progress
    this.sessionRing = document.getElementById('sessionRing');
    this.sessionPercent = document.getElementById('sessionPercent');

    // Actions
    this.sessionContinue = document.getElementById('sessionContinue');
    this.sessionDetails = document.getElementById('sessionDetails');
  }

  initEvents() {
    // Chronomètre
    this.chronoPlay.addEventListener('click', () => this.startChrono());
    this.chronoPause.addEventListener('click', () => this.pauseChrono());
    this.chronoReset.addEventListener('click', () => this.resetChrono());

    // Compteur
    this.setMinus.addEventListener('click', () => this.decrementSet());
    this.setPlus.addEventListener('click', () => this.incrementSet());

    // Actions
    this.sessionContinue.addEventListener('click', () => this.continueSession());
    this.sessionDetails.addEventListener('click', () => this.showDetails());
  }

  // ===== CHRONOMÈTRE =====

  startChrono() {
    if (!this.chrono.running) {
      this.chrono.running = true;
      this.chronoPlay.style.display = 'none';
      this.chronoPause.style.display = 'flex';
      
      this.chrono.interval = setInterval(() => {
        if (this.chrono.seconds > 0) {
          this.chrono.seconds--; // DÉCOMPTE
          this.updateChronoDisplay();
        } else {
          // Temps écoulé
          this.pauseChrono();
        }
      }, 1000);
    }
  }

  pauseChrono() {
    if (this.chrono.running) {
      this.chrono.running = false;
      this.chronoPlay.style.display = 'flex';
      this.chronoPause.style.display = 'none';
      clearInterval(this.chrono.interval);
    }
  }

  resetChrono() {
    this.pauseChrono();
    this.chrono.seconds = 90; // Reset à 90 secondes
    this.updateChronoDisplay();
  }

  updateChronoDisplay() {
    const minutes = Math.floor(this.chrono.seconds / 60);
    const seconds = this.chrono.seconds % 60;
    const formatted = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    this.chronoDisplay.textContent = formatted;
  }

  // ===== COMPTEUR DE SÉRIES =====

  incrementSet() {
    if (this.sets.current < this.sets.total) {
      this.sets.current++;
      this.updateSetDisplay();
      this.updateRingProgress();
    }
  }

  decrementSet() {
    if (this.sets.current > 0) {
      this.sets.current--;
      this.updateSetDisplay();
      this.updateRingProgress();
    }
  }

  updateSetDisplay() {
    this.setCount.textContent = this.sets.current;
  }

  // ===== RING PROGRESS =====

  updateRingProgress() {
    const percent = Math.round((this.sets.current / this.sets.total) * 100);
    this.sessionPercent.textContent = `${percent}%`;
    
    // Mise à jour du gradient conic
    const degrees = (percent / 100) * 360;
    this.sessionRing.style.background = `conic-gradient(#ff8c42 0deg ${degrees}deg, #39414d ${degrees}deg 360deg)`;
  }

  // ===== ACTIONS =====

  continueSession() {
    // Passer à la série suivante automatiquement
    this.incrementSet();
  }

  showDetails() {
    alert('Fonction "Détails" à implémenter');
  }
}

// Initialisation automatique quand le DOM est prêt
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.sessionHelper = new SessionHelper();
  });
} else {
  window.sessionHelper = new SessionHelper();
}
