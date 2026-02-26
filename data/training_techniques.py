# data/training_techniques.py
# -*- coding: utf-8 -*-
"""
Table des techniques : id, nom, catégorie, reps, charge, repos, objectif, difficulte (existante),
programme_recommande, notes.
Ajout automatique : difficulty_level (1-5) pour usage direct dans l'export PDF.
"""

import csv
import os
import datetime
from typing import List, Dict, Any

TECHNIQUES: List[Dict[str, Any]] = [
    # ---------------- SARCOPLASMIQUE
    {
        "id": "bfr",
        "nom": "Blood Flow Restriction (BFR)",
        "categorie": "SARCOPLASMIQUE",
        "reps": "15–30",
        "charge": "~20–30%",
        "repos": "Court",
        "objectif": "Pump extrême, hypertrophie sarcoplasmique",
        "difficulte": 5,
        "difficulty_level": 2,
        "programme_recommande": "Sarco",
        "notes": "Occlusion/Kaatsu; précautions vasculaires."
    },
    {
        "id": "inter_set_stretch",
        "nom": "Inter-set stretching",
        "categorie": "SARCOPLASMIQUE",
        "reps": "20–60 s stretch entre sets",
        "charge": "Modérée",
        "repos": "Pendant le stretch",
        "objectif": "Pump + stretch-mediated growth",
        "difficulte": 4,
        "difficulty_level": 3,
        "programme_recommande": "Sarco",
        "notes": "Étirements entre séries pour congestion."
    },
    {
        "id": "21s",
        "nom": "21's (7-7-7)",
        "categorie": "SARCOPLASMIQUE",
        "reps": "7 bas + 7 haut + 7 complète",
        "charge": "Légère–modérée",
        "repos": "Aucun",
        "objectif": "Temps sous tension élevé, pump",
        "difficulte": 3,
        "difficulty_level": 3,
        "programme_recommande": "Sarco",
        "notes": "Séries continues, simple et efficace."
    },
    {
        "id": "tempo_lent",
        "nom": "Tempo lent / Superslow",
        "categorie": "SARCOPLASMIQUE",
        "reps": "3–10 s tempo",
        "charge": "Légère–modérée",
        "repos": "Variable",
        "objectif": "Max TUT et signalisation hypertrophique",
        "difficulte": 3,
        "difficulty_level": 3,
        "programme_recommande": "Sarco",
        "notes": "Accent sur la phase excentrique/contrainte temporelle."
    },
    {
        "id": "pre_post_fatigue",
        "nom": "Pré-fatigue / Post-fatigue",
        "categorie": "SARCOPLASMIQUE",
        "reps": "Variation",
        "charge": "Modérée",
        "repos": "Court",
        "objectif": "Recrutement ciblé",
        "difficulte": 3,
        "difficulty_level": 3,
        "programme_recommande": "Sarco",
        "notes": "Pré-fatigue d'un muscle accessoire avant le composé."
    },
    {
        "id": "supersets",
        "nom": "Supersets / Giant sets / Bi-sets",
        "categorie": "SARCOPLASMIQUE",
        "reps": "8–20",
        "charge": "~60–70%",
        "repos": "Très court",
        "objectif": "Congestion, volume",
        "difficulte": 4,
        "difficulty_level": 4,
        "programme_recommande": "Sarco",
        "notes": "Augmente densité et pump."
    },
    {
        "id": "trisets",
        "nom": "Trisets / séries combinées",
        "categorie": "SARCOPLASMIQUE",
        "reps": "8–20",
        "charge": "Modérée",
        "repos": "Très court",
        "objectif": "Congestion intense",
        "difficulte": 4,
        "difficulty_level": 4,
        "programme_recommande": "Sarco",
        "notes": "Combinaisons de 3 exercices sans repos."
    },
    {
        "id": "gvt_10x10",
        "nom": "German Volume Training (10×10)",
        "categorie": "SARCOPLASMIQUE",
        "reps": "10×10",
        "charge": "60–80%",
        "repos": "90–120 s",
        "objectif": "Volume massif (stress métabolique)",
        "difficulte": 3,
        "difficulty_level": 4,
        "programme_recommande": "Sarco",
        "notes": "Volume élevé; planifier récupération."
    },
    {
        "id": "myo_reps_sarco",
        "nom": "Myo-reps (variante sarcoplasmique)",
        "categorie": "SARCOPLASMIQUE",
        "reps": "Activation + mini-sets",
        "charge": "Modérée",
        "repos": "Très court",
        "objectif": "Volume efficace, pump",
        "difficulte": 4,
        "difficulty_level": 4,
        "programme_recommande": "Sarco",
        "notes": "Variante orientée congestion."
    },
    {
        "id": "back_off_sets",
        "nom": "Back-off sets",
        "categorie": "SARCOPLASMIQUE",
        "reps": "1–3 séries légères après lourdes",
        "charge": "60–70% après lourd",
        "repos": "Moyen",
        "objectif": "Volume additionnel sans trop fatiguer SNC",
        "difficulte": 4,
        "difficulty_level": 3,
        "programme_recommande": "Sarco",
        "notes": "Ajout de volume après travail lourd."
    },
    {
        "id": "fst7",
        "nom": "FST-7",
        "categorie": "SARCOPLASMIQUE",
        "reps": "7 séries fin de muscle",
        "charge": "60–70%",
        "repos": "30–45 s",
        "objectif": "Pump extrême + étirement fascia",
        "difficulte": 3,
        "difficulty_level": 3,
        "programme_recommande": "Sarco",
        "notes": "Finisher orienté esthétique."
    },
    {
        "id": "drop_sets",
        "nom": "Drop sets / séries dégressives",
        "categorie": "SARCOPLASMIQUE",
        "reps": "8–15 + drops",
        "charge": "Modérée → faible",
        "repos": "Minimum",
        "objectif": "Max volume, pump",
        "difficulte": 2,
        "difficulty_level": 2,
        "programme_recommande": "Sarco",
        "notes": "Technique de fin de set."
    },
    {
        "id": "rest_pause_sarco",
        "nom": "Rest-pause (variante sarco)",
        "categorie": "SARCOPLASMIQUE",
        "reps": "8–12 + mini-pauses",
        "charge": "65–80%",
        "repos": "Très court",
        "objectif": "Volume densifié",
        "difficulte": 3,
        "difficulty_level": 3,
        "programme_recommande": "Sarco",
        "notes": "Densification; attention à la fatigue locale."
    },
    {
        "id": "burns_partials",
        "nom": "Burns / partials rapides en fin de set",
        "categorie": "SARCOPLASMIQUE",
        "reps": "10–20 petites reps rapides",
        "charge": "Très légère",
        "repos": "Aucun",
        "objectif": "Vider le muscle, pump final",
        "difficulte": 3,
        "difficulty_level": 2,
        "programme_recommande": "Sarco",
        "notes": "Fin de set, très fatigant localement."
    },
    # Ajout demandé : Séries 10–12 (standard)
    {
        "id": "series_10_12_standard",
        "nom": "Séries 10–12 (standard)",
        "categorie": "SARCOPLASMIQUE",
        "reps": "8–15 (idéal 10–12)",
        "charge": "60–75%",
        "repos": "60–90 s",
        "objectif": "Volume métabolique, temps sous tension, hypertrophie sarcoplasmique",
        "difficulte": 3,
        "difficulty_level": 3,
        "programme_recommande": "Sarco",
        "notes": "Série de base : 3–4 séries de 10–12 répétitions. Cadence contrôlée; compatible avec supersets, drop sets ou finishers."
    },

    # ---------------- MIXTE
    {
        "id": "isometrique",
        "nom": "Isométrique (holds, pauses)",
        "categorie": "MIXTE",
        "reps": "Temps sous tension",
        "charge": "Selon capacité",
        "repos": "Moyen",
        "objectif": "Activation, endurance",
        "difficulte": 5,
        "difficulty_level": 3,
        "programme_recommande": "Mixte",
        "notes": "Maintien de contraction; utile pour contrôle."
    },
    {
        "id": "paused_reps",
        "nom": "Paused reps",
        "categorie": "MIXTE",
        "reps": "8–12 avec pause 1–3 s",
        "charge": "70–85%",
        "repos": "Moyen",
        "objectif": "Tension mécanique maximale",
        "difficulte": 3,
        "difficulty_level": 4,
        "programme_recommande": "Myofi",
        "notes": "Élimine l'élan; renforce la position."
    },
    {
        "id": "lengthened_partials",
        "nom": "Lengthened partials",
        "categorie": "MIXTE",
        "reps": "Partiels en position étirée",
        "charge": "Modérée–Lourde",
        "repos": "Standard",
        "objectif": "Hypertrophie via stretch-mediated",
        "difficulte": 3,
        "difficulty_level": 3,
        "programme_recommande": "Sarco",
        "notes": "Mixte; souvent utilisé pour stretch-mediated growth."
    },
    {
        "id": "6_12_25",
        "nom": "6 / 12 / 25",
        "categorie": "MIXTE",
        "reps": "6 / 12 / 25",
        "charge": "Variable",
        "repos": "Variable",
        "objectif": "Stimule fibres lentes et rapides",
        "difficulte": 3,
        "difficulty_level": 3,
        "programme_recommande": "Mixte",
        "notes": "Combinaison de zones de répétitions."
    },
    {
        "id": "pyramidale",
        "nom": "Pyramidale (ascendante / inversée)",
        "categorie": "MIXTE",
        "reps": "4–15 selon variante",
        "charge": "60–90% selon section",
        "repos": "60–180 s",
        "objectif": "Force + volume combinés",
        "difficulte": 3,
        "difficulty_level": 3,
        "programme_recommande": "Myofi",
        "notes": "Polyvalent; orientable selon charge."
    },
    {
        "id": "repetitions_partielles_forces_negatives",
        "nom": "Répétitions partielles / forcées / négatives",
        "categorie": "MIXTE",
        "reps": "1–6 + phase négative",
        "charge": "Lourde",
        "repos": "Court",
        "objectif": "Hypertrophie + tension excentrique",
        "difficulte": 2,
        "difficulty_level": 4,
        "programme_recommande": "Myofi",
        "notes": "Technique avancée; nécessite spotter."
    },
    {
        "id": "accentuated_eccentric",
        "nom": "Accentuated eccentric loading (AEL)",
        "categorie": "MIXTE",
        "reps": "Eccentrique 4–8 s ou +20–50% charge",
        "charge": "80–120% ecc",
        "repos": "Moyen",
        "objectif": "Dommages + hypertrophie excentrique",
        "difficulte": 2,
        "difficulty_level": 5,
        "programme_recommande": "Myofi",
        "notes": "Très exigeant; prudence sur récupération."
    },
    {
        "id": "rest_pause_mixed",
        "nom": "Rest-pause (mixte)",
        "categorie": "MIXTE",
        "reps": "8–12 + mini-pauses",
        "charge": "65–80%",
        "repos": "Très court",
        "objectif": "Volume densifié",
        "difficulte": 2,
        "difficulty_level": 3,
        "programme_recommande": "Sarco",
        "notes": "Peut être orienté volume ou tension."
    },

    # ---------------- MYOFIBRILLAIRE
    {
        "id": "low_rep_weighted",
        "nom": "Low-rep weighted sets",
        "categorie": "MYOFIBRILLAIRE",
        "reps": "3–6",
        "charge": "80–90%",
        "repos": "2–5 min",
        "objectif": "Force + fibres rapides",
        "difficulte": 2,
        "difficulty_level": 5,
        "programme_recommande": "Myofi",
        "notes": "Séries courtes lourdes."
    },
    {
        "id": "heavy_compounds",
        "nom": "Heavy compounds",
        "categorie": "MYOFIBRILLAIRE",
        "reps": "3–6",
        "charge": "75–90%",
        "repos": "2–5 min",
        "objectif": "Force + densité musculaire",
        "difficulte": 1,
        "difficulty_level": 5,
        "programme_recommande": "Myofi",
        "notes": "Mouvements composés lourds."
    },
    {
        "id": "wave_loading",
        "nom": "Wave loading",
        "categorie": "MYOFIBRILLAIRE",
        "reps": "Alternance 7-5-3",
        "charge": "75–95%+",
        "repos": "Long",
        "objectif": "Force progressive + adaptation nerveuse",
        "difficulte": 1,
        "difficulty_level": 5,
        "programme_recommande": "Myofi",
        "notes": "Progression cyclique des charges."
    },
    {
        "id": "cluster_sets",
        "nom": "Cluster sets",
        "categorie": "MYOFIBRILLAIRE",
        "reps": "3–6 × mini-reps",
        "charge": "75–90%",
        "repos": "Micro-pauses + long",
        "objectif": "Force + volume sous tension lourde",
        "difficulte": 1,
        "difficulty_level": 5,
        "programme_recommande": "Myofi",
        "notes": "Très difficile; micro-pauses."
    },
    {
        "id": "progressive_overload",
        "nom": "Progressive overload classique",
        "categorie": "MYOFIBRILLAIRE",
        "reps": "Selon plan",
        "charge": "Progressif",
        "repos": "Long",
        "objectif": "Force + hypertrophie durable",
        "difficulte": 1,
        "difficulty_level": 4,
        "programme_recommande": "Myofi",
        "notes": "Principe fondamental de progression."
    },
]

