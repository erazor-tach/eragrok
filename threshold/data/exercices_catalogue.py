# data/exercices_catalogue.py
# -*- coding: utf-8 -*-
"""
Catalogue des exercices de musculation.
Source : https://www.docteur-fitness.com/exercice-musculation (+450 exercices)

Structure par groupe musculaire + métadonnées équipement.
Utilisé par l'onglet Exercices de EntrainementView.
"""
from __future__ import annotations
from typing import List, Dict, Any

# ── Labels et visuels des catégories ─────────────────────────────────────────
CAT_LABELS: Dict[str, str] = {
    "PECS":       "Pectoraux",
    "DOS":        "Dos",
    "EPAULES":    "Épaules",
    "BICEPS":     "Biceps",
    "TRICEPS":    "Triceps",
    "ABDOS":      "Abdominaux",
    "QUADRICEPS": "Quadriceps",
    "FESSIERS":   "Fessiers",
    "ISCHIO":     "Ischio-jambiers",
    "MOLLETS":    "Mollets",
    "FULL_BODY":  "Full body",
}

CAT_ICONS: Dict[str, str] = {
    "PECS":       "🏋️",
    "DOS":        "🔙",
    "EPAULES":    "🔝",
    "BICEPS":     "💪",
    "TRICEPS":    "💪",
    "ABDOS":      "🎯",
    "QUADRICEPS": "🦵",
    "FESSIERS":   "🍑",
    "ISCHIO":     "🦵",
    "MOLLETS":    "🦶",
    "FULL_BODY":  "⭐",
}

CAT_ORDER: Dict[str, int] = {
    "PECS": 0, "DOS": 1, "EPAULES": 2, "BICEPS": 3, "TRICEPS": 4,
    "ABDOS": 5, "QUADRICEPS": 6, "FESSIERS": 7, "ISCHIO": 8,
    "MOLLETS": 9, "FULL_BODY": 10,
}

# Niveaux de difficulté
DIFF_LABELS = {1: "Débutant", 2: "Facile", 3: "Intermédiaire", 4: "Avancé", 5: "Expert"}

