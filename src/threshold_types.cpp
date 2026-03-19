// threshold_types.cpp — Implémentation méthodes structures
// ─────────────────────────────────────────────────────────────────────────────
#include "threshold_types.h"

namespace threshold {

void Repas::calculer_totaux() {
    totaux = Macros(0, 0, 0, 0, 0);
    for (const auto& item : items) {
        totaux.kcal += item.macros_portion.kcal;
        totaux.proteines += item.macros_portion.proteines;
        totaux.glucides += item.macros_portion.glucides;
        totaux.lipides += item.macros_portion.lipides;
        totaux.fibres += item.macros_portion.fibres;
    }
}

void PlanJournalier::calculer_totaux() {
    totaux_jour = Macros(0, 0, 0, 0, 0);
    for (const auto& r : repas) {
        totaux_jour.kcal += r.totaux.kcal;
        totaux_jour.proteines += r.totaux.proteines;
        totaux_jour.glucides += r.totaux.glucides;
        totaux_jour.lipides += r.totaux.lipides;
        totaux_jour.fibres += r.totaux.fibres;
    }
}

void PlanMultiJours::calculer_moyennes() {
    if (jours.empty()) {
        objectifs_moyens = Macros(0, 0, 0, 0, 0);
        return;
    }
    
    float total_kcal = 0, total_prot = 0, total_gluc = 0, total_lip = 0, total_fib = 0;
    
    for (const auto& j : jours) {
        total_kcal += j.totaux_jour.kcal;
        total_prot += j.totaux_jour.proteines;
        total_gluc += j.totaux_jour.glucides;
        total_lip += j.totaux_jour.lipides;
        total_fib += j.totaux_jour.fibres;
    }
    
    float n = static_cast<float>(jours.size());
    objectifs_moyens.kcal = total_kcal / n;
    objectifs_moyens.proteines = total_prot / n;
    objectifs_moyens.glucides = total_gluc / n;
    objectifs_moyens.lipides = total_lip / n;
    objectifs_moyens.fibres = total_fib / n;
}

} // namespace threshold