def get_all_techniques() -> List[Dict[str, Any]]:
    cat_order = {"SARCOPLASMIQUE": 0, "MIXTE": 1, "MYOFIBRILLAIRE": 2}
    return sorted(TECHNIQUES, key=lambda t: (cat_order.get(t["categorie"], 9), t.get("difficulte", 5)))

def get_techniques_for_program(program: str) -> List[Dict[str, Any]]:
    p = (program or "").strip().lower()
    if p == "myofi":
        return [t for t in get_all_techniques() if t["programme_recommande"].lower() == "myofi"]
    if p == "sarco":
        return [t for t in get_all_techniques() if t["programme_recommande"].lower() == "sarco"]
    return get_all_techniques()

def find_technique_by_id(tid: str) -> Dict[str, Any]:
    for t in TECHNIQUES:
        if t["id"] == tid:
            return t
    return None

def export_techniques_csv(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["id","nom","categorie","reps","charge","repos","objectif","difficulte","difficulty_level","programme_recommande","notes"])
        for t in get_all_techniques():
            writer.writerow([t["id"], t["nom"], t["categorie"], t["reps"], t["charge"], t["repos"], t["objectif"], t.get("difficulte"), t.get("difficulty_level"), t["programme_recommande"], t.get("notes","")])

def build_program_template(program: str, weeks: int = 4) -> Dict[str, Any]:
    """
    Construit un template simple de programme.
    """
    techniques = get_techniques_for_program(program)
    if (program or "").strip().lower() == "sarco":
        series = [t for t in techniques if t["id"] == "series_10_12_standard"]
        others = [t for t in techniques if t["id"] != "series_10_12_standard"]
        techniques = series + others
    sample = techniques[:6] if len(techniques) >= 6 else techniques
    program_template = {
        "programme": program,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "weeks": []
    }
    for w in range(1, weeks + 1):
        week = {"week": w, "sessions": []}
        for s in range(1, 4):
            session = {"session": s, "exercises": []}
            for i, t in enumerate(sample):
                if (i % 3) == (s - 1):
                    session["exercises"].append({
                        "id": t["id"],
                        "nom": t["nom"],
                        "reps": t["reps"],
                        "charge": t["charge"],
                        "notes": t.get("notes","")
                    })
            week["sessions"].append(session)
        program_template["weeks"].append(week)
    return program_template