EXERCICES: List[Dict[str, Any]] = [
    # ══════════════════════════════════════════════════════════════════════
    #  PECTORAUX — 42 exercices (docteur-fitness.com/exercices-pectoraux)
    # ══════════════════════════════════════════════════════════════════════
    {"id":"developpe_couche_barre","nom":"Développé couché barre","cat":"PECS","equipement":"Barre","difficulte":3,"reps":"6–12","muscles_secondaires":"Triceps, Épaules ant.","notes":"Exercice roi pecs. Prise légèrement au-delà des épaules."},
    {"id":"developpe_incline_barre","nom":"Développé incliné barre","cat":"PECS","equipement":"Barre","difficulte":3,"reps":"8–12","muscles_secondaires":"Triceps, Deltoïdes","notes":"Banc 30–45°. Pectoraux supérieurs."},
    {"id":"developpe_decline_barre","nom":"Développé décliné barre","cat":"PECS","equipement":"Barre","difficulte":3,"reps":"8–12","muscles_secondaires":"Triceps","notes":"Banc décliné. Bas des pectoraux."},
    {"id":"developpe_couche_halteres","nom":"Développé couché haltères","cat":"PECS","equipement":"Haltères","difficulte":3,"reps":"8–15","muscles_secondaires":"Triceps, Épaules ant.","notes":"Amplitude supérieure vs barre. Étirement en bas."},
    {"id":"developpe_incline_halteres","nom":"Développé incliné haltères","cat":"PECS","equipement":"Haltères","difficulte":3,"reps":"10–15","muscles_secondaires":"Triceps, Deltoïdes","notes":"Pecs supérieurs, étirement optimal."},
    {"id":"ecarte_couche_halteres","nom":"Écarté couché haltères","cat":"PECS","equipement":"Haltères","difficulte":2,"reps":"12–15","muscles_secondaires":"Épaules ant.","notes":"Coudes légèrement fléchis, arc ample. Finition."},
    {"id":"ecarte_incline_halteres","nom":"Écarté incliné haltères","cat":"PECS","equipement":"Haltères","difficulte":2,"reps":"12–15","muscles_secondaires":"Épaules ant.","notes":"Isole le faisceau claviculaire."},
    {"id":"pompe","nom":"Pompe (push-up)","cat":"PECS","equipement":"Poids de corps","difficulte":1,"reps":"10–30","muscles_secondaires":"Triceps, Épaules","notes":"Base calisthenics. Variantes : large, serrée, archer."},
    {"id":"pompe_inclinee","nom":"Pompe inclinée","cat":"PECS","equipement":"Poids de corps","difficulte":2,"reps":"10–20","muscles_secondaires":"Triceps","notes":"Pieds surélevés. Accentue les pecs supérieurs."},
    {"id":"pompe_declinee","nom":"Pompe déclinée","cat":"PECS","equipement":"Poids de corps","difficulte":2,"reps":"10–20","muscles_secondaires":"Triceps","notes":"Mains surélevées. Accentue les pecs inférieurs."},
    {"id":"dips_pecs","nom":"Dips version pectoraux","cat":"PECS","equipement":"Poids de corps","difficulte":3,"reps":"8–15","muscles_secondaires":"Triceps, Épaules","notes":"Corps penché en avant pour cibler les pecs."},
    {"id":"cable_crossover","nom":"Croisé poulie (cable crossover)","cat":"PECS","equipement":"Poulie","difficulte":2,"reps":"12–15","muscles_secondaires":"Épaules ant.","notes":"Poulies hautes. Contraction max en fin."},
    {"id":"ecarte_poulie_basse","nom":"Écarté poulie basse","cat":"PECS","equipement":"Poulie","difficulte":2,"reps":"12–15","muscles_secondaires":"Épaules ant.","notes":"Mouvement vers le haut. Pecs supérieurs."},
    {"id":"peck_deck","nom":"Peck-deck (butterfly machine)","cat":"PECS","equipement":"Machine","difficulte":1,"reps":"12–15","muscles_secondaires":"Épaules ant.","notes":"Isolation, idéale débutants et finition."},
    {"id":"developpe_couche_machine","nom":"Développé couché machine","cat":"PECS","equipement":"Machine","difficulte":1,"reps":"10–15","muscles_secondaires":"Triceps, Épaules","notes":"Machine convergente guidée. Sécurisé."},
    {"id":"developpe_incline_machine","nom":"Développé incliné machine","cat":"PECS","equipement":"Machine","difficulte":1,"reps":"10–15","muscles_secondaires":"Triceps","notes":"Version inclinée guidée."},
    {"id":"pullover_haltere","nom":"Pull-over haltère","cat":"PECS","equipement":"Haltères","difficulte":2,"reps":"12–15","muscles_secondaires":"Grand dorsal, Dentelé","notes":"Expansion cage thoracique. Travaille aussi le dos."},
    {"id":"pullover_poulie","nom":"Pull-over poulie","cat":"PECS","equipement":"Poulie","difficulte":2,"reps":"12–15","muscles_secondaires":"Grand dorsal","notes":"Poulie haute, tension constante."},
    {"id":"developpe_couche_smith","nom":"Développé couché Smith machine","cat":"PECS","equipement":"Smith","difficulte":2,"reps":"8–15","muscles_secondaires":"Triceps, Épaules","notes":"Guidé, mouvement rectiligne."},
    {"id":"developpe_incline_smith","nom":"Développé incliné Smith machine","cat":"PECS","equipement":"Smith","difficulte":2,"reps":"10–15","muscles_secondaires":"Triceps","notes":"Pecs supérieurs, guidé."},
    {"id":"landmine_press_pecs","nom":"Landmine press unilatéral","cat":"PECS","equipement":"Landmine","difficulte":3,"reps":"10–15","muscles_secondaires":"Épaules, Core","notes":"Pecs supérieurs + stabilité."},
    {"id":"pompe_archer","nom":"Pompe archer","cat":"PECS","equipement":"Poids de corps","difficulte":4,"reps":"5–10 par côté","muscles_secondaires":"Triceps","notes":"Progression vers la pompe à une main."},
    {"id":"pompe_diamant","nom":"Pompe diamant","cat":"PECS","equipement":"Poids de corps","difficulte":3,"reps":"10–20","muscles_secondaires":"Triceps","notes":"Mains en triangle sous le sternum. Pecs internes + triceps."},
    {"id":"chest_press_elastique","nom":"Développé couché élastique","cat":"PECS","equipement":"Élastique","difficulte":2,"reps":"12–20","muscles_secondaires":"Triceps","notes":"Résistance variable. Excellent à domicile."},

    # ══════════════════════════════════════════════════════════════════════
    #  DOS — 57 exercices (docteur-fitness.com/exercices-dos)
    # ══════════════════════════════════════════════════════════════════════
    {"id":"traction","nom":"Traction (pull-up)","cat":"DOS","equipement":"Poids de corps","difficulte":4,"reps":"5–15","muscles_secondaires":"Biceps, Rhomboïdes, Trapèze","notes":"Prise pronation. Exercice roi du dos."},
    {"id":"chin_up","nom":"Chin-up (supination)","cat":"DOS","equipement":"Poids de corps","difficulte":3,"reps":"6–15","muscles_secondaires":"Biceps, Trapèze inf.","notes":"Prise supination, plus de biceps."},
    {"id":"traction_prise_serree","nom":"Traction prise serrée","cat":"DOS","equipement":"Poids de corps","difficulte":3,"reps":"6–15","muscles_secondaires":"Biceps, Grand rond","notes":"Prise neutre ou supination. Épaisseur centre."},
    {"id":"traction_australienne","nom":"Traction australienne (inverted row)","cat":"DOS","equipement":"Poids de corps","difficulte":2,"reps":"10–20","muscles_secondaires":"Biceps, Rhomboïdes","notes":"Corps incliné sous une barre. Progressif vers tractions."},
    {"id":"souleve_de_terre","nom":"Soulevé de terre (deadlift)","cat":"DOS","equipement":"Barre","difficulte":5,"reps":"3–8","muscles_secondaires":"Quadriceps, Fessiers, Trapèze, Ischio","notes":"Mouvement fondamental. Technique irréprochable requise."},
    {"id":"souleve_sumo","nom":"Soulevé de terre sumo","cat":"DOS","equipement":"Barre","difficulte":4,"reps":"3–8","muscles_secondaires":"Adducteurs, Fessiers, Quadriceps","notes":"Pieds très écartés. Plus de fessiers/adducteurs."},
    {"id":"romanian_deadlift","nom":"Romanian deadlift (RDL)","cat":"DOS","equipement":"Barre","difficulte":3,"reps":"8–12","muscles_secondaires":"Fessiers, Érecteurs","notes":"Jambes quasi tendues. Dos plat, descente contrôlée."},
    {"id":"rowing_barre_pronation","nom":"Rowing barre pronation","cat":"DOS","equipement":"Barre","difficulte":3,"reps":"6–12","muscles_secondaires":"Biceps, Rhomboïdes, Trapèze","notes":"Buste 45°, tirer vers le nombril. Dos plat."},
    {"id":"rowing_barre_supination","nom":"Rowing barre supination","cat":"DOS","equipement":"Barre","difficulte":3,"reps":"8–12","muscles_secondaires":"Biceps","notes":"Prise sous-main. Meilleure activation grand dorsal."},
    {"id":"rowing_haltere_unilateral","nom":"Rowing haltère unilatéral","cat":"DOS","equipement":"Haltères","difficulte":2,"reps":"10–15","muscles_secondaires":"Biceps, Rhomboïdes","notes":"Appui sur banc, coude vers le plafond. Amplitude max."},
    {"id":"tirage_vertical","nom":"Tirage vertical poulie haute","cat":"DOS","equipement":"Poulie","difficulte":2,"reps":"10–15","muscles_secondaires":"Biceps, Rhomboïdes","notes":"Tirer vers le menton/poitrine. Coudes bas."},
    {"id":"tirage_vertical_prise_serree","nom":"Tirage vertical prise serrée","cat":"DOS","equipement":"Poulie","difficulte":2,"reps":"10–15","muscles_secondaires":"Biceps, Grand rond","notes":"Prise neutre ou supination. Centre du dos."},
    {"id":"tirage_vertical_prise_large","nom":"Tirage vertical prise large","cat":"DOS","equipement":"Poulie","difficulte":2,"reps":"10–15","muscles_secondaires":"Biceps","notes":"Prise très large. Largeur grand dorsal."},
    {"id":"rowing_poulie_basse","nom":"Rowing poulie basse","cat":"DOS","equipement":"Poulie","difficulte":2,"reps":"10–15","muscles_secondaires":"Biceps, Érecteurs","notes":"Prise neutre, tirer vers le ventre. Buste droit."},
    {"id":"pullover_dos","nom":"Pull-over poulie / haltère (dos)","cat":"DOS","equipement":"Poulie","difficulte":2,"reps":"12–15","muscles_secondaires":"Pecs, Dentelé","notes":"Isole le grand dorsal en extension."},
    {"id":"shrug_barre","nom":"Shrug barre","cat":"DOS","equipement":"Barre","difficulte":2,"reps":"12–15","muscles_secondaires":"Élévateur scapulae","notes":"Haussements d'épaules. Mouvement vertical pur."},
    {"id":"shrug_halteres","nom":"Shrug haltères","cat":"DOS","equipement":"Haltères","difficulte":2,"reps":"12–15","muscles_secondaires":"Élévateur scapulae","notes":"Plus d'amplitude qu'avec la barre."},
    {"id":"rack_pull","nom":"Rack pull","cat":"DOS","equipement":"Barre","difficulte":4,"reps":"3–6","muscles_secondaires":"Fessiers, Ischio","notes":"Soulevé partiel depuis le rack. Phase finale."},
    {"id":"good_morning","nom":"Good morning","cat":"DOS","equipement":"Barre","difficulte":4,"reps":"10–15","muscles_secondaires":"Fessiers, Ischio","notes":"Inclinaison du buste en avant. Technique précise."},
    {"id":"hyperextension","nom":"Hyperextension (roman chair)","cat":"DOS","equipement":"Machine","difficulte":2,"reps":"12–20","muscles_secondaires":"Fessiers, Ischio","notes":"Érecteurs du rachis. Ne pas hyperétendre."},
    {"id":"rowing_machine","nom":"Rowing machine","cat":"DOS","equipement":"Machine","difficulte":1,"reps":"10–15","muscles_secondaires":"Biceps","notes":"Guidé. Idéal débutants et isolation."},
    {"id":"rowing_landmine","nom":"Rowing landmine (Meadows row)","cat":"DOS","equipement":"Landmine","difficulte":3,"reps":"10–12","muscles_secondaires":"Biceps, Core","notes":"Unilatéral, angle unique. Très efficace."},
    {"id":"rowing_smith","nom":"Rowing Smith machine","cat":"DOS","equipement":"Smith","difficulte":2,"reps":"8–12","muscles_secondaires":"Biceps, Rhomboïdes","notes":"Guidé. Buste incliné vers l'avant."},
    {"id":"face_pull","nom":"Face pull","cat":"DOS","equipement":"Poulie","difficulte":2,"reps":"15–20","muscles_secondaires":"Deltoïdes post., Trapèze","notes":"Santé épaules + deltoïdes postérieurs."},

    # ══════════════════════════════════════════════════════════════════════
    #  ÉPAULES
    # ══════════════════════════════════════════════════════════════════════
    {"id":"developpe_militaire_barre","nom":"Développé militaire barre","cat":"EPAULES","equipement":"Barre","difficulte":4,"reps":"6–12","muscles_secondaires":"Triceps, Trapèze","notes":"Fondamental épaules. Debout ou assis."},
    {"id":"developpe_militaire_halteres","nom":"Développé militaire haltères","cat":"EPAULES","equipement":"Haltères","difficulte":3,"reps":"8–15","muscles_secondaires":"Triceps","notes":"Meilleure amplitude. Prise neutre ou pronation."},
    {"id":"elevations_laterales","nom":"Élévations latérales haltères","cat":"EPAULES","equipement":"Haltères","difficulte":2,"reps":"12–20","muscles_secondaires":"Trapèze","notes":"Deltoïdes latéraux. Monter au niveau des épaules."},
    {"id":"elevations_laterales_poulie","nom":"Élévations latérales poulie","cat":"EPAULES","equipement":"Poulie","difficulte":2,"reps":"15–20","muscles_secondaires":"Trapèze","notes":"Tension constante vs haltères."},
    {"id":"elevations_laterales_elastique","nom":"Élévations latérales élastique","cat":"EPAULES","equipement":"Élastique","difficulte":1,"reps":"15–20","muscles_secondaires":"Trapèze","notes":"À domicile. Résistance progressive."},
    {"id":"oiseau_halteres","nom":"Oiseau (écarté buste penché)","cat":"EPAULES","equipement":"Haltères","difficulte":2,"reps":"12–20","muscles_secondaires":"Rhomboïdes, Trapèze","notes":"Deltoïdes postérieurs. Buste parallèle au sol."},
    {"id":"oiseau_poulie","nom":"Oiseau poulie","cat":"EPAULES","equipement":"Poulie","difficulte":2,"reps":"15–20","muscles_secondaires":"Rhomboïdes","notes":"Poulies hautes croisées. Tension constante."},
    {"id":"front_raise","nom":"Élévations frontales haltères","cat":"EPAULES","equipement":"Haltères","difficulte":2,"reps":"12–15","muscles_secondaires":"Pecs sup.","notes":"Deltoïdes antérieurs. Jusqu'au niveau des épaules."},
    {"id":"front_raise_barre","nom":"Élévations frontales barre","cat":"EPAULES","equipement":"Barre","difficulte":2,"reps":"12–15","muscles_secondaires":"Pecs sup.","notes":"Mouvement bilatéral."},
    {"id":"upright_row","nom":"Rowing menton (upright row)","cat":"EPAULES","equipement":"Barre","difficulte":3,"reps":"10–15","muscles_secondaires":"Trapèze, Biceps","notes":"Barre tirée vers le menton. Attention impingement."},
    {"id":"upright_row_halteres","nom":"Rowing menton haltères","cat":"EPAULES","equipement":"Haltères","difficulte":3,"reps":"10–15","muscles_secondaires":"Trapèze","notes":"Moins de risque qu'avec la barre."},
    {"id":"presse_epaules_machine","nom":"Presse à épaules machine","cat":"EPAULES","equipement":"Machine","difficulte":1,"reps":"10–15","muscles_secondaires":"Triceps","notes":"Guidée. Idéal débutants, sécurisé."},
    {"id":"developpe_militaire_smith","nom":"Développé militaire Smith machine","cat":"EPAULES","equipement":"Smith","difficulte":2,"reps":"10–15","muscles_secondaires":"Triceps","notes":"Guidé. Mouvement rectiligne imposé."},
    {"id":"arnold_press","nom":"Arnold press","cat":"EPAULES","equipement":"Haltères","difficulte":3,"reps":"10–15","muscles_secondaires":"Triceps, Tous deltoïdes","notes":"Rotation en cours de mouvement. Travaille les 3 faisceaux."},
    {"id":"lateral_raise_machine","nom":"Élévations latérales machine","cat":"EPAULES","equipement":"Machine","difficulte":1,"reps":"12–20","muscles_secondaires":"","notes":"Isolation deltoïdes latéraux. Guidée."},

    # ══════════════════════════════════════════════════════════════════════
    #  BICEPS
    # ══════════════════════════════════════════════════════════════════════
    {"id":"curl_barre","nom":"Curl barre droit","cat":"BICEPS","equipement":"Barre","difficulte":2,"reps":"8–12","muscles_secondaires":"Brachio-radial, Brachial ant.","notes":"Barre droite ou EZ. Coudes collés au corps."},
    {"id":"curl_barre_ez","nom":"Curl barre EZ","cat":"BICEPS","equipement":"Barre","difficulte":2,"reps":"8–12","muscles_secondaires":"Brachial ant.","notes":"Barre EZ, plus confortable pour les poignets."},
    {"id":"curl_haltere_alterne","nom":"Curl haltère alterné","cat":"BICEPS","equipement":"Haltères","difficulte":2,"reps":"10–15","muscles_secondaires":"Brachial ant.","notes":"Supination en cours de mouvement pour le pic."},
    {"id":"curl_marteau","nom":"Curl marteau (hammer curl)","cat":"BICEPS","equipement":"Haltères","difficulte":2,"reps":"10–15","muscles_secondaires":"Biceps","notes":"Prise neutre. Épaisseur bras et avant-bras."},
    {"id":"curl_incline_halteres","nom":"Curl incliné haltères","cat":"BICEPS","equipement":"Haltères","difficulte":2,"reps":"10–15","muscles_secondaires":"Brachial ant.","notes":"Banc 60°. Étirement complet du biceps."},
    {"id":"curl_concentre","nom":"Curl concentré","cat":"BICEPS","equipement":"Haltères","difficulte":2,"reps":"12–15","muscles_secondaires":"","notes":"Coude sur la cuisse. Pic du biceps, isolation max."},
    {"id":"curl_poulie_basse","nom":"Curl poulie basse","cat":"BICEPS","equipement":"Poulie","difficulte":2,"reps":"12–15","muscles_secondaires":"Brachial ant.","notes":"Tension constante. Excellent finition."},
    {"id":"curl_poulie_haute","nom":"Curl poulie haute (cable curl)","cat":"BICEPS","equipement":"Poulie","difficulte":2,"reps":"12–15","muscles_secondaires":"","notes":"Tension en position raccourcie."},
    {"id":"curl_prise_large","nom":"Curl prise large (wide grip)","cat":"BICEPS","equipement":"Barre","difficulte":2,"reps":"10–12","muscles_secondaires":"","notes":"Prise large. Chef court du biceps."},
    {"id":"preacher_curl","nom":"Preacher curl (banc Larry Scott)","cat":"BICEPS","equipement":"Barre","difficulte":2,"reps":"10–12","muscles_secondaires":"","notes":"Coudes fixés sur le banc. Isolation totale."},
    {"id":"curl_elastique","nom":"Curl élastique","cat":"BICEPS","equipement":"Élastique","difficulte":1,"reps":"15–20","muscles_secondaires":"","notes":"À domicile. Résistance variable."},
    {"id":"chin_up_biceps","nom":"Traction prise supination (biceps)","cat":"BICEPS","equipement":"Poids de corps","difficulte":4,"reps":"6–15","muscles_secondaires":"Grand dorsal","notes":"Mouvement polyarticulaire. Force biceps + dos."},

    # ══════════════════════════════════════════════════════════════════════
    #  TRICEPS
    # ══════════════════════════════════════════════════════════════════════
    {"id":"dips_triceps","nom":"Dips (version triceps)","cat":"TRICEPS","equipement":"Poids de corps","difficulte":3,"reps":"8–15","muscles_secondaires":"Pecs, Épaules","notes":"Corps vertical. Barres parallèles."},
    {"id":"extension_triceps_poulie","nom":"Extension triceps poulie haute (corde)","cat":"TRICEPS","equipement":"Poulie","difficulte":1,"reps":"12–15","muscles_secondaires":"","notes":"Avec corde ou barre droite. Coudes fixes."},
    {"id":"extension_triceps_poulie_barre","nom":"Extension triceps poulie haute (barre)","cat":"TRICEPS","equipement":"Poulie","difficulte":1,"reps":"12–15","muscles_secondaires":"","notes":"Barre droite ou EZ. Contraction maximale en bas."},
    {"id":"skullcrusher","nom":"Skullcrusher (extension couché)","cat":"TRICEPS","equipement":"Barre","difficulte":3,"reps":"10–15","muscles_secondaires":"","notes":"Barre EZ recommandée. Chef long triceps."},
    {"id":"skullcrusher_halteres","nom":"Skullcrusher haltères","cat":"TRICEPS","equipement":"Haltères","difficulte":3,"reps":"10–15","muscles_secondaires":"","notes":"Plus d'amplitude qu'avec la barre."},
    {"id":"developpe_prise_serree","nom":"Développé couché prise serrée","cat":"TRICEPS","equipement":"Barre","difficulte":3,"reps":"6–12","muscles_secondaires":"Pecs, Épaules","notes":"Prise étroite (largeur épaules). Force + masse."},
    {"id":"overhead_extension_haltere","nom":"Extension overhead haltère","cat":"TRICEPS","equipement":"Haltères","difficulte":2,"reps":"12–15","muscles_secondaires":"","notes":"Bras au-dessus de la tête, descendre derrière la nuque."},
    {"id":"overhead_extension_poulie","nom":"Extension overhead poulie","cat":"TRICEPS","equipement":"Poulie","difficulte":2,"reps":"12–15","muscles_secondaires":"","notes":"Poulie basse, tension au point d'étirement."},
    {"id":"kickback_triceps","nom":"Kickback triceps haltère","cat":"TRICEPS","equipement":"Haltères","difficulte":2,"reps":"12–15","muscles_secondaires":"","notes":"Buste penché, coude fixe, extension vers l'arrière."},
    {"id":"kickback_poulie","nom":"Kickback triceps poulie","cat":"TRICEPS","equipement":"Poulie","difficulte":2,"reps":"12–15","muscles_secondaires":"","notes":"Tension constante. Version poulie du kickback."},
    {"id":"dips_banc","nom":"Dips au banc","cat":"TRICEPS","equipement":"Poids de corps","difficulte":2,"reps":"12–20","muscles_secondaires":"Épaules","notes":"Mains sur le banc, pieds au sol. Débutants."},
    {"id":"triceps_barre_front","nom":"Extension front barre","cat":"TRICEPS","equipement":"Barre","difficulte":2,"reps":"10–15","muscles_secondaires":"","notes":"Barre EZ vers le front. Coudes fixes."},
    {"id":"developpe_smith_prise_serree","nom":"Développé Smith prise serrée","cat":"TRICEPS","equipement":"Smith","difficulte":2,"reps":"10–15","muscles_secondaires":"Pecs","notes":"Guidé, sécurisé."},
    {"id":"extension_triceps_elastique","nom":"Extension triceps élastique","cat":"TRICEPS","equipement":"Élastique","difficulte":1,"reps":"15–20","muscles_secondaires":"","notes":"À domicile. Résistance progressive."},

    # ══════════════════════════════════════════════════════════════════════
    #  ABDOMINAUX
    # ══════════════════════════════════════════════════════════════════════
    {"id":"crunch","nom":"Crunch au sol","cat":"ABDOS","equipement":"Poids de corps","difficulte":1,"reps":"15–25","muscles_secondaires":"Transverse","notes":"Montée partielle. Pas de traction sur la nuque."},
    {"id":"crunch_incline","nom":"Crunch incliné (banc)","cat":"ABDOS","equipement":"Poids de corps","difficulte":2,"reps":"15–20","muscles_secondaires":"","notes":"Plus d'amplitude et de résistance."},
    {"id":"planche","nom":"Planche (gainage)","cat":"ABDOS","equipement":"Poids de corps","difficulte":2,"reps":"30–120 s","muscles_secondaires":"Érecteurs, Fessiers","notes":"Corps aligné. Ne pas laisser les hanches tomber."},
    {"id":"planche_laterale","nom":"Planche latérale","cat":"ABDOS","equipement":"Poids de corps","difficulte":3,"reps":"30–60 s","muscles_secondaires":"Obliques ext.","notes":"Obliques. Corps aligné de côté."},
    {"id":"releve_jambes_suspendu","nom":"Relevé de jambes suspendu","cat":"ABDOS","equipement":"Poids de corps","difficulte":3,"reps":"10–20","muscles_secondaires":"Psoas, Iliaque","notes":"Suspendu à barre. Variante genoux fléchis."},
    {"id":"releve_jambes_sol","nom":"Relevé de jambes au sol","cat":"ABDOS","equipement":"Poids de corps","difficulte":2,"reps":"12–20","muscles_secondaires":"Psoas","notes":"Allongé, jambes tendues ou fléchies."},
    {"id":"russian_twist","nom":"Russian twist","cat":"ABDOS","equipement":"Poids de corps","difficulte":2,"reps":"20–30","muscles_secondaires":"Obliques, Transverse","notes":"Pieds décollés pour plus de difficulté."},
    {"id":"russian_twist_med","nom":"Russian twist medecine-ball","cat":"ABDOS","equipement":"Machine","difficulte":3,"reps":"20–30","muscles_secondaires":"Obliques","notes":"Charge additionnelle pour les obliques."},
    {"id":"ab_wheel","nom":"Rouleau abdominal (ab wheel)","cat":"ABDOS","equipement":"Poids de corps","difficulte":4,"reps":"8–15","muscles_secondaires":"Grand dorsal, Épaules","notes":"Extension lente, retour contrôlé. Très exigeant."},
    {"id":"crunch_poulie","nom":"Crunch poulie haute","cat":"ABDOS","equipement":"Poulie","difficulte":2,"reps":"15–20","muscles_secondaires":"","notes":"À genoux, corde derrière la tête. Contraction vers les genoux."},
    {"id":"decline_crunch","nom":"Crunch décliné","cat":"ABDOS","equipement":"Machine","difficulte":3,"reps":"15–20","muscles_secondaires":"","notes":"Banc décliné. Plus difficile grâce à la gravité."},
    {"id":"mountain_climber","nom":"Mountain climber","cat":"ABDOS","equipement":"Poids de corps","difficulte":3,"reps":"20–30 s","muscles_secondaires":"Épaules, Fléchisseurs de hanche","notes":"Cardio-abdos. Genoux vers la poitrine en alternance."},
    {"id":"dragon_flag","nom":"Dragon flag","cat":"ABDOS","equipement":"Poids de corps","difficulte":5,"reps":"5–10","muscles_secondaires":"Érecteurs, Core complet","notes":"Technique avancée de Bruce Lee. Corps rigide."},

    # ══════════════════════════════════════════════════════════════════════
    #  QUADRICEPS
    # ══════════════════════════════════════════════════════════════════════
    {"id":"squat_barre","nom":"Squat barre (back squat)","cat":"QUADRICEPS","equipement":"Barre","difficulte":4,"reps":"5–12","muscles_secondaires":"Fessiers, Ischio, Érecteurs","notes":"Roi des exercices. Cuisses parallèles ou en dessous."},
    {"id":"squat_halteres","nom":"Squat haltères","cat":"QUADRICEPS","equipement":"Haltères","difficulte":3,"reps":"10–15","muscles_secondaires":"Fessiers, Ischio","notes":"Accessible. Idéal à domicile."},
    {"id":"front_squat","nom":"Front squat (squat avant)","cat":"QUADRICEPS","equipement":"Barre","difficulte":5,"reps":"6–10","muscles_secondaires":"Fessiers, Core","notes":"Barre devant les épaules. Exige forte mobilité."},
    {"id":"leg_press","nom":"Leg press (presse à cuisse)","cat":"QUADRICEPS","equipement":"Machine","difficulte":2,"reps":"10–20","muscles_secondaires":"Fessiers, Ischio","notes":"Pieds hauts = fessiers. Pieds bas = quadriceps."},
    {"id":"hack_squat","nom":"Hack squat machine","cat":"QUADRICEPS","equipement":"Machine","difficulte":3,"reps":"10–15","muscles_secondaires":"Fessiers","notes":"Pieds écartés ou serrés pour cibler différentes zones."},
    {"id":"hack_squat_inverse","nom":"Hack squat inversé","cat":"QUADRICEPS","equipement":"Machine","difficulte":3,"reps":"10–15","muscles_secondaires":"Fessiers","notes":"Face contre la machine. Quad supérieur, VMO."},
    {"id":"leg_extension","nom":"Leg extension","cat":"QUADRICEPS","equipement":"Machine","difficulte":1,"reps":"12–20","muscles_secondaires":"","notes":"Isolation pure des quadriceps. Finition."},
    {"id":"fente_avant","nom":"Fente avant (lunges)","cat":"QUADRICEPS","equipement":"Poids de corps","difficulte":2,"reps":"10–15/jambe","muscles_secondaires":"Fessiers, Ischio","notes":"Genou à 90°, ne pas dépasser l'orteil."},
    {"id":"fente_marche","nom":"Fente marchée","cat":"QUADRICEPS","equipement":"Poids de corps","difficulte":3,"reps":"10–15/jambe","muscles_secondaires":"Fessiers, Équilibre","notes":"Progression dynamique des fentes."},
    {"id":"fente_bulgare","nom":"Fente bulgare (split squat)","cat":"QUADRICEPS","equipement":"Poids de corps","difficulte":4,"reps":"10–15/jambe","muscles_secondaires":"Fessiers, Ischio","notes":"Pied arrière sur banc. Excellent pour déséquilibres."},
    {"id":"squat_gobelet","nom":"Squat gobelet (goblet squat)","cat":"QUADRICEPS","equipement":"Kettlebell","difficulte":2,"reps":"12–15","muscles_secondaires":"Fessiers, Core","notes":"Kettlebell tenu devant soi. Bonne posture."},
    {"id":"squat_smith","nom":"Squat Smith machine","cat":"QUADRICEPS","equipement":"Smith","difficulte":2,"reps":"10–15","muscles_secondaires":"Fessiers","notes":"Guidé. Sécurisé pour débutants."},
    {"id":"squat_pistol","nom":"Squat pistol (unipodal)","cat":"QUADRICEPS","equipement":"Poids de corps","difficulte":5,"reps":"5–10/jambe","muscles_secondaires":"Fessiers, Core","notes":"Squat complet une jambe. Requiert mobilité."},
    {"id":"sissy_squat","nom":"Sissy squat","cat":"QUADRICEPS","equipement":"Poids de corps","difficulte":4,"reps":"10–15","muscles_secondaires":"","notes":"Isolation extreme des quads. Genou en avant."},

    # ══════════════════════════════════════════════════════════════════════
    #  FESSIERS
    # ══════════════════════════════════════════════════════════════════════
    {"id":"hip_thrust","nom":"Hip thrust barre","cat":"FESSIERS","equipement":"Barre","difficulte":3,"reps":"8–20","muscles_secondaires":"Ischio, Quadriceps","notes":"Dos sur banc, poussée des hanches. Contraction en haut."},
    {"id":"hip_thrust_machine","nom":"Hip thrust machine","cat":"FESSIERS","equipement":"Machine","difficulte":1,"reps":"12–20","muscles_secondaires":"Ischio","notes":"Version guidée du hip thrust."},
    {"id":"hip_thrust_elastique","nom":"Hip thrust élastique","cat":"FESSIERS","equipement":"Élastique","difficulte":2,"reps":"15–20","muscles_secondaires":"Ischio","notes":"À domicile. Résistance variable."},
    {"id":"squat_sumo","nom":"Squat sumo","cat":"FESSIERS","equipement":"Barre","difficulte":3,"reps":"10–15","muscles_secondaires":"Adducteurs, Quadriceps","notes":"Pieds très écartés, pointes à 45°."},
    {"id":"kickback_fessiers","nom":"Kickback fessiers (quadrupédie)","cat":"FESSIERS","equipement":"Poids de corps","difficulte":1,"reps":"15–20/jambe","muscles_secondaires":"","notes":"À 4 pattes, extension jambe arrière. Simple."},
    {"id":"abduction_machine","nom":"Abduction machine","cat":"FESSIERS","equipement":"Machine","difficulte":1,"reps":"15–25","muscles_secondaires":"Tenseur du fascia lata","notes":"Isolation fessiers moyens et petits."},
    {"id":"reverse_hyperextension","nom":"Reverse hyperextension","cat":"FESSIERS","equipement":"Machine","difficulte":2,"reps":"15–20","muscles_secondaires":"Ischio, Érecteurs","notes":"Extension jambes vers l'arrière en position allongée."},
    {"id":"souleve_terre_roumain","nom":"Soulevé de terre roumain","cat":"FESSIERS","equipement":"Barre","difficulte":3,"reps":"10–15","muscles_secondaires":"Ischio, Érecteurs","notes":"Charnière de hanche. Étirement max des fessiers."},
    {"id":"step_up","nom":"Step-up","cat":"FESSIERS","equipement":"Poids de corps","difficulte":2,"reps":"12–15/jambe","muscles_secondaires":"Quadriceps, Ischio","notes":"Monter sur un banc ou boîte. Unilatéral."},
    {"id":"pont_fessiers","nom":"Pont fessiers (glute bridge)","cat":"FESSIERS","equipement":"Poids de corps","difficulte":1,"reps":"15–20","muscles_secondaires":"Ischio","notes":"Version au sol du hip thrust. Débutants."},

    # ══════════════════════════════════════════════════════════════════════
    #  ISCHIO-JAMBIERS
    # ══════════════════════════════════════════════════════════════════════
    {"id":"leg_curl_couche","nom":"Leg curl couché machine","cat":"ISCHIO","equipement":"Machine","difficulte":1,"reps":"10–15","muscles_secondaires":"Mollets","notes":"Isolation ischio-jambiers. Descente contrôlée."},
    {"id":"leg_curl_assis","nom":"Leg curl assis machine","cat":"ISCHIO","equipement":"Machine","difficulte":1,"reps":"10–15","muscles_secondaires":"","notes":"Angle différent du couché. Chef long."},
    {"id":"leg_curl_debout","nom":"Leg curl debout machine","cat":"ISCHIO","equipement":"Machine","difficulte":2,"reps":"12–15/jambe","muscles_secondaires":"","notes":"Unilatéral. Meilleur recrutement."},
    {"id":"rdl","nom":"Romanian deadlift (RDL)","cat":"ISCHIO","equipement":"Barre","difficulte":3,"reps":"8–12","muscles_secondaires":"Fessiers, Érecteurs","notes":"Jambes quasi tendues. Étirement maximum."},
    {"id":"rdl_halteres","nom":"RDL haltères","cat":"ISCHIO","equipement":"Haltères","difficulte":3,"reps":"10–15","muscles_secondaires":"Fessiers","notes":"Plus d'amplitude qu'avec la barre."},
    {"id":"rdl_unilateral","nom":"RDL unilatéral","cat":"ISCHIO","equipement":"Haltères","difficulte":4,"reps":"10–12/jambe","muscles_secondaires":"Fessiers, Core","notes":"Balance et force unilatérale."},
    {"id":"good_morning_ischio","nom":"Good morning","cat":"ISCHIO","equipement":"Barre","difficulte":4,"reps":"10–15","muscles_secondaires":"Érecteurs, Fessiers","notes":"Barre sur le dos, inclinaison vers l'avant."},
    {"id":"glute_ham_raise","nom":"Glute-ham raise","cat":"ISCHIO","equipement":"Machine","difficulte":5,"reps":"8–12","muscles_secondaires":"Fessiers, Érecteurs","notes":"Ischio en flexion ET extension. Très avancé."},
    {"id":"nordic_hamstring","nom":"Nordic hamstring curl","cat":"ISCHIO","equipement":"Poids de corps","difficulte":5,"reps":"5–10","muscles_secondaires":"","notes":"Genoux sur tapis, descente contrôlée. Excellente excentriq."},
    {"id":"leg_curl_poulie","nom":"Leg curl poulie","cat":"ISCHIO","equipement":"Poulie","difficulte":2,"reps":"12–15","muscles_secondaires":"","notes":"Poulie basse, tension constante."},

    # ══════════════════════════════════════════════════════════════════════
    #  MOLLETS
    # ══════════════════════════════════════════════════════════════════════
    {"id":"calf_raise_debout","nom":"Extension mollets debout (standing calf raise)","cat":"MOLLETS","equipement":"Machine","difficulte":1,"reps":"15–25","muscles_secondaires":"Soléaire","notes":"Jambes tendues. Gastrocnémiens. Amplitude complète."},
    {"id":"calf_raise_assis","nom":"Extension mollets assis (seated calf raise)","cat":"MOLLETS","equipement":"Machine","difficulte":1,"reps":"15–25","muscles_secondaires":"","notes":"Jambes fléchies = Soléaire. Amplitude complète."},
    {"id":"calf_raise_presse","nom":"Extension mollets sur presse","cat":"MOLLETS","equipement":"Machine","difficulte":1,"reps":"15–25","muscles_secondaires":"","notes":"Pointes de pieds sur le bord de la presse."},
    {"id":"calf_raise_unilateral","nom":"Extension mollets unilatéral","cat":"MOLLETS","equipement":"Poids de corps","difficulte":2,"reps":"15–20/jambe","muscles_secondaires":"","notes":"Sur une jambe. Corrige les déséquilibres."},
    {"id":"calf_raise_barre","nom":"Extension mollets barre debout","cat":"MOLLETS","equipement":"Barre","difficulte":2,"reps":"15–20","muscles_secondaires":"","notes":"Barre sur le dos. Charge lourde possible."},
    {"id":"calf_raise_haltere","nom":"Extension mollets haltère","cat":"MOLLETS","equipement":"Haltères","difficulte":2,"reps":"15–20","muscles_secondaires":"","notes":"Haltère dans une main, appui sur une marche."},
    {"id":"saut_corde_mollets","nom":"Sauts à la corde","cat":"MOLLETS","equipement":"Poids de corps","difficulte":2,"reps":"2–5 min","muscles_secondaires":"Cardio, Coordination","notes":"Cardio + gainage mollets. Impact plyométrique."},

    # ══════════════════════════════════════════════════════════════════════
    #  FULL BODY / POLYARTICULAIRES POPULAIRES
    # ══════════════════════════════════════════════════════════════════════
    {"id":"soulevé_de_terre","nom":"Soulevé de terre (deadlift)","cat":"FULL_BODY","equipement":"Barre","difficulte":5,"reps":"3–8","muscles_secondaires":"Tout le corps","notes":"Mouvement fondamental. Technique irréprochable."},
    {"id":"squat_front","nom":"Front squat","cat":"FULL_BODY","equipement":"Barre","difficulte":5,"reps":"5–10","muscles_secondaires":"Core, Fessiers, Quad","notes":"Barre devant. Mobilité élevée requise."},
    {"id":"snatch","nom":"Snatch (arraché)","cat":"FULL_BODY","equipement":"Barre","difficulte":5,"reps":"1–5","muscles_secondaires":"Tout le corps","notes":"Haltérophilie. Barre en un geste au-dessus."},
    {"id":"clean_jerk","nom":"Clean and jerk (épaulé-jeté)","cat":"FULL_BODY","equipement":"Barre","difficulte":5,"reps":"1–3","muscles_secondaires":"Tout le corps","notes":"2 phases. Technique avancée."},
    {"id":"thruster","nom":"Thruster","cat":"FULL_BODY","equipement":"Barre","difficulte":4,"reps":"8–15","muscles_secondaires":"Épaules, Core, Jambes","notes":"Squat + développé militaire enchaîné. CrossFit."},
    {"id":"burpee","nom":"Burpee","cat":"FULL_BODY","equipement":"Poids de corps","difficulte":3,"reps":"10–20","muscles_secondaires":"Cardio complet","notes":"Pompe + saut. Conditioning et cardio."},
    {"id":"kettlebell_swing","nom":"Kettlebell swing","cat":"FULL_BODY","equipement":"Kettlebell","difficulte":3,"reps":"15–30","muscles_secondaires":"Fessiers, Dos, Épaules","notes":"Propulsion de la hanche. Ne pas tirer avec les bras."},
    {"id":"turkish_getup","nom":"Turkish get-up","cat":"FULL_BODY","equipement":"Kettlebell","difficulte":4,"reps":"3–5/côté","muscles_secondaires":"Core, Stabilisation","notes":"Séquence de 7 étapes. Mobilité et force."},
    {"id":"clean_halteres","nom":"Clean haltères","cat":"FULL_BODY","equipement":"Haltères","difficulte":4,"reps":"6–10","muscles_secondaires":"Ischio, Épaules, Core","notes":"Version haltères du clean. Explosivité."},
]


