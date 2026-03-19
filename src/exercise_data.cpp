// exercise_data.cpp — Catalogue exercices et techniques THRESHOLD
// Porté depuis Python exercices_catalogue.py + training_techniques.py
#include "exercise_data.h"
#include <algorithm>

namespace threshold {

const std::map<std::string, std::string> CAT_LABELS = {
    {"PECS","Pectoraux"},{"DOS","Dos"},{"EPAULES","Épaules"},
    {"BICEPS","Biceps"},{"TRICEPS","Triceps"},{"ABDOS","Abdominaux"},
    {"QUADRICEPS","Quadriceps"},{"FESSIERS","Fessiers"},
    {"ISCHIO","Ischio-jambiers"},{"MOLLETS","Mollets"},{"FULL_BODY","Full body"},
};
const std::map<std::string, std::string> CAT_ICONS = {
    {"PECS","🏋️"},{"DOS","🔙"},{"EPAULES","🔝"},{"BICEPS","💪"},
    {"TRICEPS","💪"},{"ABDOS","🎯"},{"QUADRICEPS","🦵"},{"FESSIERS","🍑"},
    {"ISCHIO","🦵"},{"MOLLETS","🦶"},{"FULL_BODY","⭐"},
};

const std::vector<Exercise> EXERCICES = {
    // ── PECTORAUX (24) ──
    {"developpe_couche_barre","Développé couché barre","PECS","moyen","Barre",3,"6–12","Triceps, Épaules ant.","Exercice roi pecs."},
    {"developpe_incline_barre","Développé incliné barre","PECS","superieur","Barre",3,"8–12","Triceps, Deltoïdes","Banc 30–45°."},
    {"developpe_decline_barre","Développé décliné barre","PECS","inferieur","Barre",3,"8–12","Triceps","Banc décliné."},
    {"developpe_couche_halteres","Développé couché haltères","PECS","moyen","Haltères",3,"8–15","Triceps, Épaules ant.","Amplitude supérieure."},
    {"developpe_incline_halteres","Développé incliné haltères","PECS","superieur","Haltères",3,"10–15","Triceps, Deltoïdes","Pecs supérieurs."},
    {"ecarte_couche_halteres","Écarté couché haltères","PECS","moyen","Haltères",2,"12–15","Épaules ant.","Finition."},
    {"ecarte_incline_halteres","Écarté incliné haltères","PECS","superieur","Haltères",2,"12–15","Épaules ant.","Faisceau claviculaire."},
    {"pompe","Pompe (push-up)","PECS","complet","Poids de corps",1,"10–30","Triceps, Épaules","Base calisthenics."},
    {"dips_pecs","Dips version pectoraux","PECS","inferieur","Poids de corps",3,"8–15","Triceps, Épaules","Corps penché en avant."},
    {"cable_crossover","Croisé poulie","PECS","moyen","Poulie",2,"12–15","Épaules ant.","Contraction max en fin."},
    {"peck_deck","Peck-deck (butterfly)","PECS","moyen","Machine",1,"12–15","Épaules ant.","Isolation, finition."},
    {"developpe_couche_machine","Développé couché machine","PECS","moyen","Machine",1,"10–15","Triceps, Épaules","Machine convergente."},
    {"pullover_haltere","Pull-over haltère","PECS","complet","Haltères",2,"12–15","Grand dorsal, Dentelé","Expansion cage thoracique."},
    {"developpe_couche_smith","Développé couché Smith","PECS","moyen","Smith",2,"8–15","Triceps, Épaules","Guidé."},
    {"pompe_diamant","Pompe diamant","PECS","inferieur","Poids de corps",3,"10–20","Triceps","Mains en triangle."},
    // ── DOS (20) ──
    {"traction","Traction (pull-up)","DOS","general","Poids de corps",4,"5–15","Biceps, Rhomboïdes, Trapèze","Exercice roi du dos."},
    {"chin_up","Chin-up (supination)","DOS","general","Poids de corps",3,"6–15","Biceps, Trapèze inf.","Plus de biceps."},
    {"souleve_de_terre","Soulevé de terre","DOS","general","Barre",5,"3–8","Quadriceps, Fessiers, Trapèze","Technique irréprochable."},
    {"romanian_deadlift","Romanian deadlift (RDL)","DOS","general","Barre",3,"8–12","Fessiers, Érecteurs","Jambes quasi tendues."},
    {"rowing_barre_pronation","Rowing barre pronation","DOS","general","Barre",3,"6–12","Biceps, Rhomboïdes","Buste 45°."},
    {"rowing_haltere_unilateral","Rowing haltère unilatéral","DOS","general","Haltères",2,"10–15","Biceps, Rhomboïdes","Appui sur banc."},
    {"tirage_vertical","Tirage vertical poulie haute","DOS","general","Poulie",2,"10–15","Biceps, Rhomboïdes","Tirer vers poitrine."},
    {"tirage_vertical_prise_serree","Tirage vertical prise serrée","DOS","general","Poulie",2,"10–15","Biceps, Grand rond","Centre du dos."},
    {"rowing_poulie_basse","Rowing poulie basse","DOS","general","Poulie",2,"10–15","Biceps, Érecteurs","Prise neutre."},
    {"shrug_barre","Shrug barre","DOS","general","Barre",2,"12–15","Élévateur scapulae","Haussements d'épaules."},
    {"shrug_halteres","Shrug haltères","DOS","general","Haltères",2,"12–15","Élévateur scapulae","Plus d'amplitude."},
    {"face_pull","Face pull","DOS","general","Poulie",2,"15–20","Deltoïdes post., Trapèze","Santé épaules."},
    {"hyperextension","Hyperextension","DOS","general","Machine",2,"12–20","Fessiers, Ischio","Érecteurs du rachis."},
    {"rowing_machine","Rowing machine","DOS","general","Machine",1,"10–15","Biceps","Guidé. Débutants."},
    {"rack_pull","Rack pull","DOS","general","Barre",4,"3–6","Fessiers, Ischio","Soulevé partiel."},
    // ── ÉPAULES (14) ──
    {"developpe_militaire_barre","Développé militaire barre","EPAULES","anterieur","Barre",4,"6–12","Triceps, Trapèze","Fondamental épaules."},
    {"developpe_militaire_halteres","Développé militaire haltères","EPAULES","anterieur","Haltères",3,"8–15","Triceps","Meilleure amplitude."},
    {"elevations_laterales","Élévations latérales haltères","EPAULES","moyen","Haltères",2,"12–20","Trapèze","Deltoïdes latéraux."},
    {"elevations_laterales_poulie","Élévations latérales poulie","EPAULES","moyen","Poulie",2,"15–20","Trapèze","Tension constante."},
    {"oiseau_halteres","Oiseau (écarté buste penché)","EPAULES","posterieur","Haltères",2,"12–20","Rhomboïdes, Trapèze","Deltoïdes postérieurs."},
    {"oiseau_poulie","Oiseau poulie","EPAULES","posterieur","Poulie",2,"15–20","Rhomboïdes","Poulies hautes croisées."},
    {"front_raise","Élévations frontales haltères","EPAULES","anterieur","Haltères",2,"12–15","Pecs sup.","Deltoïdes antérieurs."},
    {"upright_row","Rowing menton","EPAULES","complet","Barre",3,"10–15","Trapèze, Biceps","Attention impingement."},
    {"presse_epaules_machine","Presse à épaules machine","EPAULES","complet","Machine",1,"10–15","Triceps","Guidée. Sécurisé."},
    {"arnold_press","Arnold press","EPAULES","complet","Haltères",3,"10–15","Triceps","Rotation en mouvement."},
    // ── BICEPS (12) ──
    {"curl_barre","Curl barre droit","BICEPS","general","Barre",2,"8–12","Brachio-radial","Coudes collés au corps."},
    {"curl_barre_ez","Curl barre EZ","BICEPS","general","Barre",2,"8–12","Brachial ant.","Plus confortable poignets."},
    {"curl_haltere_alterne","Curl haltère alterné","BICEPS","general","Haltères",2,"10–15","Brachial ant.","Supination en mouvement."},
    {"curl_marteau","Curl marteau","BICEPS","general","Haltères",2,"10–15","Biceps","Épaisseur bras."},
    {"curl_incline_halteres","Curl incliné haltères","BICEPS","general","Haltères",2,"10–15","Brachial ant.","Banc 60°. Étirement complet."},
    {"curl_concentre","Curl concentré","BICEPS","general","Haltères",2,"12–15","","Pic du biceps, isolation max."},
    {"curl_poulie_basse","Curl poulie basse","BICEPS","general","Poulie",2,"12–15","Brachial ant.","Tension constante."},
    {"preacher_curl","Preacher curl","BICEPS","general","Barre",2,"10–12","","Isolation totale."},
    {"chin_up_biceps","Traction supination (biceps)","BICEPS","general","Poids de corps",4,"6–15","Grand dorsal","Polyarticulaire."},
    // ── TRICEPS (12) ──
    {"dips_triceps","Dips (version triceps)","TRICEPS","general","Poids de corps",3,"8–15","Pecs, Épaules","Corps vertical."},
    {"extension_triceps_poulie","Extension triceps poulie (corde)","TRICEPS","general","Poulie",1,"12–15","","Coudes fixes."},
    {"skullcrusher","Skullcrusher","TRICEPS","general","Barre",3,"10–15","","Barre EZ recommandée."},
    {"developpe_prise_serree","Développé couché prise serrée","TRICEPS","general","Barre",3,"6–12","Pecs, Épaules","Force + masse."},
    {"overhead_extension_haltere","Extension overhead haltère","TRICEPS","general","Haltères",2,"12–15","","Derrière la nuque."},
    {"overhead_extension_poulie","Extension overhead poulie","TRICEPS","general","Poulie",2,"12–15","","Poulie basse."},
    {"kickback_triceps","Kickback triceps haltère","TRICEPS","general","Haltères",2,"12–15","","Extension vers l'arrière."},
    {"dips_banc","Dips au banc","TRICEPS","general","Poids de corps",2,"12–20","Épaules","Débutants."},
    // ── ABDOMINAUX (12) ──
    {"crunch","Crunch au sol","ABDOS","general","Poids de corps",1,"15–25","Transverse","Montée partielle."},
    {"planche","Planche (gainage)","ABDOS","general","Poids de corps",2,"30–120 s","Érecteurs, Fessiers","Corps aligné."},
    {"planche_laterale","Planche latérale","ABDOS","general","Poids de corps",3,"30–60 s","Obliques ext.","Corps aligné de côté."},
    {"releve_jambes_suspendu","Relevé de jambes suspendu","ABDOS","general","Poids de corps",3,"10–20","Psoas","Variante genoux fléchis."},
    {"russian_twist","Russian twist","ABDOS","general","Poids de corps",2,"20–30","Obliques, Transverse","Pieds décollés."},
    {"ab_wheel","Rouleau abdominal","ABDOS","general","Poids de corps",4,"8–15","Grand dorsal, Épaules","Très exigeant."},
    {"crunch_poulie","Crunch poulie haute","ABDOS","general","Poulie",2,"15–20","","Contraction vers genoux."},
    {"mountain_climber","Mountain climber","ABDOS","general","Poids de corps",3,"20–30 s","Épaules","Cardio-abdos."},
    {"dragon_flag","Dragon flag","ABDOS","general","Poids de corps",5,"5–10","Core complet","Technique Bruce Lee."},
    // ── QUADRICEPS (14) ──
    {"squat_barre","Squat barre (back squat)","QUADRICEPS","quadriceps","Barre",4,"5–12","Fessiers, Ischio, Érecteurs","Roi des exercices."},
    {"front_squat","Front squat","QUADRICEPS","quadriceps","Barre",5,"6–10","Fessiers, Core","Forte mobilité requise."},
    {"leg_press","Leg press","QUADRICEPS","quadriceps","Machine",2,"10–20","Fessiers, Ischio","Pieds hauts=fessiers."},
    {"hack_squat","Hack squat machine","QUADRICEPS","quadriceps","Machine",3,"10–15","Fessiers","Pieds écartés ou serrés."},
    {"leg_extension","Leg extension","QUADRICEPS","quadriceps","Machine",1,"12–20","","Isolation pure quads."},
    {"fente_avant","Fente avant (lunges)","QUADRICEPS","quadriceps","Poids de corps",2,"10–15/jambe","Fessiers, Ischio","Genou à 90°."},
    {"fente_bulgare","Fente bulgare","QUADRICEPS","quadriceps","Poids de corps",4,"10–15/jambe","Fessiers, Ischio","Pied arrière sur banc."},
    {"squat_gobelet","Squat gobelet","QUADRICEPS","quadriceps","Kettlebell",2,"12–15","Fessiers, Core","Bonne posture."},
    {"squat_smith","Squat Smith machine","QUADRICEPS","quadriceps","Smith",2,"10–15","Fessiers","Guidé. Sécurisé."},
    {"sissy_squat","Sissy squat","QUADRICEPS","quadriceps","Poids de corps",4,"10–15","","Isolation extreme quads."},
    // ── FESSIERS (10) ──
    {"hip_thrust","Hip thrust barre","FESSIERS","fessiers","Barre",3,"8–20","Ischio, Quadriceps","Poussée des hanches."},
    {"hip_thrust_machine","Hip thrust machine","FESSIERS","fessiers","Machine",1,"12–20","Ischio","Version guidée."},
    {"squat_sumo","Squat sumo","FESSIERS","fessiers","Barre",3,"10–15","Adducteurs, Quadriceps","Pieds très écartés."},
    {"kickback_fessiers","Kickback fessiers","FESSIERS","fessiers","Poids de corps",1,"15–20/jambe","","Extension jambe arrière."},
    {"abduction_machine","Abduction machine","FESSIERS","fessiers","Machine",1,"15–25","","Fessiers moyens."},
    {"souleve_terre_roumain","Soulevé de terre roumain","FESSIERS","fessiers","Barre",3,"10–15","Ischio, Érecteurs","Charnière de hanche."},
    {"step_up","Step-up","FESSIERS","fessiers","Poids de corps",2,"12–15/jambe","Quadriceps, Ischio","Monter sur banc."},
    {"pont_fessiers","Pont fessiers","FESSIERS","fessiers","Poids de corps",1,"15–20","Ischio","Version au sol."},
    // ── ISCHIO-JAMBIERS (10) ──
    {"leg_curl_couche","Leg curl couché machine","ISCHIO","ischio","Machine",1,"10–15","Mollets","Isolation ischio."},
    {"leg_curl_assis","Leg curl assis machine","ISCHIO","ischio","Machine",1,"10–15","","Chef long."},
    {"rdl","Romanian deadlift (RDL)","ISCHIO","ischio","Barre",3,"8–12","Fessiers, Érecteurs","Étirement maximum."},
    {"rdl_halteres","RDL haltères","ISCHIO","ischio","Haltères",3,"10–15","Fessiers","Plus d'amplitude."},
    {"rdl_unilateral","RDL unilatéral","ISCHIO","ischio","Haltères",4,"10–12/jambe","Fessiers, Core","Force unilatérale."},
    {"glute_ham_raise","Glute-ham raise","ISCHIO","ischio","Machine",5,"8–12","Fessiers, Érecteurs","Très avancé."},
    {"nordic_hamstring","Nordic hamstring curl","ISCHIO","ischio","Poids de corps",5,"5–10","","Excellente excentrique."},
    // ── MOLLETS (7) ──
    {"calf_raise_debout","Extension mollets debout","MOLLETS","general","Machine",1,"15–25","Soléaire","Amplitude complète."},
    {"calf_raise_assis","Extension mollets assis","MOLLETS","general","Machine",1,"15–25","","Soléaire."},
    {"calf_raise_presse","Extension mollets presse","MOLLETS","general","Machine",1,"15–25","","Pointes sur bord presse."},
    {"calf_raise_unilateral","Extension mollets unilatéral","MOLLETS","general","Poids de corps",2,"15–20/jambe","","Corrige déséquilibres."},
    {"saut_corde_mollets","Sauts à la corde","MOLLETS","general","Poids de corps",2,"2–5 min","Cardio","Impact plyométrique."},
    // ── FULL BODY (9) ──
    {"soulevé_de_terre","Soulevé de terre","FULL_BODY","general","Barre",5,"3–8","Tout le corps","Mouvement fondamental."},
    {"squat_front","Front squat","FULL_BODY","general","Barre",5,"5–10","Core, Fessiers, Quad","Mobilité élevée."},
    {"thruster","Thruster","FULL_BODY","general","Barre",4,"8–15","Épaules, Core, Jambes","Squat + développé."},
    {"burpee","Burpee","FULL_BODY","general","Poids de corps",3,"10–20","Cardio complet","Pompe + saut."},
    {"kettlebell_swing","Kettlebell swing","FULL_BODY","general","Kettlebell",3,"15–30","Fessiers, Dos, Épaules","Propulsion hanche."},
    {"turkish_getup","Turkish get-up","FULL_BODY","general","Kettlebell",4,"3–5/côté","Core, Stabilisation","Séquence 7 étapes."},
    {"clean_halteres","Clean haltères","FULL_BODY","general","Haltères",4,"6–10","Ischio, Épaules, Core","Explosivité."},
};

const std::vector<Technique> TECHNIQUES = {
    // ── SARCOPLASMIQUE ──
    {"bfr","Blood Flow Restriction (BFR)","SARCOPLASMIQUE","15–30","~20–30%","Court","Pump extrême, hypertrophie sarcoplasmique",5,2,"Sarco","Occlusion/Kaatsu."},
    {"inter_set_stretch","Inter-set stretching","SARCOPLASMIQUE","20–60 s stretch","Modérée","Pendant le stretch","Pump + stretch-mediated growth",4,3,"Sarco","Étirements entre séries."},
    {"21s","21's (7-7-7)","SARCOPLASMIQUE","7 bas + 7 haut + 7 complète","Légère–modérée","Aucun","Temps sous tension élevé, pump",3,3,"Sarco","Séries continues."},
    {"tempo_lent","Tempo lent / Superslow","SARCOPLASMIQUE","3–10 s tempo","Légère–modérée","Variable","Max TUT et signalisation",3,3,"Sarco","Accent excentrique."},
    {"pre_post_fatigue","Pré-fatigue / Post-fatigue","SARCOPLASMIQUE","Variation","Modérée","Court","Recrutement ciblé",3,3,"Sarco","Pré-fatigue muscle accessoire."},
    // ── MIXTE ──
    {"drop_set","Drop set","MIXTE","3–4 drops","De lourde à légère","Aucun entre drops","Hypertrophie + endurance",3,3,"Mixte","Réduire charge sans pause."},
    {"superset","Superset","MIXTE","2 exercices enchaînés","Variable","Court après le superset","Densité + pump",3,2,"Mixte","Agoniste/antagoniste ou même muscle."},
    {"giant_set","Giant set","MIXTE","3–4 exercices","Modérée","Court après le giant","Volume élevé + pump",4,3,"Mixte","3-4 exos même groupe sans pause."},
    {"rest_pause","Rest-pause","MIXTE","Failure + 10–15 s + reps","Lourde","10–15 s intra-set","Force + hypertrophie",4,4,"Mixte","Micro-pauses pour reps supplémentaires."},
    {"myo_reps","Myo-reps","MIXTE","Activation + micro-sets","Modérée","3–5 s","Efficacité temporelle",4,4,"Mixte","Set d'activation + mini-sets."},
    {"cluster_set","Cluster set","MIXTE","2–3 reps × 4–6 clusters","Lourde (85–90%)","15–30 s intra","Force + volume lourd",4,4,"Mixte","Mini-séries à charge lourde."},
    // ── MYOFIBRILLAIRE ──
    {"5x5","5×5 (Stronglifts)","MYOFIBRILLAIRE","5","Lourde (80–85%)","3–5 min","Force pure",3,3,"Myofib","Programme classique force."},
    {"531","5/3/1 (Wendler)","MYOFIBRILLAIRE","5/3/1","Progression calculée","3–5 min","Force progressive",4,4,"Myofib","Cycles de 4 semaines."},
    {"rm_test","Test de 1RM","MYOFIBRILLAIRE","1","Maximale","5+ min","Évaluer la force max",5,5,"Myofib","Échauffement progressif obligatoire."},
    {"negatives","Négatives (excentriques)","MYOFIBRILLAIRE","3–6","Supra-maximale (105–120%)","3–5 min","Force excentrique + masse",5,5,"Myofib","Partenaire requis."},
    {"isometrique","Isométrique","MYOFIBRILLAIRE","5–30 s maintien","Variable","2–3 min","Force angulaire spécifique",3,3,"Myofib","Position statique maintenue."},
    {"wave_loading","Wave loading","MYOFIBRILLAIRE","3/2/1 vagues","Lourde progressive","2–3 min","Force neurale",5,5,"Myofib","Potentialisation post-activation."},
};

// ═════════════════════════════════════════════════════════════════════════════
//  HELPERS
// ═════════════════════════════════════════════════════════════════════════════
std::vector<const Exercise*> get_exercises_by_cat(const std::string& cat) {
    std::vector<const Exercise*> result;
    for (auto& e : EXERCICES) if (e.cat == cat) result.push_back(&e);
    return result;
}

std::vector<const Exercise*> get_exercises_by_equipement(const std::string& equip) {
    std::vector<const Exercise*> result;
    for (auto& e : EXERCICES) if (e.equipement == equip) result.push_back(&e);
    return result;
}

const Exercise* get_exercise_by_id(const std::string& id) {
    for (auto& e : EXERCICES) if (e.id == id) return &e;
    return nullptr;
}

std::vector<const Technique*> get_techniques_by_categorie(const std::string& cat) {
    std::vector<const Technique*> result;
    for (auto& t : TECHNIQUES) if (t.categorie == cat) result.push_back(&t);
    return result;
}

} // namespace threshold