# ══════════════════════════════════════════════════════════════════════════════
#  FONCTIONS UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════

def get_all_exercices() -> List[Dict[str, Any]]:
    """Retourne tous les exercices triés par catégorie puis difficulté."""
    return sorted(
        EXERCICES,
        key=lambda e: (CAT_ORDER.get(e["cat"], 99), e.get("difficulte", 3))
    )


def get_by_categorie(cat: str) -> List[Dict[str, Any]]:
    """Retourne les exercices d'une catégorie (ex: 'PECS')."""
    return [e for e in EXERCICES if e["cat"] == cat.upper()]


def get_by_equipement(equipement: str) -> List[Dict[str, Any]]:
    """Filtre par équipement (ex: 'Barre', 'Haltères', 'Poids de corps')."""
    eq = equipement.strip().lower()
    return [e for e in EXERCICES if eq in e.get("equipement", "").lower()]


def search_exercices(query: str) -> List[Dict[str, Any]]:
    """Recherche textuelle dans nom, notes, muscles_secondaires, catégorie."""
    q = query.strip().lower()
    if not q:
        return get_all_exercices()
    return [
        e for e in EXERCICES
        if q in e["nom"].lower()
        or q in e.get("notes", "").lower()
        or q in e.get("muscles_secondaires", "").lower()
        or q in CAT_LABELS.get(e["cat"], "").lower()
    ]


def get_categories() -> List[str]:
    """Retourne la liste ordonnée des catégories présentes."""
    seen, cats = set(), []
    for e in get_all_exercices():
        c = e["cat"]
        if c not in seen:
            seen.add(c)
            cats.append(c)
    return cats


def find_by_id(eid: str) -> Dict[str, Any] | None:
    """Trouve un exercice par son id."""
    for e in EXERCICES:
        if e["id"] == eid:
            return e
    return None
