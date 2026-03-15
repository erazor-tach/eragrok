# ui/cycle.py — THRESHOLD · Module Cycle Hormonal (Flet)
# ─────────────────────────────────────────────────────────────────────────────
# Port complet du cycle_module.py d'ERAGROK vers Flet.
# Logique métier identique, UI reconstruite en composants Flet mobile-first.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import re
import math
import datetime
from typing import Optional

import flet as ft

from ui.theme import (
    ACCENT, ACCENT_DIM, ACCENT_GLOW, ACCENT_HOVER,
    BG_CARD, BG_CARD2, BG_INPUT, BG_ROOT,
    BORDER, DANGER, DANGER_HVR, GRAY, GRAY_HVR, PURPLE, SUCCESS, SUCCESS_HVR,
    TEXT, TEXT_ACCENT, TEXT_MUTED, TEXT_SUB, WARNING,
    R_CARD, R_INPUT,
    mk_btn, mk_card, mk_card2, mk_dropdown, mk_entry,
    mk_label, mk_sep, mk_title, mk_badge,
)
from data import db as _db, utils
from data import injection_schedule as _inj

# ── Logique métier extraite (proposition #9) ──────────────────────────────────
from data.logic.cycle_logic import (
    _parse_dose_range, _recommended_dose, _calc_vials, _build_cycle_plan,
    _PCT_STRICT, _ORAL_PRODUCTS, _ESTER_WASHOUT, _PCT_NORMAL, _PCT_AGRESSIF,
    _dose_color,
)


# ══════════════════════════════════════════════════════════════════════════════
#  DONNÉES — identiques à eragrok/cycle_module.py
# ══════════════════════════════════════════════════════════════════════════════

CATEGORIES = {
    0: "Base cycle (Testostérones & Sustanon)",
    1: "Anabolisants injectables",
    2: "Anabolisants oraux",
    3: "Peptides",
    4: "Hormones",
    5: "Post Cycle Therapy — PCT (Clomid / Nolvadex)",
    6: "Anti-Aromatases & Anti-Prolactine (IA)",
}

CATEGORY_ITEMS = {
    0: ["Sustanon 250/300/350","Testosterone Enanthate","Testosterone Cypionate",
        "Testosterone Propionate","Testosterone Undecanoate (Nebido)"],
    1: ["Boldenone Undecylenate (Equipoise)","Drostanolone Enanthate (Masteron E)",
        "Drostanolone Propionate (Masteron P)","Methenolone Enanthate (Primobolan)",
        "Nandrolone Decanoate (Deca)","Nandrolone Phenylpropionate (NPP)",
        "Trenbolone Hexahydrobenzylcarbonate","Trenbolone Acetate","Trenbolone Enanthate",
        "Stanozolol Injection (Winstrol depot)","Cut Stack (mix Tren/Mast/Test)"],
    2: ["Mesterolone (Proviron)","Methandienone (Dianabol)","Oxandrolone (Anavar)",
        "Oxymetholone (Anadrol)","Stanozolol oral (Winstrol)","Turinabol","Halotestin",
        "Primobolan tablets"],
    3: ["Melanotan 2","BPC-157","TB-500","CJC-1295 sans DAC","CJC-1295 with DAC",
        "Ipamorelin","GHRP-6","GHRP-2","HGH Fragment 176-191","PEG MGF",
        "Tirzepatide","Semaglutide"],
    4: ["HGH Somatropin","HCG","Liothyronine T3","Lévothyroxine T4",
        "Insulin (listed for completeness only)","IGF-1 LR3"],
    5: ["Clomiphene (Clomid)","Tamoxifen (Nolvadex)"],
    6: ["Anastrozole (Arimidex)","Exemestane (Aromasin)","Letrozole (Femara)",
        "Cabergoline (Dostinex)"],
}

PRODUCT_INFO = {
    "Boldenone Undecylenate (Equipoise)":     {"utilite":"Masse maigre, vascularité, appétit","dose_min":"300–400 mg/sem","dose_max":"800 mg/sem","popularite":"★★★☆☆","dangerosite":"★★★☆☆","demi_vie":"~14 jours","notes":"RBC très haut, anxiété, appétit incontrôlable — min efficace 600 mg","dose":"300–400 mg/sem → 800 mg/sem","halflife":"~14 j","usage":"Masse maigre + vascularité — min efficace 600 mg"},
    "Drostanolone Enanthate (Masteron E)":    {"utilite":"Hardness, anti-estro, sèche finale","dose_min":"200–300 mg/sem","dose_max":"600 mg/sem","popularite":"★★★★☆","dangerosite":"★★☆☆☆","demi_vie":"~8–10 jours","notes":"Chute cheveux si prédisposé, articulations sèches","dose":"200–300 mg/sem → 600 mg/sem","halflife":"~8–10 j","usage":"Hardness, anti-estro, sèche finale"},
    "Drostanolone Propionate (Masteron P)":   {"utilite":"Hardness rapide, prépa contest","dose_min":"300–400 mg/sem","dose_max":"600 mg/sem","popularite":"★★★★☆","dangerosite":"★★☆☆☆","demi_vie":"~3 jours","notes":"Pins fréquents, effet plus aigu que Enanthate","dose":"300–400 mg/sem → 600 mg/sem","halflife":"~3 j","usage":"Hardness rapide, prépa contest"},
    "Methenolone Enanthate (Primobolan)":     {"utilite":"Masse très propre, zéro rétention","dose_min":"400 mg/sem","dose_max":"800 mg/sem","popularite":"★★★★☆","dangerosite":"★☆☆☆☆","demi_vie":"~10 jours","notes":"Très sûr, cher, beaucoup de faux","dose":"400 mg/sem → 800 mg/sem","halflife":"~10 j","usage":"Masse très propre, zéro rétention"},
    "Nandrolone Decanoate (Deca)":            {"utilite":"Masse, récupération articulaire","dose_min":"300 mg/sem","dose_max":"600 mg/sem","popularite":"★★★★★","dangerosite":"★★★★☆","demi_vie":"~7–15 jours","notes":"Prolactine, 'Deca dick', rétention d'eau","dose":"300 mg/sem → 600 mg/sem","halflife":"~7–15 j","usage":"Masse + articulations + collagène"},
    "Nandrolone Phenylpropionate (NPP)":      {"utilite":"Deca rapide, moins de rétention","dose_min":"300 mg/sem","dose_max":"600 mg/sem","popularite":"★★★★☆","dangerosite":"★★★★☆","demi_vie":"~4–5 jours","notes":"Effets similaires à Deca mais kick plus rapide","dose":"300 mg/sem → 600 mg/sem","halflife":"~4–5 j","usage":"Deca rapide, moins de rétention"},
    "Trenbolone Hexahydrobenzylcarbonate":    {"utilite":"⚠ Usage vétérinaire — aucune étude humaine. Force, densité, sèche extrême","dose_min":"152–228 mg/sem","dose_max":"400 mg/sem","popularite":"★★★★★","dangerosite":"★★★★★","demi_vie":"~14 jours","notes":"Retiré du marché humain (Parabolan). Risque cancer prostate, cardio, insomnie, agressivité","dose":"152–228 mg/sem → 400 mg/sem","halflife":"~14 j","usage":"⚠ Usage vétérinaire, aucune étude humaine. Retiré du marché humain (Parabolan) dans les années 90"},
    "Sustanon 250/300/350":                   {"utilite":"Base polyvalente, kick + longue durée","dose_min":"250–375 mg/sem","dose_max":"750 mg/sem","popularite":"★★★★★","dangerosite":"★★★☆☆","demi_vie":"mix 7–15 jours","notes":"Œstrogènes variables selon batch","dose":"250–375 mg/sem → 750 mg/sem","halflife":"mix 7–15 j","usage":"Base polyvalente, kick + longue durée"},
    "Testosterone Enanthate":                 {"utilite":"Base (masse/force)","dose_min":"250–500 mg/sem","dose_max":"1000 mg/sem","popularite":"★★★★★","dangerosite":"★★★☆☆","demi_vie":"~8–10 jours","notes":"Œstrogènes, risque de gynécomastie sans IA","dose":"250–500 mg/sem → 1000 mg/sem","halflife":"~8–10 j","usage":"Base absolue masse/force — avancés jusqu'à 1000 mg"},
    "Testosterone Cypionate":                 {"utilite":"Similaire à Enanthate","dose_min":"250–500 mg/sem","dose_max":"1000 mg/sem","popularite":"★★★★★","dangerosite":"★★★☆☆","demi_vie":"~8–12 jours","notes":"Effets similaires à Enanthate","dose":"250–500 mg/sem → 1000 mg/sem","halflife":"~8–12 j","usage":"Quasi identique à Enanthate"},
    "Testosterone Propionate":                {"utilite":"Base courte, sèche, kick rapide","dose_min":"100 mg EOD","dose_max":"150 mg EOD","popularite":"★★★★☆","dangerosite":"★★★☆☆","demi_vie":"~2–3 jours","notes":"Injections fréquentes, douloureuses","dose":"100 mg EOD → 150 mg EOD","halflife":"~2–3 j","usage":"Base courte, sèche, kick rapide — pins fréquents"},
    "Testosterone Undecanoate (Nebido)":      {"utilite":"Testostérone longue durée","dose_min":"1000 mg / 10–14 sem","dose_max":"1000 mg / 8–10 sem","popularite":"★★★☆☆","dangerosite":"★★★☆☆","demi_vie":"20–34 jours","notes":"Très lent à monter/descendre","dose":"1000 mg/10 sem → 1000 mg/8 sem","halflife":"20–34 j","usage":"Test très longue durée, TRT"},
    "Trenbolone Acetate":                     {"utilite":"⚠ Usage vétérinaire — aucune étude humaine. Force, sèche extrême","dose_min":"50–75 mg EOD","dose_max":"75–100 mg EOD","popularite":"★★★★★","dangerosite":"★★★★★","demi_vie":"~2–3 jours","notes":"Marché noir uniquement. Sueurs nocturnes, insomnie, agressivité, atrophie testiculaire","dose":"50–75 mg EOD → 75–100 mg EOD","halflife":"~2–3 j","usage":"⚠ Usage vétérinaire, aucune étude humaine. Marché noir uniquement"},
    "Trenbolone Enanthate":                   {"utilite":"⚠ Usage vétérinaire — aucune étude humaine. Tren longue durée","dose_min":"200–300 mg/sem","dose_max":"500 mg/sem","popularite":"★★★★★","dangerosite":"★★★★★","demi_vie":"~8–10 jours","notes":"Jamais approuvé. Marché noir uniquement. Mêmes risques que les autres esters","dose":"200–300 mg/sem → 500 mg/sem","halflife":"~8–10 j","usage":"⚠ Usage vétérinaire, aucune étude humaine. Jamais approuvé"},
    "Stanozolol Injection (Winstrol depot)":  {"utilite":"Dureté, force sans prise de poids","dose_min":"50 mg EOD","dose_max":"100 mg EOD","popularite":"★★★★☆","dangerosite":"★★★★☆","demi_vie":"~24 h","notes":"Articulations sèches, impact foie et cholestérol","dose":"50 mg EOD → 100 mg EOD","halflife":"~24 h","usage":"Dureté, force sans poids — cutting avancé jusqu'à 100 mg"},
    "Cut Stack (mix Tren/Mast/Test)":         {"utilite":"Coupe sèche ultra-agressive","dose_min":"300–450 mg/sem (mix)","dose_max":"600 mg/sem (mix)","popularite":"★★★★☆","dangerosite":"★★★★★","demi_vie":"variable","notes":"Cumul des effets secondaires des composants","dose":"300–450 mg/sem → 600 mg/sem","halflife":"variable","usage":"Coupe sèche ultra-agressive — cumul effets secondaires"},
    "Mesterolone (Proviron)":                 {"utilite":"Anti-œstro, libido, dureté","dose_min":"25 mg/j","dose_max":"50–100 mg/j","popularite":"★★★★☆","dangerosite":"★☆☆☆☆","demi_vie":"~12 h","notes":"Très sûr, souvent sous-dosé","dose":"25 mg/j → 50–100 mg/j","halflife":"~12 h","usage":"Anti-œstro, libido, dureté — souvent sous-dosé"},
    "Methandienone (Dianabol)":               {"utilite":"Masse rapide + force","dose_min":"20–30 mg/j","dose_max":"50–75 mg/j","popularite":"★★★★★","dangerosite":"★★★★★","demi_vie":"~4–6 h","notes":"Hépatotoxicité, œstrogènes, rétention massive — max 6 sem","dose":"20–30 mg/j → 50–75 mg/j","halflife":"~4–6 h","usage":"Kickstart masse rapide — max 6 sem (hépatotoxique)"},
    "Oxandrolone (Anavar)":                   {"utilite":"Sèche, force, perte graisse","dose_min":"30–50 mg/j","dose_max":"80–100 mg/j","popularite":"★★★★★","dangerosite":"★★☆☆☆","demi_vie":"~9–10 h","notes":"Très cher, faux fréquent","dose":"30–50 mg/j → 80–100 mg/j","halflife":"~9–10 h","usage":"Sèche, force, perte graisse — avancés jusqu'à 100 mg"},
    "Oxymetholone (Anadrol)":                 {"utilite":"Masse massive","dose_min":"50 mg/j","dose_max":"100–150 mg/j","popularite":"★★★★☆","dangerosite":"★★★★★","demi_vie":"~8–9 h","notes":"Foie très toxique, rétention importante","dose":"50 mg/j → 100–150 mg/j","halflife":"~8–9 h","usage":"Masse massive — très hépatotoxique, max 6 sem"},
    "Stanozolol oral (Winstrol)":             {"utilite":"Dureté, sèche, force","dose_min":"30–50 mg/j","dose_max":"80–100 mg/j","popularite":"★★★★★","dangerosite":"★★★★☆","demi_vie":"~8–9 h","notes":"Impact hépatique et articulations","dose":"30–50 mg/j → 80–100 mg/j","halflife":"~8–9 h","usage":"Dureté, sèche, force — articulations sèches"},
    "Turinabol":                              {"utilite":"Masse maigre, force","dose_min":"30–50 mg/j","dose_max":"80–100 mg/j","popularite":"★★★☆☆","dangerosite":"★★★☆☆","demi_vie":"~16 h","notes":"Plus sûr que Dianabol","dose":"30–50 mg/j → 80–100 mg/j","halflife":"~16 h","usage":"Masse maigre, force — plus sûr que Dianabol"},
    "Halotestin":                             {"utilite":"Force pure (powerlifting)","dose_min":"10–20 mg/j","dose_max":"30–40 mg/j","popularite":"★★★☆☆","dangerosite":"★★★★★","demi_vie":"~6–8 h","notes":"Hépatotoxicité, agressivité","dose":"10–20 mg/j → 30–40 mg/j","halflife":"~6–8 h","usage":"Force pure powerlifting — très hépatotoxique"},
    "Primobolan tablets":                     {"utilite":"Coupe maigre qualité","dose_min":"50–100 mg/j","dose_max":"150 mg/j","popularite":"★★★★☆","dangerosite":"★★☆☆☆","demi_vie":"~4–6 h","notes":"Très cher, faux fréquent","dose":"50–100 mg/j → 150 mg/j","halflife":"~4–6 h","usage":"Coupe maigre qualité — très cher, faux fréquents"},
    "Melanotan 2":                            {"utilite":"Bronzage, libido","dose_min":"0.25–0.5 mg/j","dose_max":"1–2 mg/j","popularite":"★★★☆☆","dangerosite":"★★★☆☆","demi_vie":"—","notes":"Nausées, érections spontanées","dose":"0.25–0.5 mg/j → 1–2 mg/j","halflife":"—","usage":"Bronzage + libido — nausées, érections spontanées"},
    "BPC-157":                                {"utilite":"Cicatrisation tendons/intestin","dose_min":"250–500 mcg/j","dose_max":"500–1000 mcg/j","popularite":"★★★★★","dangerosite":"★☆☆☆☆","demi_vie":"—","notes":"Très utilisé, profil de sécurité favorable","dose":"250–500 mcg/j → 500–1000 mcg/j","halflife":"—","usage":"Cicatrisation tendons/intestin — très sûr"},
    "TB-500":                                 {"utilite":"Cicatrisation, mobilité","dose_min":"2–5 mg/sem","dose_max":"7.5–10 mg/sem","popularite":"★★★★☆","dangerosite":"★★☆☆☆","demi_vie":"—","notes":"Souvent combiné avec BPC-157","dose":"2–5 mg/sem → 7.5–10 mg/sem","halflife":"—","usage":"Cicatrisation + mobilité — souvent combiné BPC"},
    "CJC-1295 sans DAC":                      {"utilite":"GH pulsatile","dose_min":"100 mcg 3x/j","dose_max":"200 mcg 3x/j","popularite":"★★★★☆","dangerosite":"★★☆☆☆","demi_vie":"—","notes":"À combiner avec GHRP","dose":"100 mcg 3×/j → 200 mcg 3×/j","halflife":"—","usage":"GH pulsatile — à combiner avec GHRP"},
    "CJC-1295 with DAC":                      {"utilite":"GH continue","dose_min":"1–2 mg/sem","dose_max":"2–4 mg/sem","popularite":"★★★☆☆","dangerosite":"★★☆☆☆","demi_vie":"—","notes":"Moins pulsatile","dose":"1–2 mg/sem → 2–4 mg/sem","halflife":"—","usage":"GH continue — moins pulsatile"},
    "Ipamorelin":                             {"utilite":"GH doux, sélectif","dose_min":"100–300 mcg 2–3x/j","dose_max":"300 mcg 3x/j","popularite":"★★★★☆","dangerosite":"★☆☆☆☆","demi_vie":"—","notes":"Très sûr","dose":"100–300 mcg 2–3×/j → 300 mcg 3×/j","halflife":"—","usage":"GH doux + sélectif — très sûr, peu d'appétit"},
    "GHRP-6":                                 {"utilite":"GH + forte faim","dose_min":"100 mcg 3x/j","dose_max":"200 mcg 3x/j","popularite":"★★★☆☆","dangerosite":"★★☆☆☆","demi_vie":"—","notes":"Faim marquée","dose":"100 mcg 3×/j → 200 mcg 3×/j","halflife":"—","usage":"GH + forte faim — faim très marquée"},
    "GHRP-2":                                 {"utilite":"GH + appétit modéré","dose_min":"100 mcg 3x/j","dose_max":"200 mcg 3x/j","popularite":"★★★☆☆","dangerosite":"★★☆☆☆","demi_vie":"—","notes":"Moins d'appétit que GHRP-6","dose":"100 mcg 3×/j → 200 mcg 3×/j","halflife":"—","usage":"GH + appétit modéré — moins faim que GHRP-6"},
    "HGH Fragment 176-191":                   {"utilite":"Lipolyse ciblée","dose_min":"250 mcg 2x/j","dose_max":"500 mcg 2x/j","popularite":"★★★★☆","dangerosite":"★☆☆☆☆","demi_vie":"—","notes":"Pas d'effet GH systémique","dose":"250 mcg 2×/j → 500 mcg 2×/j","halflife":"—","usage":"Lipolyse ciblée — pas d'effet GH global"},
    "PEG MGF":                                {"utilite":"Récupération musculaire locale","dose_min":"200 mcg/sem","dose_max":"400 mcg/sem","popularite":"★★★☆☆","dangerosite":"★★☆☆☆","demi_vie":"—","notes":"Post-entraînement","dose":"200 mcg post-ent → 400 mcg post-ent","halflife":"—","usage":"Hypertrophie locale post-entraînement"},
    "Tirzepatide":                            {"utilite":"Perte de poids, contrôle glycémique","dose_min":"2.5 mg/sem","dose_max":"15 mg/sem","popularite":"★★★★★","dangerosite":"★★☆☆☆","demi_vie":"~5 jours","notes":"Nausées fréquentes en début, titration progressive","dose":"2.5 mg/sem → 15 mg/sem","halflife":"—","usage":"Perte de poids massive (Mounjaro)"},
    "Semaglutide":                            {"utilite":"Perte de poids, satiété","dose_min":"0.25 mg/sem","dose_max":"2.4 mg/sem","popularite":"★★★★★","dangerosite":"★★☆☆☆","demi_vie":"~7 jours","notes":"Nausées, titration obligatoire","dose":"0.25 mg/sem → 2.4 mg/sem","halflife":"—","usage":"Perte de poids (Ozempic/Wegovy)"},
    "HGH Somatropin":                         {"utilite":"Masse maigre, récupération, anti-âge","dose_min":"2–4 UI/j","dose_max":"6–10 UI/j","popularite":"★★★★★","dangerosite":"★★★☆☆","demi_vie":"~2–3 h","notes":"Rétention eau, syndrome canal carpien, coût élevé — faux très courants","dose":"2–4 UI/j → 6–10 UI/j","halflife":"—","usage":"Récupération + anti-âge + masse maigre"},
    "HCG":                                    {"utilite":"Maintien testiculaire pendant cycle","dose_min":"250–500 UI 2x/sem","dose_max":"1000–1500 UI 2x/sem","popularite":"★★★★★","dangerosite":"★★☆☆☆","demi_vie":"~36 h","notes":"Démarre S3, arrêt 4–5 jours avant PCT","dose":"250–500 UI 2×/sem → 1000–1500 UI 2×/sem","halflife":"—","usage":"Maintien testicules / testostérone"},
    "Liothyronine T3":                        {"utilite":"Métabolisme, sèche","dose_min":"25 mcg/j","dose_max":"100 mcg/j","popularite":"★★★★☆","dangerosite":"★★★★☆","demi_vie":"~2.5 jours","notes":"Catabolisme musculaire si trop haut","dose":"25–75 mcg/j","halflife":"~2.5 j","usage":"Métabolisme, sèche, thyroïde"},
    "Lévothyroxine T4":                       {"utilite":"Thyroïde, métabolisme de base","dose_min":"25–50 mcg/j","dose_max":"150–200 mcg/j","popularite":"★★★☆☆","dangerosite":"★★★☆☆","demi_vie":"~7 jours","notes":"Action lente","dose":"50–200 mcg/j","halflife":"~7 j","usage":"Support thyroïde"},
    "Insulin (listed for completeness only)": {"utilite":"Transport nutriments post-workout","dose_min":"—","dose_max":"—","popularite":"★★★★★","dangerosite":"★★★★★","demi_vie":"variable","notes":"⚠️ DANGER DE MORT — hypoglycémie","dose":"—","halflife":"~5 min","usage":"⚠ Référence uniquement — ne pas utiliser sans supervision médicale"},
    "IGF-1 LR3":                              {"utilite":"Croissance musculaire locale","dose_min":"20–50 mcg/j","dose_max":"80–120 mcg/j","popularite":"★★★★☆","dangerosite":"★★★☆☆","demi_vie":"~20–30 h","notes":"Hypoglycémie, croissance organes internes","dose":"20–50 mcg/j → 80–120 mcg/j","halflife":"—","usage":"Hypertrophie locale + globale — hypoglycémie possible"},
    "Clomiphene (Clomid)":                    {"utilite":"Relance HPTA post-cycle","dose_min":"50 mg/j S1–2","dose_max":"100 mg/j (agressif S1)","popularite":"★★★★★","dangerosite":"★★☆☆☆","demi_vie":"~5–7 jours","notes":"Troubles visuels possibles, humeur. Ne pas utiliser pendant le cycle.","timing":"J14 post-cycle — matin à jeun","oral":True,"dose":"50 mg/j → 100–200 mg/j","halflife":"~5 j","usage":"Relance axe HPTA — vision floue possible"},
    "Tamoxifen (Nolvadex)":                   {"utilite":"Relance HPTA + anti-gynéco","dose_min":"20 mg/j S1–4","dose_max":"40 mg/j (agressif S1–2)","popularite":"★★★★★","dangerosite":"★★☆☆☆","demi_vie":"~5–7 jours","notes":"Combiné avec Clomid pour PCT optimal. Ne pas combiner avec Letrozole.","timing":"J14 post-cycle — à prendre avec nourriture","oral":True,"dose":"20 mg/j → 40 mg/j","halflife":"~7 j","usage":"Relance + bloc périphérique œstrogène"},
    "Anastrozole (Arimidex)":                 {"utilite":"Contrôle œstrogènes","dose_min":"0.25 mg EOD","dose_max":"1 mg EOD","popularite":"★★★★★","dangerosite":"★★★☆☆","demi_vie":"~48 h","notes":"Ne pas sur-doser : E2 trop bas = douleurs articulaires. Cible : 20–30 pg/mL.","timing":"Lendemain injection testo — EOD à partir de S2","oral":True,"dose":"0.5 mg EOD → 1 mg/j","halflife":"~46 h","usage":"Inhibiteur aromatase réversible — lipides impactés"},
    "Exemestane (Aromasin)":                  {"utilite":"IA suicidaire, rebond réduit","dose_min":"12.5 mg EOD","dose_max":"25 mg/j","popularite":"★★★★☆","dangerosite":"★★★☆☆","demi_vie":"~24 h","notes":"Moins de rebond E2. Légèrement anabolique. Départ : 12.5 mg EOD.","timing":"Lendemain injection testo — EOD","oral":True,"dose":"12.5 mg/j ou EOD → 25 mg/j","halflife":"~27 h","usage":"Inhibiteur aromatase irréversible — lipides OK"},
    "Letrozole (Femara)":                     {"utilite":"IA puissant, gynéco urgence","dose_min":"0.5–1 mg EOD","dose_max":"2.5 mg/j","popularite":"★★★☆☆","dangerosite":"★★★★☆","demi_vie":"~2 jours","notes":"Très puissant — risque crash E2. Réserver aux cas résistants. Départ : 0.25 mg EOD.","timing":"EOD — surveiller estradiol toutes les 4 semaines","oral":True,"dose":"0.25–0.5 mg EOD → 2.5 mg/j","halflife":"~2 j","usage":"IA très puissant — crash œstro possible"},
    "Cabergoline (Dostinex)":                 {"utilite":"Anti-prolactine (Tren/Deca)","dose_min":"0.25 mg 2x/sem","dose_max":"0.5 mg 2x/sem","popularite":"★★★★★","dangerosite":"★★☆☆☆","demi_vie":"~65 h","notes":"Obligatoire avec Tren/Deca. Prendre le soir avec nourriture. Départ : 0.25 mg 2x/sem.","timing":"Soir avec nourriture — 2x/semaine","oral":True,"dose":"0.25 mg 2×/sem → 0.5–1 mg 2×/sem","halflife":"~65 h","usage":"Contrôle prolactine — essentiel avec Tren/Deca"},
}

_AROMATIZING_TEST  = {"Testosterone Enanthate","Testosterone Cypionate","Testosterone Propionate","Sustanon 250/300/350","Testosterone Undecanoate (Nebido)"}
_AI_PRODUCTS       = {"Anastrozole (Arimidex)","Exemestane (Aromasin)","Letrozole (Femara)"}
_HCG_PRODUCTS_SET  = {"HCG"}
_PCT_STRICT        = {"Clomiphene (Clomid)","Tamoxifen (Nolvadex)"}
_ORAL_PRODUCTS     = set(CATEGORY_ITEMS.get(2, []))
_ESTER_WASHOUT     = {
    "Testosterone Enanthate":2,"Testosterone Cypionate":2,"Sustanon 250/300/350":2,
    "Testosterone Undecanoate (Nebido)":5,"Boldenone Undecylenate (Equipoise)":3,
    "Nandrolone Decanoate (Deca)":3,"Methenolone Enanthate (Primobolan)":2,
    "Trenbolone Enanthate":2,"Trenbolone Acetate":1,"Trenbolone Hexahydrobenzylcarbonate":3,
    "Drostanolone Enanthate (Masteron E)":2,"Drostanolone Propionate (Masteron P)":1,
    "Cut Stack (mix Tren/Mast/Test)":2,
}
_PCT_NORMAL   = [(1,2,"Clomid 50 mg/j","Nolvadex 20 mg/j"),(3,4,"Clomid 25 mg/j","Nolvadex 10 mg/j")]
_PCT_AGRESSIF = [(1,2,"Clomid 100 mg/j","Nolvadex 40 mg/j"),(3,4,"Clomid 50 mg/j","Nolvadex 20 mg/j"),(5,6,"Clomid 25 mg/j","Nolvadex 10 mg/j")]

_KNOWLEDGE_QUESTIONS = [
    {"q":"Qu'est-ce que la suppression de l'axe HPTA ?","choices":["A — Un effet bénéfique qui augmente la production naturelle de testostérone","B — L'arrêt partiel ou total de la production hormonale naturelle par le cerveau","C — Un simple déséquilibre temporaire sans conséquence","D — Un terme désignant la prise de masse musculaire rapide"],"answer":"B","explication":"La suppression HPTA signifie que l'hypothalamus et l'hypophyse cessent de stimuler les testicules. Sans PCT, cette suppression peut devenir permanente."},
    {"q":"Quelle est la principale conséquence cardiovasculaire des stéroïdes anabolisants ?","choices":["A — Une amélioration de la circulation sanguine","B — Une augmentation du HDL (bon cholestérol)","C — Chute du HDL, hausse du LDL, hypertrophie du ventricule gauche, risque d'infarctus","D — Aucune conséquence documentée sur le cœur"],"answer":"C","explication":"Les AAS sont fortement associés à la cardiomyopathie, des profils lipidiques athérogènes et des morts subites cardiaques."},
    {"q":"Qu'est-ce que l'hépatotoxicité des stéroïdes oraux alkylés en C17-alpha ?","choices":["A — Une toxicité rénale sans gravité","B — Une augmentation temporaire des enzymes hépatiques sans risque","C — Une toxicité hépatique pouvant mener à la peliose, cholestase ou carcinome","D — Un terme marketing sans réalité clinique"],"answer":"C","explication":"Les oraux alkylés (Dianabol, Anadrol, Winstrol…) résistent à la dégradation hépatique, provoquant une charge toxique directe pouvant être irréversible."},
    {"q":"Quel est le rôle du PCT (Post Cycle Therapy) ?","choices":["A — Accélérer la prise de masse après le cycle","B — Relancer l'axe HPTA supprimé pour restaurer la production endogène de testostérone","C — Éliminer les stéroïdes du corps plus rapidement","D — Prévenir uniquement la rétention d'eau"],"answer":"B","explication":"Sans PCT adapté, l'axe HPTA peut rester supprimé des mois ou de façon permanente, entraînant dépression profonde, infertilité, perte musculaire."},
    {"q":"Pourquoi l'usage de stéroïdes avant 21 ans est-il particulièrement dangereux ?","choices":["A — Ce n'est pas plus dangereux qu'après 21 ans","B — L'axe hormonal et les os sont en développement — fermeture prématurée des cartilages, suppression HPTA définitive possible","C — Uniquement à cause des risques d'acné","D — Parce que les effets sont moins visibles à cet âge"],"answer":"B","explication":"Avant 21 ans, le système endocrinien n'est pas mature. Une intervention exogène peut stopper définitivement le développement naturel."},
]

_CONFIRM_PHRASE = "J'AI PRIS MA DÉCISION EN CONNAISSANCE DE CAUSE"


# ══════════════════════════════════════════════════════════════════════════════
#  CLASSE PRINCIPALE — CycleView
# ══════════════════════════════════════════════════════════════════════════════

class CycleView:
    """
    Gère tout l'écran Cycle :
      - État partagé dans self.state (dict mutable)
      - Chaque section est un widget reconstruit via _rebuild_*
      - page.update() appelé après chaque changement
    """

    def __init__(self, page: ft.Page, app_state: dict):
        self.page      = page
        self.app_state = app_state

        # État interne cycle
        self.state: dict = {
            "selected_products": [],   # list[str]
            "product_doses":     {},   # {prod: str}
            "length":            12,
            "preset":            "12 semaines",
            "end_mode":          "PCT",
            "pct_mode":          "Normal",
            "start_date":        "",
            "fin_date":          "",
            "maintenance_dose":  "",
            "note":              "",
        }

        # Contrôles réactifs (gardés pour update ciblé)
        self._fin_label:    Optional[ft.Text]       = None
        self._advice_col:   Optional[ft.Column]     = None
        self._doses_col:    Optional[ft.Column]     = None
        self._hist_col:     Optional[ft.Column]     = None
        self._product_checks: dict[str, ft.Checkbox] = {}  # {prod: checkbox}
        self._dose_fields:  dict[str, ft.TextField] = {}   # {prod: textfield}

        # Catalogue
        self._cat_selected_prod: Optional[str] = None
        self._cat_selected_ref:  dict = {"container": None}
        self._cat_prod_col:      Optional[ft.Column] = None
        self._cat_detail_name:   Optional[ft.Text] = None
        self._cat_detail_dose:   Optional[ft.Text] = None
        self._cat_detail_hl:     Optional[ft.Text] = None
        self._cat_detail_use:    Optional[ft.Text] = None
        self._cat_btn_modifier:  Optional[ft.ElevatedButton] = None
        self._cat_btn_supprimer: Optional[ft.ElevatedButton] = None

        # Paramètres PCT / Maintenance
        self._pct_zone:              Optional[ft.Column]        = None
        self._maint_field:           Optional[ft.TextField]     = None
        self._pct_clomid_j14:        Optional[ft.TextField]     = None
        self._pct_nolvadex_j14:      Optional[ft.TextField]     = None
        self._pct_clomid_j28:        Optional[ft.TextField]     = None
        self._pct_nolvadex_j28:      Optional[ft.TextField]     = None
        self._pct_note:              Optional[ft.Text]          = None
        self._btn_voir_selection:    Optional[ft.ElevatedButton] = None

        # Historique — sélection
        self._hist_selected_row: Optional[dict] = None
        self._hist_selected_ref: dict = {"container": None}

        # Planning d'injections — config jours 2x/sem par produit
        # {produit: (wd1, wd2)}  ex: {"Test E": (0, 3)}
        self.state["days_2x_config"] = {}
        self._inj_planner_col: Optional[ft.Column] = None
        self._inj_preview_col: Optional[ft.Column] = None

        # Conteneur racine scrollable
        self.root_col     = ft.Column(spacing=0, expand=True)
        self._main_col    = self.root_col   # alias — _build_all écrit dans _main_col
        self._modal_layer = None            # modal via page.overlay
        self._build_all()
        self._load_last_cycle()

    # ── Point d'entrée public ────────────────────────────────────────────────

    def get_view(self) -> ft.Column:
        return self.root_col

    # ══════════════════════════════════════════════════════════════════════════
    #  CONSTRUCTION UI
    # ══════════════════════════════════════════════════════════════════════════

    def _build_all(self):
        self._main_col.controls.clear()

        # Hero
        self._main_col.controls.append(self._build_hero())

        # ── Colonnes dynamiques (initialisées avant les accordéons) ──────────
        self._doses_col  = ft.Column(spacing=8)
        self._advice_col = ft.Column(spacing=6)
        self._hist_col   = ft.Column(spacing=4)
        self._inj_planner_col = ft.Column(spacing=8)
        self._inj_preview_col = None

        # Pré-remplissage initial
        self._rebuild_doses()
        self._rebuild_advice()
        self._rebuild_history()
        self._rebuild_injection_planner()

        # ── Accordéons Ghost ─────────────────────────────────────────────────
        accordions = [
            self._ghost_accord(
                num=1, title="Sélection des produits",
                status_fn=lambda: f"{len(self.state['selected_products'])} produit(s)" if self.state['selected_products'] else "À configurer",
                content_fn=self._build_product_selector_inner,
                open=True,
            ),
            self._ghost_accord(
                num=2, title="Doses par produit",
                status_fn=lambda: f"{len(self.state['product_doses'])} dose(s) saisie(s)" if self.state['product_doses'] else "À configurer",
                content_fn=lambda: self._doses_col,
                open=False,
            ),
            self._ghost_accord(
                num=3, title="Paramètres du cycle",
                status_fn=lambda: f"{self.state['length']} sem · {self.state['end_mode']}",
                content_fn=self._build_params_inner,
                open=False,
            ),
            self._ghost_accord(
                num=4, title="Planning d'injections",
                status_fn=lambda: f"{len(self.state['selected_products'])} produit(s) planifié(s)" if self.state['selected_products'] else "Configurez vos produits",
                content_fn=lambda: self._inj_planner_col,
                open=False,
            ),
            self._ghost_accord(
                num=5, title="Résumé & recommandations",
                status_fn=lambda: f"{len(self.state['selected_products'])} produits analysés" if self.state['selected_products'] else "Sélectionnez des produits",
                content_fn=lambda: self._advice_col,
                open=False,
            ),
            self._ghost_accord(
                num=6, title="Notes",
                status_fn=lambda: "Note ajoutée" if self.state.get("note") else "Optionnel",
                content_fn=self._build_notes_inner,
                open=False,
            ),
        ]

        for ac in accordions:
            self._main_col.controls.append(ac)

        # Historique (sans numéro)
        self._main_col.controls.append(
            self._ghost_accord(
                num=None, title="Historique des cycles",
                status_fn=lambda: "",
                content_fn=lambda: self._hist_col,
                open=False,
            )
        )
        # Catalogue des produits (sans numéro)
        self._main_col.controls.append(
            self._ghost_accord(
                num=None, title="Catalogue des produits",
                status_fn=lambda: f"{sum(len(v) for v in CATEGORY_ITEMS.values())} produits · {len(CATEGORIES)} catégories",
                content_fn=self._build_catalogue_inner,
                open=False,
            )
        )
        self._main_col.controls.append(ft.Container(height=20))

    # ── Catalogue des produits ────────────────────────────────────────────────


    _CAT_COLORS = {
        0: "#e8c96e",   # or — Base Test
        1: "#6eb5e8",   # bleu — injectables
        2: "#e86e6e",   # rouge — oraux
        3: "#a0e86e",   # vert — peptides
        4: "#c86ee8",   # violet — hormones
        5: "#6ee8b5",   # turquoise — PCT
        6: "#e8906e",   # orange — IA/AP
    }

    def _build_catalogue_inner(self) -> ft.Container:
        cat_cols: list = []
        cat_refs: list[dict] = []

        # ── Fiche produit ─────────────────────────────────────────────────────
        self._cat_detail_name = ft.Text("Sélectionne un produit", size=13,
                                        color=TEXT_ACCENT, weight=ft.FontWeight.BOLD)
        self._cat_detail_dose = ft.Text("", size=12, color=TEXT)
        self._cat_detail_hl   = ft.Text("", size=12, color=TEXT_MUTED)
        self._cat_detail_use  = ft.Text("", size=12, color=TEXT_SUB)
        detail_box = ft.Container(
            content=ft.Column([
                mk_title("  🔎  FICHE PRODUIT"),
                mk_sep(),
                ft.Container(
                    content=ft.Column([
                        self._cat_detail_name,
                        self._cat_detail_dose,
                        self._cat_detail_hl,
                        self._cat_detail_use,
                    ], spacing=4),
                    padding=ft.Padding.all(10),
                ),
            ]),
            bgcolor=BG_CARD2, border_radius=10,
            margin=ft.Margin.symmetric(horizontal=12),
            padding=ft.Padding.symmetric(vertical=8),
        )

        self._cat_selected_ref = {"container": None}

        def _show_detail(prod: str):
            info = self._get_product_info(prod)
            self._cat_detail_name.value = prod
            self._cat_detail_dose.value = f"Dosage : {info.get('dose', '—')}"
            self._cat_detail_hl.value   = f"Demi-vie : {info.get('halflife', '—')}"
            self._cat_detail_use.value  = f"Usage : {info.get('usage', '—')}"
            self._safe_update()

        def _make_item(prod: str):
            item_ref = ft.Ref[ft.Container]()
            is_custom = self._is_custom_product(prod)
            def _click(e, p=prod, r=item_ref):
                prev = self._cat_selected_ref["container"]
                if prev and prev.current:
                    prev.current.bgcolor = "transparent"
                if r.current:
                    r.current.bgcolor = ACCENT_DIM
                self._cat_selected_ref["container"] = r
                self._cat_selected_prod = p
                self._safe_update()
                _show_detail(p)
            return ft.Container(
                content=ft.Row([
                    ft.Text(f"  {prod}", size=12, color=TEXT, expand=True),
                    ft.Text("✦", size=9, color=ACCENT, tooltip="Personnalisé") if is_custom else ft.Container(width=0),
                ]),
                padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                border_radius=6, ink=True, bgcolor="transparent",
                ref=item_ref, on_click=_click,
            )

        # ── Sections par catégorie ────────────────────────────────────────────
        def _build_cat_sections():
            cat_cols.clear()
            cat_refs.clear()
            all_prods = self._get_all_products()
            for cat_id, cat_name in CATEGORIES.items():
                color = self._CAT_COLORS.get(cat_id, TEXT_SUB)
                base_items  = CATEGORY_ITEMS.get(cat_id, [])
                extra_items = [p for p in self._load_custom_products()
                               if p.get("categorie_id") == cat_id]
                extra_names = [p["nom"] for p in extra_items]
                items = base_items + extra_names
                _state    = {"open": False}
                _icon_ref = ft.Ref[ft.Text]()
                _body_ref = ft.Ref[ft.Column]()

                def _make_toggle(s, ir, br):
                    def _toggle(e=None):
                        s["open"] = not s["open"]
                        ir.current.value   = "▼" if s["open"] else "▶"
                        br.current.visible = s["open"]
                        try: e.page.update()
                        except Exception: pass
                    return _toggle

                item_rows = [_make_item(p) for p in items]
                body_col  = ft.Column(item_rows, spacing=0, ref=_body_ref, visible=False)
                header = ft.Container(
                    content=ft.Row([
                        ft.Text("▶", size=11, color=color,
                                weight=ft.FontWeight.BOLD, ref=_icon_ref),
                        ft.Text(f" {cat_name}", size=11, color=color,
                                weight=ft.FontWeight.BOLD, expand=True),
                        ft.Text(str(len(items)), size=10, color=TEXT_MUTED),
                    ], spacing=4),
                    bgcolor=BG_CARD2, border_radius=6,
                    padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                    ink=True,
                    on_click=_make_toggle(_state, _icon_ref, _body_ref),
                )
                cat_refs.append({"header": header, "body": body_col,
                                 "items": items, "state": _state,
                                 "icon": _icon_ref, "body_ref": _body_ref})
                cat_cols.extend([header, body_col])

        _build_cat_sections()
        self._cat_prod_col = ft.Column(cat_cols, spacing=4)

        # ── Recherche ─────────────────────────────────────────────────────────
        def _on_search(e):
            q = e.control.value.lower().strip()
            for entry in cat_refs:
                vis = [p for p in entry["items"] if q in p.lower()] if q else entry["items"]
                entry["body_ref"].current.controls = [_make_item(p) for p in vis]
                open_it = bool(q and vis)
                entry["state"]["open"] = open_it
                entry["icon"].current.value   = "▼" if open_it else "▶"
                entry["body_ref"].current.visible = open_it if q else False
            try: e.page.update()
            except Exception: pass

        search_field = mk_entry(
            label="🔍 Rechercher un produit", hint="nom...", width=280,
            on_change=_on_search,
        )

        # ── Boutons CRUD ──────────────────────────────────────────────────────
        self._cat_btn_modifier  = mk_btn("✏ Modifier",   self._on_cat_edit,
                                          color=ACCENT,  hover=ACCENT_HOVER, width=130, height=38)
        self._cat_btn_supprimer = mk_btn("🗑 Supprimer", self._on_cat_delete,
                                          color=DANGER,  hover=DANGER_HVR,   width=130, height=38)
        btn_ajouter = mk_btn("➕ Nouveau",  self._on_cat_add,
                             color=SUCCESS, hover=SUCCESS_HVR, width=150, height=38)

        return ft.Container(
            content=ft.Column([
                ft.Container(content=search_field,
                             padding=ft.Padding.symmetric(horizontal=12, vertical=8)),
                ft.Container(content=self._cat_prod_col, expand=True,
                             padding=ft.Padding.symmetric(horizontal=12)),
                detail_box,
                ft.Container(
                    content=ft.Row([btn_ajouter, self._cat_btn_modifier, self._cat_btn_supprimer],
                                   spacing=8, wrap=True),
                    padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                ),
            ], spacing=0),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.Border.all(1, BORDER),
            margin=ft.Margin.symmetric(horizontal=12, vertical=6),
        )

    # ── Helpers catalogue ─────────────────────────────────────────────────────

    def _custom_products_path(self) -> str:
        """Conservé pour la migration — retourne le chemin du JSON legacy."""
        from data.utils import USERS_DIR
        import os
        user = self.app_state.get("current_user", "default") or "default"
        folder = os.path.join(USERS_DIR, user)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "custom_products.json")

    def _migrate_json_if_needed(self):
        """Migre custom_products.json → DB si le fichier existe encore."""
        json_path = self._custom_products_path()
        import os
        if os.path.exists(json_path):
            _db.custom_products_migrate_from_json(self.app_state, json_path)

    def _load_custom_products(self) -> list:
        """Charge les produits personnalisés depuis la DB."""
        self._migrate_json_if_needed()
        return _db.custom_products_get_all(self.app_state)

    def _save_custom_products(self, prods: list):
        """Compatibilité — remplacé par upsert/delete individuels.
        Synchronise la liste complète : supprime les absents, upserte les présents.
        """
        existing = {p["nom"] for p in _db.custom_products_get_all(self.app_state)}
        new_noms = {p["nom"] for p in prods}
        for nom in existing - new_noms:
            _db.custom_products_delete(self.app_state, nom)
        for p in prods:
            _db.custom_products_upsert(
                self.app_state,
                nom          = p["nom"],
                categorie_id = int(p.get("categorie_id", 0)),
                dose         = p.get("dose", ""),
                halflife     = p.get("halflife", ""),
                usage        = p.get("usage", ""),
                notes        = p.get("notes", ""),
            )

    def _get_all_products(self) -> list[str]:
        base = [p for items in CATEGORY_ITEMS.values() for p in items]
        custom_names = [p["nom"] for p in self._load_custom_products()]
        return base + custom_names

    def _is_custom_product(self, nom: str) -> bool:
        return any(p["nom"] == nom for p in self._load_custom_products())

    def _get_product_info(self, nom: str) -> dict:
        if nom in PRODUCT_INFO:
            return PRODUCT_INFO[nom]
        row = _db.custom_products_get_one(self.app_state, nom)
        if row:
            return {"dose": row.get("dose", "—"),
                    "halflife": row.get("halflife", "—"),
                    "usage": row.get("usage", "—")}
        return {}

    def _rebuild_catalogue(self):
        """Reconstruit la liste produits après CRUD."""
        if self._cat_prod_col is None:
            return
        self._cat_prod_col.controls.clear()
        for cat_id, cat_name in CATEGORIES.items():
            color = self._CAT_COLORS.get(cat_id, TEXT_SUB)
            base_items  = CATEGORY_ITEMS.get(cat_id, [])
            extra_names = [p["nom"] for p in self._load_custom_products()
                           if p.get("categorie_id") == cat_id]
            items = base_items + extra_names
            _state    = {"open": False}
            _icon_ref = ft.Ref[ft.Text]()
            _body_ref = ft.Ref[ft.Column]()

            def _make_toggle(s, ir, br):
                def _toggle(e=None):
                    s["open"] = not s["open"]
                    ir.current.value   = "▼" if s["open"] else "▶"
                    br.current.visible = s["open"]
                    try: e.page.update()
                    except Exception: pass
                return _toggle

            def _make_item(prod):
                item_ref = ft.Ref[ft.Container]()
                is_custom = self._is_custom_product(prod)
                def _click(e, p=prod, r=item_ref):
                    prev = self._cat_selected_ref["container"]
                    if prev and prev.current:
                        prev.current.bgcolor = "transparent"
                    if r.current:
                        r.current.bgcolor = ACCENT_DIM
                    self._cat_selected_ref["container"] = r
                    self._cat_selected_prod = p
                    info = self._get_product_info(p)
                    if self._cat_detail_name:
                        self._cat_detail_name.value = p
                        self._cat_detail_dose.value = f"Dosage : {info.get('dose', '—')}"
                        self._cat_detail_hl.value   = f"Demi-vie : {info.get('halflife', '—')}"
                        self._cat_detail_use.value  = f"Usage : {info.get('usage', '—')}"
                    self._safe_update()
                return ft.Container(
                    content=ft.Row([
                        ft.Text(f"  {prod}", size=12, color=TEXT, expand=True),
                        ft.Text("✦", size=9, color=ACCENT, tooltip="Personnalisé") if is_custom else ft.Container(width=0),
                    ]),
                    padding=ft.Padding.symmetric(horizontal=8, vertical=6),
                    border_radius=6, ink=True, bgcolor="transparent",
                    ref=item_ref, on_click=_click,
                )

            body_col = ft.Column([_make_item(p) for p in items],
                                 spacing=0, ref=_body_ref, visible=False)
            header = ft.Container(
                content=ft.Row([
                    ft.Text("▶", size=11, color=color,
                            weight=ft.FontWeight.BOLD, ref=_icon_ref),
                    ft.Text(f" {cat_name}", size=11, color=color,
                            weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text(str(len(items)), size=10, color=TEXT_MUTED),
                ], spacing=4),
                bgcolor=BG_CARD2, border_radius=6,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                ink=True,
                on_click=_make_toggle(_state, _icon_ref, _body_ref),
            )
            self._cat_prod_col.controls.extend([header, body_col])
        self._safe_update()

    # ── CRUD catalogue ────────────────────────────────────────────────────────

    def _on_cat_add(self, e=None):
        self._open_product_modal(None)

    def _on_cat_edit(self, e=None):
        prod = self._cat_selected_prod
        if not prod:
            self._snack("Sélectionne d'abord un produit.", WARNING); return
        if not self._is_custom_product(prod):
            self._snack("Les produits de base ne peuvent pas être modifiés directement — une copie personnalisée sera créée.", WARNING)
        info = self._get_product_info(prod)
        # Cherche le dict complet si custom
        full = next((p for p in self._load_custom_products() if p["nom"] == prod), None)
        if full is None:
            # Crée un dict à partir des infos intégrées pour préremplir
            full = {"nom": prod, "categorie_id": self._cat_id_for(prod),
                    "dose": info.get("dose",""), "halflife": info.get("halflife",""),
                    "usage": info.get("usage",""), "notes": "", "_custom": True}
        self._open_product_modal(full)

    def _on_cat_delete(self, e=None):
        prod = self._cat_selected_prod
        if not prod:
            self._snack("Sélectionne d'abord un produit.", WARNING); return
        if not self._is_custom_product(prod):
            self._snack("Les produits de base ne peuvent pas être supprimés.", WARNING); return
        customs = self._load_custom_products()
        customs = [p for p in customs if p["nom"] != prod]
        self._save_custom_products(customs)
        self._cat_selected_prod = None
        if self._cat_detail_name:
            self._cat_detail_name.value = "Sélectionne un produit"
            self._cat_detail_dose.value = ""
            self._cat_detail_hl.value   = ""
            self._cat_detail_use.value  = ""
        self._rebuild_catalogue()
        self._snack("✔ Produit supprimé.", SUCCESS)

    def _cat_id_for(self, nom: str) -> int:
        for cat_id, items in CATEGORY_ITEMS.items():
            if nom in items:
                return cat_id
        return 0

    def _open_product_modal(self, prod: dict | None):
        """AlertDialog — même pattern que les autres modals de cycle.py."""
        is_edit = prod is not None

        def _mk_field(label, value="", **kw):
            return ft.TextField(
                label=label, value=value,
                bgcolor=BG_INPUT, border_color=BORDER,
                focused_border_color=ACCENT, color=TEXT,
                label_style=ft.TextStyle(color=TEXT_SUB, size=11),
                border_radius=8, text_size=13, **kw)

        f_nom  = _mk_field("Nom *",    prod["nom"]            if prod else "")
        f_dose = _mk_field("Dosage",   prod.get("dose","")    if prod else "")
        f_hl   = _mk_field("Demi-vie", prod.get("halflife","") if prod else "")
        f_use  = _mk_field("Usage",    prod.get("usage","")   if prod else "")
        f_note = _mk_field("Notes",    prod.get("notes","")   if prod else "",
                           multiline=True, min_lines=2, max_lines=3)

        cat_options = [ft.dropdown.Option(key=str(cid), text=cname)
                       for cid, cname in CATEGORIES.items()]
        current_cat = str(prod.get("categorie_id", 0)) if prod else "0"
        f_cat = ft.Dropdown(
            label="Catégorie *", value=current_cat,
            options=cat_options,
            bgcolor=BG_INPUT, border_color=BORDER,
            focused_border_color=ACCENT, color=TEXT,
            label_style=ft.TextStyle(color=TEXT_SUB, size=11),
            border_radius=8, text_size=13,
        )

        dlg = ft.AlertDialog(modal=True)

        def _close(ev=None):
            dlg.open = False
            self.page.update()

        def _save(ev=None):
            nom = f_nom.value.strip()
            if not nom:
                self._snack("Le nom est obligatoire.", DANGER); return
            try: cat_id = int(f_cat.value)
            except Exception: cat_id = 0
            old_nom = prod["nom"] if prod else None
            if old_nom and old_nom != nom:
                _db.custom_products_delete(self.app_state, old_nom)
            _db.custom_products_upsert(
                self.app_state,
                nom          = nom,
                categorie_id = cat_id,
                dose         = f_dose.value.strip(),
                halflife     = f_hl.value.strip(),
                usage        = f_use.value.strip(),
                notes        = f_note.value.strip(),
            )
            self._cat_selected_prod = nom
            _close()
            self._rebuild_catalogue()
            self._snack(f"✔ Produit « {nom} » sauvegardé.", SUCCESS)

        dlg.title = ft.Text(
            "✏ Modifier le produit" if is_edit else "➕ Nouveau produit",
            color=ACCENT, weight=ft.FontWeight.BOLD, size=15,
        )
        dlg.content = ft.Container(
            content=ft.Column([
                f_nom, f_cat, f_dose,
                ft.Row([f_hl], spacing=8),
                f_use, f_note,
            ], spacing=10, tight=True),
            width=340,
            padding=ft.padding.only(top=8),
        )
        dlg.actions = [
            ft.ElevatedButton(
                content=ft.Text("✕ Annuler", size=13, color=TEXT,
                                weight=ft.FontWeight.BOLD),
                bgcolor=GRAY, on_click=_close, width=130, height=42,
            ),
            ft.ElevatedButton(
                content=ft.Text("💾 Sauvegarder", size=13, color=TEXT,
                                weight=ft.FontWeight.BOLD),
                bgcolor=SUCCESS, on_click=_save, width=170, height=42,
            ),
        ]
        dlg.bgcolor = BG_CARD
        dlg.shape   = ft.RoundedRectangleBorder(radius=16)

        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _build_inline_timeline(self) -> ft.Container:
        """Barre timeline Cycle → Washout → PCT avec légende — depuis self.state."""
        import datetime as _dt

        n_weeks   = self.state.get("length", 12)
        start_str = self.state.get("start_date", "")
        end_mode  = self.state.get("end_mode", "PCT")
        washout_w = 2
        pct_w     = 4 if end_mode == "PCT" else 0
        total_w   = n_weeks + washout_w + pct_w

        debut = None
        try:
            debut = _dt.datetime.strptime(start_str, "%d/%m/%Y").date()
        except Exception:
            pass

        today    = _dt.date.today()
        days_in  = (today - debut).days if debut else -1
        cur_week = days_in / 7 if days_in >= 0 else -1

        phases = [("CYCLE", n_weeks, "#1a4a1a", "#22c55e")]
        if washout_w:
            phases.append(("WASH", washout_w, "#2a1a00", "#f59e0b"))
        if pct_w:
            phases.append(("PCT", pct_w, "#0a0d2b", "#3b82f6"))

        bar_segments = []
        week_cursor  = 0
        for label, n_w, bg_col, txt_col in phases:
            is_active = (week_cursor <= cur_week < week_cursor + n_w)
            bar_segments.append(ft.Container(
                content=ft.Text(label, size=9, color=txt_col,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.CENTER),
                bgcolor=bg_col, expand=round(n_w * 10), height=28,
                alignment=ft.Alignment(0, 0),
                border=ft.border.all(2, txt_col) if is_active else None,
            ))
            week_cursor += n_w

        week_labels = ft.Row([
            ft.Text("S0", size=8, color=TEXT_MUTED),
            ft.Container(expand=True),
            ft.Text(f"S{n_weeks}", size=8, color=TEXT_MUTED),
            ft.Container(expand=True),
            ft.Text(f"S{n_weeks + washout_w}", size=8, color=TEXT_MUTED),
            *([] if not pct_w else [
                ft.Container(expand=True),
                ft.Text(f"S{total_w}", size=8, color=TEXT_MUTED),
            ]),
        ])

        if debut:
            fin_cycle = debut + _dt.timedelta(weeks=n_weeks)
            pct_start = debut + _dt.timedelta(weeks=n_weeks + washout_w)
            end_date  = debut + _dt.timedelta(weeks=total_w)
            if days_in < 0:
                phase_txt, phase_col = "Cycle pas encore démarré", TEXT_MUTED
            elif days_in < n_weeks * 7:
                wk   = days_in // 7 + 1
                left = n_weeks * 7 - days_in
                phase_txt, phase_col = f"CYCLE — Semaine {wk}/{n_weeks}  ·  {left}j restants", "#22c55e"
            elif days_in < (n_weeks + washout_w) * 7:
                phase_txt, phase_col = "WASHOUT — Arrêt des produits", "#f59e0b"
            else:
                pct_day = days_in - (n_weeks + washout_w) * 7
                phase_txt, phase_col = f"PCT — Jour {pct_day + 1}", "#3b82f6"
            legende = ft.Column([
                ft.Text(f"📍  {phase_txt}", size=11, color=phase_col,
                        weight=ft.FontWeight.BOLD),
                ft.Text(
                    f"Début : {debut:%d/%m/%Y}  ·  Fin cycle : {fin_cycle:%d/%m/%Y}"
                    + (f"  ·  PCT : {pct_start:%d/%m/%Y}  ·  Fin PCT : {end_date:%d/%m/%Y}"
                       if pct_w else ""),
                    size=10, color=TEXT_MUTED,
                ),
            ], spacing=4)
        else:
            legende = ft.Column([
                ft.Text("Configurez une date de début pour voir la légende",
                        size=11, color=TEXT_MUTED, italic=True),
            ])

        return ft.Container(
            content=ft.Column([
                ft.Row(bar_segments, spacing=0),
                ft.Container(height=4),
                week_labels,
                ft.Container(height=6),
                legende,
            ], spacing=0),
            bgcolor=BG_CARD2, border_radius=10,
            padding=ft.Padding.all(12),
            margin=ft.Margin.symmetric(horizontal=12, vertical=6),
        )

    # ── Planning d'injections ─────────────────────────────────────────────────

    def _rebuild_injection_planner(self):
        """Reconstruit la liste fréquences + aperçu selon les produits en cours."""
        if not hasattr(self, "_inj_planner_col") or self._inj_planner_col is None:
            return
        self._inj_planner_col.controls.clear()
        selected = self.state.get("selected_products", [])

        if not selected:
            self._inj_planner_col.controls.append(
                ft.Text("Sélectionnez des produits d'abord.", size=12, color=TEXT_MUTED)
            )
            self._safe_update()
            return

        combo_options = [
            ft.dropdown.Option(key=f"{wd1},{wd2}", text=label)
            for wd1, wd2, label in _inj.COMBOS_2X_SEM
        ]

        FREQ_LABELS = {
            "ED": "Chaque jour", "EOD": "Tous les 2 jours",
            "E3D": "Tous les 3 jours", "2x/sem": "2x/semaine",
            "1x/sem": "1x/semaine", "PCT": "Post-cycle (J+14)",
            "10sem": "Toutes les 10 sem",
        }

        # Produits dont le timing dépend de la testo
        HCG_PRODS = {"HCG"}
        IA_PRODS  = {"Anastrozole (Arimidex)", "Exemestane (Aromasin)", "Letrozole (Femara)"}
        # Vérifie si une testo de base est sélectionnée
        testo_wdays = _inj._testo_days(self.state.get("days_2x_config", {}))
        has_testo = bool(testo_wdays)

        self._inj_planner_col.controls.append(mk_title("  💉  FRÉQUENCES D'INJECTION"))
        self._inj_planner_col.controls.append(mk_sep())

        for prod in selected:
            freq = _inj.get_freq(prod)

            # HCG — timing automatique basé sur la testo
            if prod in HCG_PRODS:
                note = "⚡ Veille de la testo (auto)" if has_testo else "⚡ Veille testo — configurez la testo d'abord"
                self._inj_planner_col.controls.append(ft.Row([
                    ft.Text(f"  {prod}", size=12, color=TEXT, expand=True),
                    ft.Text(note, size=11, color=WARNING),
                ], spacing=8))
                continue

            # IA — timing automatique lendemain testo
            if prod in IA_PRODS:
                note = "⏱ Lendemain testo (auto)" if has_testo else "⏱ Lendemain testo — configurez la testo d'abord"
                self._inj_planner_col.controls.append(ft.Row([
                    ft.Text(f"  {prod}", size=12, color=TEXT, expand=True),
                    ft.Text(note, size=11, color=WARNING),
                ], spacing=8))
                continue

            # PCT — démarrage J+14 post-cycle, ED
            if freq == _inj.FREQ_PCT:
                self._inj_planner_col.controls.append(ft.Row([
                    ft.Text(f"  {prod}", size=12, color=TEXT, expand=True),
                    ft.Text("Post-cycle J+14 · chaque jour", size=11, color=PURPLE),
                ], spacing=8))
                continue

            if freq == _inj.FREQ_2X_SEM:
                cur = self.state["days_2x_config"].get(prod, (0, 3))
                cur_key = f"{cur[0]},{cur[1]}"
                dd = ft.Dropdown(
                    value=cur_key, options=combo_options,
                    bgcolor=BG_INPUT, border_color=BORDER,
                    focused_border_color=ACCENT, color=TEXT,
                    label_style=ft.TextStyle(color=TEXT_SUB, size=11),
                    border_radius=8, text_size=12, width=200,
                )
                def _on_combo(e, p=prod, d=dd):
                    parts = (d.value or "0,3").split(",")
                    self.state["days_2x_config"][p] = (int(parts[0]), int(parts[1]))
                    self._rebuild_injection_planner()  # met à jour notes HCG/IA
                    self._rebuild_injection_preview()
                dd.on_select = _on_combo
                self._inj_planner_col.controls.append(ft.Row([
                    ft.Text(f"  {prod}", size=12, color=TEXT, expand=True),
                    dd,
                ], spacing=8))
            else:
                self._inj_planner_col.controls.append(ft.Row([
                    ft.Text(f"  {prod}", size=12, color=TEXT, expand=True),
                    ft.Text(FREQ_LABELS.get(freq, freq), size=11, color=TEXT_MUTED),
                ], spacing=8))

        # Aperçu
        self._inj_planner_col.controls.append(ft.Container(height=12))
        self._inj_planner_col.controls.append(mk_title("  📅  APERÇU 3 PROCHAINS JOURS"))
        self._inj_planner_col.controls.append(mk_sep())
        self._inj_preview_col = ft.Column(spacing=4)
        self._rebuild_injection_preview()
        self._inj_planner_col.controls.append(self._inj_preview_col)
        self._safe_update()

    def _rebuild_injection_preview(self):
        """Met à jour l'aperçu des 3 prochains jours d'injections."""
        if not hasattr(self, "_inj_preview_col") or self._inj_preview_col is None:
            return
        self._inj_preview_col.controls.clear()

        selected = self.state.get("selected_products", [])
        doses    = self.state.get("product_doses", {})
        start_str = self.state.get("start_date", "")
        n_weeks  = self.state.get("length", 12)
        days_2x  = self.state.get("days_2x_config", {})

        try:
            start = datetime.datetime.strptime(start_str, "%d/%m/%Y").date()
        except Exception:
            start = datetime.date.today()

        products_doses = {p: doses.get(p, "—") for p in selected}

        # Si pas de config 2x/sem, appliquer lundi/jeudi par défaut
        for prod in selected:
            if _inj.get_freq(prod) == _inj.FREQ_2X_SEM and prod not in days_2x:
                days_2x[prod] = (0, 3)

        planning = _inj.get_next_injections(
            products_doses, start, n_weeks, days_2x, days_ahead=3
        )

        JOURS_FR_LONG = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
        today = datetime.date.today()

        if not planning:
            self._inj_preview_col.controls.append(
                ft.Text("Aucune injection dans les 3 prochains jours.", size=11, color=TEXT_MUTED)
            )
        else:
            for date, items in sorted(planning.items()):
                is_today = (date == today)
                day_label = ("Aujourd'hui" if is_today
                             else f"{JOURS_FR_LONG[date.weekday()]} {date.strftime('%d/%m')}")
                day_color = SUCCESS if is_today else ACCENT

                self._inj_preview_col.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Text(day_label, size=12, color=day_color,
                                    weight=ft.FontWeight.BOLD),
                            *[ft.Row([
                                ft.Text(f"  💉 {it['product']}", size=11, color=TEXT, expand=True),
                                ft.Text(it['dose'], size=11, color=TEXT_MUTED),
                                ft.Text(f"[{it['freq']}]{it.get('timing_note','')}", size=10,
                                        color=WARNING if it.get('timing_note') else TEXT_SUB),
                            ], spacing=6) for it in items],
                        ], spacing=3),
                        bgcolor=BG_CARD2 if is_today else "transparent",
                        border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                        border=ft.border.all(1, SUCCESS) if is_today else None,
                    )
                )

        self._safe_update()

    def _ghost_accord(self, num: int, title: str, status_fn, content_fn, open: bool) -> ft.Container:
        """Accordéon style Ghost — numéro + titre + status + flèche."""
        body_ref   = ft.Ref[ft.Container]()
        arrow_ref  = ft.Ref[ft.Text]()
        num_ref    = ft.Ref[ft.Container]()
        state      = {"open": open}

        # Couleur numéro selon état
        num_bg   = ACCENT if open else BG_CARD2
        num_col  = "#000000" if open else TEXT_MUTED

        num_box = ft.Container(
            content=ft.Text(str(num) if num is not None else "", size=13, color=num_col,
                            weight=ft.FontWeight.BOLD),
            width=28 if num is not None else 0, height=28, border_radius=8,
            bgcolor=num_bg if num is not None else "transparent",
            alignment=ft.Alignment(0, 0),
            ref=num_ref,
            visible=num is not None,
        )

        status_text = ft.Text(
            status_fn() if callable(status_fn) else status_fn,
            size=11, color=TEXT_MUTED if not open else SUCCESS,
        )

        def _toggle(e=None):
            state["open"] = not state["open"]
            body_ref.current.visible = state["open"]
            arrow_ref.current.value  = "▼" if state["open"] else "▶"
            if num is not None and num_ref.current:
                num_ref.current.bgcolor  = ACCENT if state["open"] else BG_CARD2
                num_ref.current.content.color = "#000000" if state["open"] else TEXT_MUTED
            # Refresh status
            try:
                status_text.value = status_fn()
                status_text.color = SUCCESS if state["open"] else TEXT_MUTED
            except Exception:
                pass
            try: e.page.update()
            except Exception: pass

        header = ft.Container(
            content=ft.Row([
                num_box,
                ft.Column([
                    ft.Text(title, size=15,
                            color=ACCENT if num is not None else ACCENT,
                            weight=ft.FontWeight.BOLD),
                    status_text,
                ], spacing=1, expand=True),
                ft.Text("▼" if open else "▶", size=12, color=ACCENT, ref=arrow_ref),
            ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=_toggle,
            bgcolor=BG_CARD,
            padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        )

        # Construire le contenu
        try:
            inner = content_fn()
        except Exception as _err:
            import traceback; traceback.print_exc()
            inner = ft.Text(f"Erreur : {_err}", color=DANGER, size=12)

        body = ft.Container(
            content=inner if isinstance(inner, ft.Control) else ft.Column([inner]),
            visible=open,
            ref=body_ref,
            bgcolor=BG_CARD,
            padding=ft.Padding.only(left=16, right=16, bottom=16),
        )

        return ft.Container(
            content=ft.Column([header, body], spacing=0),
            bgcolor=BG_CARD,
            border_radius=R_CARD,
            border=ft.Border.all(1, ACCENT + "44" if open else BORDER),
            margin=ft.Margin.only(left=12, right=12, bottom=3),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    def _build_hero(self) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("💉 CYCLE HORMONAL", size=22, color=ACCENT,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    mk_badge("RESTRICTED", color="#3a0000", text_color=DANGER),
                ]),
                ft.Text("Planificateur de cycle — informations médicales et pharmacologiques",
                        size=11, color=TEXT_MUTED),
            ], spacing=4),
            bgcolor=BG_CARD,
            padding=ft.Padding.symmetric(horizontal=20, vertical=16),
            margin=ft.Margin.only(bottom=3),
        )

    # ── BLOC 1 : Sélection produits ──────────────────────────────────────────

    def _build_product_selector_inner(self) -> ft.Column:
        """Contenu sélection produits — retourne Column pour accordéon Ghost."""
        cat_sections = []
        self._product_checks = {}

        for cat_id, cat_name in CATEGORIES.items():
            items = CATEGORY_ITEMS.get(cat_id, [])
            checks = []
            for prod in items:
                cb = ft.Checkbox(
                    label=prod, value=False,
                    fill_color={ft.ControlState.SELECTED: ACCENT},
                    label_style=ft.TextStyle(color=TEXT, size=12),
                    on_change=lambda e, p=prod: self._on_product_toggle(p, e.control.value),
                )
                self._product_checks[prod] = cb
                checks.append(cb)

            cat_sections.append(
                ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Text(cat_name, size=11, color=ACCENT_GLOW,
                                            weight=ft.FontWeight.BOLD),
                            bgcolor=BG_CARD2, border_radius=6,
                            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                        ),
                        ft.Column(checks, spacing=2),
                    ], spacing=6),
                    padding=ft.Padding.only(bottom=10),
                )
            )

        preset_dd = mk_dropdown(
            "Preset", ["12 semaines", "16 semaines", "Premier Cycle", "Personnalisé"],
            value="12 semaines", width=200,
            on_change=lambda e: self._on_preset_change(e.control.value),
        )

        return ft.Column([
            ft.Container(content=preset_dd, padding=ft.Padding.only(bottom=10)),
            ft.Container(
                content=ft.Column(cat_sections, spacing=4, scroll=ft.ScrollMode.AUTO),
                height=340,
            ),
        ], spacing=4)

    # ── BLOC 2 : Paramètres cycle ────────────────────────────────────────────

    def _build_params_inner(self) -> ft.Column:
        """Contenu paramètres cycle — retourne Column pour accordéon Ghost."""
        self._length_field = mk_entry(
            label="Durée (semaines)", hint="12", value="12", width=120,
            on_change=lambda e: self._on_length_change(e.control.value),
        )
        self._fin_label = ft.Text("—", size=13, color=ACCENT)

        self._end_dd = mk_dropdown(
            "Fin de cycle", ["PCT", "Cruise", "TRT"],
            value="PCT", width=150,
            on_change=lambda e: self._on_end_mode_change(e.control.value),
        )
        self._pct_dd = mk_dropdown(
            "Mode PCT", ["Normal", "Agressif"],
            value="Normal", width=150,
            on_change=lambda e: self._on_pct_mode_change(e.control.value),
        )
        today_str = datetime.date.today().strftime("%d/%m/%Y")
        self._start_field = mk_entry(
            label="Date début", hint="JJ/MM/AAAA", value=today_str, width=130,
            on_change=lambda e: self._on_start_date_change(e.control.value),
        )
        self.state["start_date"] = today_str
        self._update_fin_date()

        def _open_cal(e):
            from data.widgets import show_date_picker
            def _on_date(date_str):
                self._start_field.value = date_str
                self._on_start_date_change(date_str)
            show_date_picker(self.page, self._start_field.value or today_str, _on_date)

        cal_btn = ft.ElevatedButton(
            content=ft.Text("📅", size=18),
            bgcolor=BG_CARD2, color=TEXT,
            tooltip="Choisir une date",
            on_click=_open_cal,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding.all(0),
            ),
            width=44, height=44,
        )

        # ── Zone dynamique PCT / Maintenance ─────────────────────────────────
        self._pct_zone = ft.Column(spacing=8)
        self._maint_field = mk_entry(
            label="Dose maintenance (mg/sem)", hint="250", value="", width=200,
            on_change=lambda e: self._on_maintenance_change(e.control.value),
        )
        # 4 champs PCT : Clomid J14 / Nolvadex J14 / Clomid J28 / Nolvadex J28
        self._pct_clomid_j14   = mk_entry(label="Clomid — J+14 (mg/j)",   hint="50",  value="50",  width=185,
                                           on_change=lambda e: self.state.update({"pct_clomid_j14": e.control.value}))
        self._pct_nolvadex_j14 = mk_entry(label="Nolvadex — J+14 (mg/j)", hint="20",  value="20",  width=185,
                                           on_change=lambda e: self.state.update({"pct_nolvadex_j14": e.control.value}))
        self._pct_clomid_j28   = mk_entry(label="Clomid — J+28 (mg/j)",   hint="25",  value="25",  width=185,
                                           on_change=lambda e: self.state.update({"pct_clomid_j28": e.control.value}))
        self._pct_nolvadex_j28 = mk_entry(label="Nolvadex — J+28 (mg/j)", hint="10",  value="10",  width=185,
                                           on_change=lambda e: self.state.update({"pct_nolvadex_j28": e.control.value}))
        self._pct_note = ft.Text("", size=11, color=TEXT_MUTED, italic=True)
        self._refresh_pct_zone()

        # Bouton "Voir sélection" — visible seulement si produits sélectionnés
        self._btn_voir_selection = mk_btn(
            "🔍  Voir sélection", self._show_selected_products_modal,
            color=ACCENT_DIM, hover=ACCENT_HOVER, width=160, height=36,
        )
        self._btn_voir_selection.visible = bool(self.state.get("selected_products"))

        return ft.Column([
            ft.Row([self._length_field,
                    ft.Row([self._start_field, cal_btn], spacing=0)],
                   spacing=12, wrap=True),
            ft.Row([
                ft.Text("Fin estimée :", size=12, color=TEXT_SUB),
                self._fin_label,
            ], spacing=8),
            ft.Row([self._end_dd, self._pct_dd], spacing=12, wrap=True),
            self._pct_zone,
            ft.Container(
                content=self._btn_voir_selection,
                padding=ft.Padding.only(top=6),
            ),
        ], spacing=10)

    # ── BLOC 5 : Notes ───────────────────────────────────────────────────────

    def _build_notes_inner(self) -> ft.Column:
        """Contenu notes — retourne Column pour accordéon Ghost."""
        self._note_field = ft.TextField(
            label="Notes / Observations", multiline=True, min_lines=3, max_lines=6,
            bgcolor=BG_INPUT, border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT, label_style=ft.TextStyle(color=TEXT_SUB, size=12),
            border_radius=R_INPUT, text_size=13,
            on_change=lambda e: self.state.update({"note": e.control.value}),
        )
        return ft.Column([self._note_field], spacing=0)

    # ══════════════════════════════════════════════════════════════════════════
    #  SECTIONS DYNAMIQUES
    # ══════════════════════════════════════════════════════════════════════════

    def _rebuild_doses(self):
        """Reconstruit les cartes de doses pour les produits sélectionnés."""
        if self._doses_col is None:
            return
        self._doses_col.controls.clear()
        self._dose_fields = {}
        selected = self.state["selected_products"]

        # Mettre à jour visibilité du bouton "Voir sélection"
        if hasattr(self, "_btn_voir_selection") and self._btn_voir_selection:
            self._btn_voir_selection.visible = bool(selected)

        if not selected:
            self._doses_col.controls.append(
                ft.Container(
                    content=ft.Text("← Sélectionnez des produits ci-dessus",
                                    size=12, color=TEXT_MUTED),
                    padding=ft.Padding.all(16),
                )
            )
        else:
            n_weeks = self.state["length"]
            for prod in selected:
                self._doses_col.controls.append(self._build_dose_card(prod, n_weeks))

        self._safe_update()

    def _build_dose_card(self, prod: str, n_weeks: int) -> ft.Container:
        info     = PRODUCT_INFO.get(prod, {})
        dose_min = info.get("dose_min", "—")
        dose_max = info.get("dose_max", "—")
        utilite  = info.get("utilite", "—")
        demi_vie = info.get("demi_vie", "—")
        danger   = info.get("dangerosite", "—")
        notes    = info.get("notes", "")
        rec      = _recommended_dose(dose_min)
        is_oral  = prod in _ORAL_PRODUCTS
        is_pct   = prod in _PCT_STRICT

        current_dose = self.state["product_doses"].get(prod, "")
        dose_indicator = ft.Text("—", size=11, color=TEXT_MUTED)

        def _on_dose_change(e, p=prod, di=dose_indicator, dmn=dose_min, dmx=dose_max):
            val = e.control.value.strip()
            self.state["product_doses"][p] = val
            if not val:
                di.value = "—"; di.color = TEXT_MUTED
            else:
                color = _dose_color(val, dmn, dmx)
                _, hi_min = _parse_dose_range(dmn)
                _, hi_max = _parse_dose_range(dmx)
                try:
                    entered = float(re.findall(r'\d+(?:[.,]\d+)?', val)[0].replace(',', '.'))
                    if hi_min and entered <= hi_min:
                        msg = "✅ Dans la fourchette recommandée"
                    elif hi_max and entered <= hi_max:
                        msg = "⚠  Dépasse le conseillé"
                    else:
                        msg = "🔴 Dépasse le maximum"
                except Exception:
                    msg = "—"
                di.value = msg; di.color = color
            self._rebuild_advice()
            self.page.update()

        dose_field = mk_entry(label="Dose utilisée", hint=rec, value=current_dose,
                              width=160, on_change=_on_dose_change)
        self._dose_fields[prod] = dose_field

        # Calculateur vials (injectables uniquement)
        vial_section = []
        if not is_oral and not is_pct:
            vial_result = ft.Text("", size=11, color=ACCENT)
            conc_f = mk_entry(label="Conc. (mg/ml)", hint="250", width=120)
            vol_f  = mk_entry(label="Vol. (ml)", hint="10",  width=100)

            def _update_vials(e=None, cr=conc_f, vr=vol_f, rr=vial_result, p=prod):
                df = self._dose_fields.get(p)
                dose_v = df.value if df else ""
                res = _calc_vials(dose_v, cr.value or "", vr.value or "", self.state["length"])
                rr.value = f"→ {res}" if res != "—" else ""
                self.page.update()

            conc_f.on_change = _update_vials
            vol_f.on_change  = _update_vials
            vial_section = [
                ft.Container(height=4),
                ft.Row([
                    ft.Text("Calculateur vials :", size=11, color=TEXT_MUTED),
                    conc_f, vol_f,
                ], spacing=8, wrap=True),
                vial_result,
            ]

        # Protocole PCT
        pct_section = []
        if is_pct:
            pct_mode = self.state.get("pct_mode", "Normal")
            end_mode = self.state.get("end_mode", "PCT")
            _PCT_SCHEDULES = {
                "Clomiphene (Clomid)":   {"Normal":[("J+14","50 mg/j"),("J+28","25 mg/j")],"Agressif":[("J+14","100 mg/j"),("J+28","50 mg/j"),("J+42","25 mg/j")]},
                "Tamoxifen (Nolvadex)":  {"Normal":[("J+14","20 mg/j"),("J+28","20 mg/j")],"Agressif":[("J+14","40 mg/j"),("J+28","20 mg/j"),("J+42","10 mg/j")]},
            }
            schedule = _PCT_SCHEDULES.get(prod, {}).get(pct_mode, [])
            if end_mode in ("TRT", "Cruise"):
                pct_section = [ft.Container(
                    content=ft.Text(f"⚠️  Incompatible avec {end_mode} — PCT inutile en maintien exogène.",
                                    size=11, color=WARNING),
                    bgcolor="#1a1020", border_radius=6, padding=ft.Padding.all(10),
                )]
            else:
                rows = [ft.Text(f"Protocole PCT — {pct_mode} (démarre 14j après dernière injection)",
                                size=11, color=ACCENT_GLOW, weight=ft.FontWeight.BOLD)]
                for phase, dose_txt in schedule:
                    rows.append(ft.Row([
                        ft.Text(phase, size=11, color=ACCENT, width=50),
                        ft.Text(dose_txt, size=11, color=TEXT),
                    ], spacing=8))
                pct_section = rows

        timing   = info.get("timing", "")

        card_controls = [
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Text(f"💊  {prod}", size=13, color=ACCENT, weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text(danger, size=11, color=WARNING),
                ]),
                bgcolor=BG_INPUT, border_radius=ft.BorderRadius.only(top_left=10, top_right=10),
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text(f"Utilité : {utilite}  |  Demi-vie : {demi_vie}",
                            size=11, color=TEXT_SUB),
                    ft.Text(f"Plage : {dose_min}  →  {dose_max}  |  ✅ Conseillé : {rec}",
                            size=11, color=TEXT_MUTED),
                    *([] if not timing else [
                        ft.Text(f"🕐 Timing : {timing}", size=11, color="#88aaff"),
                    ]),
                    ft.Container(height=6),
                    *([] if is_pct else [dose_field, dose_indicator]),
                    *vial_section,
                    *pct_section,
                    *([] if not notes else [
                        ft.Container(height=4),
                        ft.Text(f"⚠  {notes}", size=10, color="#cc9944"),
                    ]),
                ], spacing=4),
                padding=ft.Padding.all(12),
            ),
        ]

        return ft.Container(
            content=ft.Column(card_controls, spacing=0),
            bgcolor=BG_CARD2, border_radius=10,
            margin=ft.Margin.symmetric(horizontal=12, vertical=4),
        )

    def _rebuild_advice(self):
        """Met à jour le bloc résumé & recommandations."""
        if self._advice_col is None:
            return
        self._advice_col.controls.clear()
        selected = self.state["selected_products"]

        if not selected:
            self._advice_col.controls.append(
                ft.Container(
                    content=ft.Text("(aucun produit sélectionné)", size=12, color=TEXT_MUTED),
                    padding=ft.Padding.all(16),
                )
            )
            self._safe_update()
            return

        doses = self.state["product_doses"]
        n_weeks = self.state["length"]

        has_testo     = any(p in _AROMATIZING_TEST for p in selected)
        has_ai        = any(p in _AI_PRODUCTS for p in selected)
        has_hcg       = any(p in _HCG_PRODUCTS_SET for p in selected)
        has_tren_deca = any("Trenbolone" in p or "Nandrolone" in p or "Deca" in p for p in selected)
        has_caber     = any("Cabergoline" in p for p in selected)
        has_oraux     = any(p in _ORAL_PRODUCTS for p in selected)
        has_boldenone = any("Boldenone" in p for p in selected)
        max_washout   = max((_ESTER_WASHOUT.get(p, 0) for p in selected), default=2)

        alerts = []
        if has_testo and not has_ai:
            alerts.append("⚠️  TESTO sans IA — ajoute Anastrozole 0.25 mg EOD ou Exemestane 12.5 mg EOD\n→ Sans IA : gynécomastie, rétention, hypertension")
        if has_testo and not has_hcg:
            alerts.append("⚠️  TESTO sans hCG — atrophie testiculaire progressive\n→ HCG 500 UI 2–3x/sem à partir de S3")
        if has_tren_deca and not has_caber:
            alerts.append("⚠️  Tren/Deca sans Cabergoline — risque prolactine élevée\n→ Cabergoline 0.25 mg 2x/sem dès S1")

        bilan = []
        if has_oraux:      bilan.append("ALAT/ASAT S4 et S8 (hépatotoxicité)")
        if has_boldenone:  bilan.append("Hématocrite S4 et S8 (polyglobulie)")
        if has_tren_deca:  bilan.append("Prolactine S4 et S8")
        if has_testo or has_ai: bilan.append("Lipides HDL/LDL S4 et S8")
        bilan.append("Bilan hormonal complet 4 sem post-PCT")
        if bilan:
            alerts.append("🩸  BILANS SANGUINS :\n→ " + "\n→ ".join(bilan))

        max_w_prod = max(selected, key=lambda p: _ESTER_WASHOUT.get(p, 0), default=None)
        if max_w_prod and _ESTER_WASHOUT.get(max_w_prod, 0) > 0:
            alerts.append(f"⏳  Wash-out : {max_washout} sem (ester le plus long : {max_w_prod})")

        if alerts:
            self._advice_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(a, size=11, color="#ff6644", weight=ft.FontWeight.BOLD)
                        for a in alerts
                    ], spacing=6),
                    bgcolor="#2a1010", border_radius=8,
                    padding=ft.Padding.all(12),
                    margin=ft.Margin.symmetric(horizontal=12),
                )
            )

        for prod in selected:
            info   = PRODUCT_INFO.get(prod, {})
            d_min  = info.get("dose_min", "—")
            d_max  = info.get("dose_max", "—")
            rec    = _recommended_dose(d_min)
            notes  = info.get("notes", "")
            dose_v = doses.get(prod, "")

            dose_display = []
            if dose_v:
                color = _dose_color(dose_v, d_min, d_max)
                try:
                    nums  = re.findall(r'\d+(?:[.,]\d+)?', dose_v)
                    total = int(float(nums[0].replace(',', '.')) * n_weeks)
                    dose_display = [ft.Text(f"Dose : {dose_v}/sem  →  {total} mg sur {n_weeks} sem",
                                           size=11, color=color)]
                except Exception:
                    pass

            self._advice_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"💊 {prod}", size=12, color=ACCENT, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Conseillé : {rec}  |  Plage : {d_min} → {d_max}", size=11, color="#aaddaa"),
                        *dose_display,
                        *([] if not notes else [ft.Text(f"⚠ {notes}", size=10, color="#cc9944")]),
                    ], spacing=3),
                    bgcolor=BG_CARD2, border_radius=8,
                    padding=ft.Padding.all(10),
                    margin=ft.Margin.symmetric(horizontal=12, vertical=3),
                )
            )

        # Timeline + Boutons Générer + Sauvegarder en bas du résumé
        self._advice_col.controls.append(self._build_inline_timeline())
        self._advice_col.controls.append(
            ft.Container(
                content=ft.Row([
                    mk_btn("🧬  Générer planning", self._on_generate,
                           color=WARNING, hover="#d97706", width=180, height=44),
                    mk_btn("💾  SAUVEGARDER", self._on_save,
                           color=SUCCESS, hover=SUCCESS_HVR, width=160, height=44),
                    mk_btn("📄  Export PDF", self._on_export_pdf,
                           color=GRAY, hover=GRAY_HVR, width=140, height=44),
                ], spacing=10, wrap=True),
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            )
        )

        self._safe_update()

    def _rebuild_history(self):
        """Recharge les cycles sauvegardés depuis la base."""
        if self._hist_col is None:
            return
        self._hist_col.controls.clear()
        self._hist_selected_row = None
        self._hist_selected_ref = {"container": None}

        try:
            rows = _db.cycle_get_all(self._fake_app())
        except Exception:
            rows = []

        if not rows:
            self._hist_col.controls.append(
                ft.Container(
                    content=ft.Text("Aucun cycle sauvegardé.", size=12, color=TEXT_MUTED),
                    padding=ft.Padding.all(16),
                )
            )
            self._safe_update()
            return

        import datetime as _dt

        def _parse_date(s):
            for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                try:
                    return _dt.datetime.strptime(str(s or "").strip(), fmt).date()
                except Exception:
                    pass
            return None

        today = _dt.date.today()

        def _is_active(row):
            d = _parse_date(row.get("debut", ""))
            if not d:
                return False
            try: n = int(row.get("longueur_sem", 12))
            except: n = 12
            d_fin = _parse_date(row.get("fin_estimee", "")) or (d + _dt.timedelta(weeks=n))
            end_mode = row.get("end_mode", "PCT")
            d_fin_active = d_fin if end_mode in ("TRT", "Cruise") else d_fin + _dt.timedelta(weeks=6)
            return d <= today <= d_fin_active

        btn_charger   = mk_btn("📂 Charger",   self._on_hist_load,   color=ACCENT,    hover=ACCENT_HOVER, width=120, height=36)
        btn_modifier  = mk_btn("✏ Modifier",   self._on_hist_edit,   color="#40c0e0", hover="#2aa0c0",    width=120, height=36)
        btn_supprimer = mk_btn("🗑 Supprimer", self._on_hist_delete, color="#6b2222", hover=DANGER_HVR,   width=120, height=36)

        for row in reversed(rows[-10:]):
            debut        = row.get("debut", "—")
            fin          = row.get("fin_estimee", "—")
            semaines     = row.get("longueur_sem", "?")
            produits     = row.get("produits_doses", "")
            note         = row.get("note", "")
            prod_preview = produits[:80] + ("…" if len(produits) > 80 else "")
            actif        = _is_active(row)
            badge_txt    = "● EN COURS" if actif else "● ARCHIVÉ"
            badge_col    = SUCCESS      if actif else TEXT_MUTED
            item_ref     = ft.Ref[ft.Container]()

            def _on_select(e, r=row, ref=item_ref):
                prev = self._hist_selected_ref["container"]
                if prev and prev.current:
                    prev.current.bgcolor = BG_CARD2
                if ref.current:
                    ref.current.bgcolor = ACCENT_DIM
                self._hist_selected_ref["container"] = ref
                self._hist_selected_row = r
                self._safe_update()

            self._hist_col.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"📅 {debut} → {fin}", size=12, color=ACCENT,
                                    weight=ft.FontWeight.BOLD, expand=True),
                            ft.Text(badge_txt, size=10, color=badge_col,
                                    weight=ft.FontWeight.BOLD),
                            ft.Text(f"{semaines} sem", size=11, color=TEXT_SUB),
                        ], spacing=8),
                        ft.Text(prod_preview, size=11, color=TEXT),
                        *([] if not note else [ft.Text(note[:60], size=10, color=TEXT_MUTED)]),
                    ], spacing=4),
                    bgcolor=BG_CARD2, border_radius=8,
                    padding=ft.Padding.all(10),
                    margin=ft.Margin.symmetric(horizontal=12, vertical=3),
                    ink=True, ref=item_ref, on_click=_on_select,
                )
            )

        self._hist_col.controls.append(
            ft.Container(
                content=ft.Row([btn_charger, btn_modifier, btn_supprimer],
                               spacing=8, wrap=True),
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            )
        )
        self._safe_update()

    def _on_hist_load(self, e=None):
        row = getattr(self, "_hist_selected_row", None)
        if not row:
            self._snack("Sélectionne d'abord un cycle.", WARNING); return
        self._load_cycle_from_history(row)
        self._snack("✔ Cycle chargé.", SUCCESS)

    def _on_hist_delete(self, e=None):
        row = getattr(self, "_hist_selected_row", None)
        if not row:
            self._snack("Sélectionne d'abord un cycle.", WARNING); return
        debut = row.get("debut", "")
        self._delete_cycle_by_date(debut)
        self._hist_selected_row = None
        self._hist_selected_ref = {"container": None}

    def _on_hist_edit(self, e=None):
        row = getattr(self, "_hist_selected_row", None)
        if not row:
            self._snack("Sélectionne d'abord un cycle.", WARNING); return
        self._open_hist_edit_modal(row)

    def _open_hist_edit_modal(self, row: dict):
        """Modal complet : modifie date, durée, produits/doses, fin de cycle, PCT, note."""
        def _mk_field(label, value="", **kw):
            return ft.TextField(
                label=label, value=value,
                bgcolor=BG_INPUT, border_color=BORDER,
                focused_border_color=ACCENT, color=TEXT,
                label_style=ft.TextStyle(color=TEXT_SUB, size=11),
                border_radius=8, text_size=13, **kw)

        f_debut   = _mk_field("Date début (JJ/MM/AAAA)", row.get("debut", ""), width=180)
        f_sem     = _mk_field("Durée (sem)", str(row.get("longueur_sem", "12")), width=100)
        f_produits= _mk_field("Produits & doses", row.get("produits_doses", ""),
                               multiline=True, min_lines=3, max_lines=5,
                               hint_text="Produit: dose | Produit2: dose2 ...")
        f_note    = _mk_field("Notes", row.get("note", ""),
                               multiline=True, min_lines=2, max_lines=3)

        end_mode_cur = row.get("end_mode", "PCT")
        f_end = ft.Dropdown(
            label="Fin de cycle",
            value=end_mode_cur,
            options=[ft.dropdown.Option(v) for v in ["PCT", "Cruise", "TRT"]],
            bgcolor=BG_INPUT, border_color=BORDER,
            focused_border_color=ACCENT, color=TEXT,
            label_style=ft.TextStyle(color=TEXT_SUB, size=11),
            border_radius=8, text_size=13, width=150,
        )

        dlg = ft.AlertDialog(modal=True)

        def _close(ev=None):
            dlg.open = False
            self.page.update()

        def _save(ev=None):
            try:
                import data.db as _db2
                fake = self._fake_app()
                con  = _db2.get_user_db(fake.current_user)
                con.execute(
                    """UPDATE cycle
                       SET debut=?, longueur_sem=?, produits_doses=?,
                           note=?, end_mode=?
                       WHERE debut=?""",
                    (
                        f_debut.value.strip(),
                        f_sem.value.strip(),
                        f_produits.value.strip(),
                        f_note.value.strip(),
                        f_end.value or "PCT",
                        row.get("debut", ""),
                    )
                )
                con.commit(); con.close()
            except Exception as ex:
                self._snack(f"Erreur : {ex}", DANGER); return
            _close()
            self._rebuild_history()
            self._snack("✔ Cycle modifié.", SUCCESS)

        dlg.title = ft.Text("✏ Modifier le cycle", color=ACCENT,
                            weight=ft.FontWeight.BOLD, size=15)
        dlg.content = ft.Container(
            content=ft.Column([
                ft.Row([f_debut, f_sem, f_end], spacing=10, wrap=True),
                f_produits,
                f_note,
            ], spacing=10, tight=True),
            width=360, padding=ft.padding.only(top=8),
        )
        dlg.actions = [
            ft.ElevatedButton(
                content=ft.Text("✕ Annuler", size=13, color=TEXT,
                                weight=ft.FontWeight.BOLD),
                bgcolor=GRAY, on_click=_close, width=130, height=42),
            ft.ElevatedButton(
                content=ft.Text("💾 Sauvegarder", size=13, color=TEXT,
                                weight=ft.FontWeight.BOLD),
                bgcolor=SUCCESS, on_click=_save, width=170, height=42),
        ]
        dlg.bgcolor = BG_CARD
        dlg.shape   = ft.RoundedRectangleBorder(radius=16)
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    # ══════════════════════════════════════════════════════════════════════════
    #  PLANNING MODAL
    # ══════════════════════════════════════════════════════════════════════════

    def _show_planning_modal(self):
        selected = self.state["selected_products"]
        if not selected:
            self._snack("Sélectionnez au moins un produit.", DANGER)
            return

        PHASE_COLORS = {
            "CYCLE": ACCENT, "WASHOUT": WARNING,
            "PCT": PURPLE, "CRUISE": "#40c0e0", "TRT": "#c080ff",
        }

        # ── État local options ────────────────────────────────────────────────
        opt_state = {
            "end_mode": self.state.get("end_mode", "PCT"),
            "pct_mode": self.state.get("pct_mode", "Normal"),
        }

        # ── Résumé produits sélectionnés ──────────────────────────────────────
        pct_sel  = [p for p in selected if p in _PCT_STRICT]
        hcg_sel  = [p for p in selected if p in _HCG_PRODUCTS_SET]
        ia_sel   = [p for p in selected if p in _AI_PRODUCTS]
        has_testo = any(p in _AROMATIZING_TEST for p in selected)
        info_parts = []
        if hcg_sel:
            info_parts.append("💉 hCG → démarrage S3, veille injection testo")
        if pct_sel:
            info_parts.append(f"💊 PCT strict J14 → {', '.join(pct_sel)}")
        if ia_sel:
            info_parts.append(f"🛡️ IA cycle → {', '.join(ia_sel)}")
        if has_testo and not ia_sel:
            info_parts.append("⚠️ TESTO SANS IA DÉTECTÉE — risque gynécomastie")

        info_text = ft.Text(
            "  |  ".join(info_parts) if info_parts else "Aucun hCG ni PCT sélectionné",
            size=11, color=TEXT_SUB,
        )

        # ── Tableau dynamique ─────────────────────────────────────────────────
        table_col    = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=0)
        legend_text  = ft.Text("", size=11, color=TEXT_MUTED)

        def _build_rows():
            plan = _build_cycle_plan({**self.state, **opt_state}, CATEGORY_ITEMS)
            table_col.controls.clear()
            table_col.controls.append(
                ft.DataTable(
                    columns=[
                        ft.DataColumn(ft.Text("Semaine",      size=11, color=TEXT_SUB)),
                        ft.DataColumn(ft.Text("Date début",   size=11, color=TEXT_SUB)),
                        ft.DataColumn(ft.Text("Phase",        size=11, color=TEXT_SUB)),
                        ft.DataColumn(ft.Text("Produits & IA",size=11, color=TEXT_SUB)),
                        ft.DataColumn(ft.Text("hCG / Timing", size=11, color=TEXT_SUB)),
                        ft.DataColumn(ft.Text("PCT / Protocole",size=11, color=TEXT_SUB)),
                    ],
                    rows=[
                        ft.DataRow(cells=[
                            ft.DataCell(ft.Text(w["label"],               size=11, color=PHASE_COLORS.get(w["phase"], TEXT))),
                            ft.DataCell(ft.Text(w["date_start"] or "—",   size=11, color=TEXT_SUB)),
                            ft.DataCell(ft.Text(w["phase"],               size=11, color=PHASE_COLORS.get(w["phase"], TEXT), weight=ft.FontWeight.BOLD)),
                            ft.DataCell(ft.Text((w["produits"] or "—")[:70], size=10, color=TEXT)),
                            ft.DataCell(ft.Text(w["hcg"] or "—",          size=10, color=ACCENT_GLOW)),
                            ft.DataCell(ft.Text(w["pct_info"] or "—",     size=10, color=PURPLE)),
                        ])
                        for w in plan
                    ],
                    column_spacing=10,
                    heading_row_color=BG_CARD2,
                    data_row_color={ft.ControlState.DEFAULT: BG_ROOT},
                    border=ft.Border.all(1, BORDER),
                    border_radius=8,
                )
            )
            # Compteurs
            n_c = sum(1 for w in plan if w["phase"] == "CYCLE")
            n_w = sum(1 for w in plan if w["phase"] == "WASHOUT")
            n_p = sum(1 for w in plan if w["phase"] == "PCT")
            n_e = sum(1 for w in plan if w["phase"] in ("CRUISE", "TRT"))
            legend_text.value = (
                f"✅ Cycle : {n_c} sem  |  ⏳ Wash-out : {n_w} sem  |  "
                f"💊 PCT : {n_p} sem  |  🔵 {opt_state['end_mode']} : {n_e} sem  |  "
                f"TOTAL : {n_c+n_w+n_p+n_e} semaines"
            )
            try:
                self.page.update()
            except Exception:
                pass

        # ── Boutons options End Mode ──────────────────────────────────────────
        def _make_end_btn(label, color):
            def _on(e):
                opt_state["end_mode"] = label
                _build_rows()
            return mk_btn(label, _on, color=color, hover=color, width=90, height=34)

        def _make_pct_btn(label, color):
            def _on(e):
                opt_state["pct_mode"] = label
                _build_rows()
            return mk_btn(label, _on, color=color, hover=color, width=100, height=34)

        opts_row = ft.Row([
            ft.Text("Fin :", size=11, color=TEXT_MUTED),
            _make_end_btn("PCT",    ACCENT),
            _make_end_btn("Cruise", "#40c0e0"),
            _make_end_btn("TRT",    "#c080ff"),
            ft.Container(width=16),
            ft.Text("Mode PCT :", size=11, color=TEXT_MUTED),
            _make_pct_btn("Normal",   ACCENT),
            _make_pct_btn("Agressif", WARNING),
        ], spacing=6, wrap=True)

        # Légende couleurs
        legend_colors = ft.Row([
            ft.Text("🟢 Cycle", size=10, color=ACCENT),
            ft.Text("🟡 Wash-out", size=10, color=WARNING),
            ft.Text("🔵 PCT", size=10, color=PURPLE),
            ft.Text("🔵 Cruise", size=10, color="#40c0e0"),
            ft.Text("🟣 TRT", size=10, color="#c080ff"),
        ], spacing=12, wrap=True)

        # Premier rendu
        _build_rows()

        w = self.page.window.width if self.page.window else 420
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("🧬  PLANNING DE CYCLE — Semaine par semaine",
                          color=ACCENT, size=15, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=info_text,
                        bgcolor=BG_CARD2, border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
                        margin=ft.Margin.only(bottom=6),
                    ),
                    opts_row,
                    ft.Container(height=6),
                    table_col,
                    ft.Container(height=8),
                    legend_colors,
                    legend_text,
                ], scroll=ft.ScrollMode.AUTO),
                width=min(w * 0.95, 900),
                height=520,
                bgcolor=BG_CARD,
            ),
            actions=[
                ft.TextButton(content=ft.Text("Fermer", color=TEXT_MUTED), on_click=lambda e: self._close_dlg(dlg)),
            ],
            bgcolor=BG_CARD,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _close_dlg(self, dlg):
        dlg.open = False
        self.page.update()

    def _load_cycle_from_history(self, row: dict):
        """Charge un cycle sauvegardé dans tous les widgets UI — port de _load_cycle_into_ui."""
        if not row:
            return
        debut        = row.get("debut", "")
        longueur_sem = str(row.get("longueur_sem", "12")).strip()
        note_s       = row.get("note", "")
        produits_s   = row.get("produits_doses", "")

        # Longueur
        try:
            self.state["length"] = int(longueur_sem)
            if hasattr(self, "_length_field"):
                self._length_field.value = longueur_sem
        except Exception:
            pass

        # Preset
        preset_map = {"12": "12 semaines", "16": "16 semaines"}
        self.state["preset"] = preset_map.get(longueur_sem, "Personnalisé")

        # Date début
        if debut and debut != "—":
            self.state["start_date"] = debut
            if hasattr(self, "_start_field"):
                self._start_field.value = debut

        # Note
        if note_s and hasattr(self, "_note_field"):
            self.state["note"] = note_s
            self._note_field.value = note_s

        # Produits + doses
        if produits_s:
            # Effacer sélection courante
            for p, cb in self._product_checks.items():
                cb.value = False
            self.state["selected_products"].clear()
            self.state["product_doses"].clear()

            entries = [e.strip() for e in produits_s.split("|") if e.strip()]
            for entry in entries:
                parts = entry.split(":", 1)
                name  = parts[0].strip()
                dose  = parts[1].strip() if len(parts) > 1 else ""
                if name in self._product_checks:
                    self._product_checks[name].value = True
                    if name not in self.state["selected_products"]:
                        self.state["selected_products"].append(name)
                    if dose:
                        self.state["product_doses"][name] = dose

        self._rebuild_doses()
        self._rebuild_advice()
        self._update_fin_date()
        self._safe_update()
        self._snack(f"✔ Cycle du {debut} chargé.", SUCCESS)

    def _delete_cycle_by_date(self, debut: str):
        """Supprime un cycle de la DB par date de début — port de _delete_selected_cycle."""
        def _confirm(e):
            dlg.open = False
            self.page.update()
            try:
                import data.db as _db2
                fake = self._fake_app()
                con  = _db2.get_user_db(fake.current_user)
                con.execute("DELETE FROM cycle WHERE debut=?", (debut,))
                con.commit()
                con.close()
                self._rebuild_history()
                self._snack(f"✔ Cycle du {debut} supprimé.", SUCCESS)
            except Exception as ex:
                self._snack(f"Erreur suppression : {ex}", DANGER)

        def _cancel(e):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmer la suppression", color=DANGER, size=14),
            content=ft.Text(f"Supprimer le cycle du {debut} ?\nCette action est irréversible.",
                            size=12, color=TEXT),
            actions=[
                ft.TextButton(content=ft.Text("Annuler", color=TEXT_MUTED), on_click=_cancel),
                ft.TextButton(content=ft.Text("Supprimer", color=TEXT_MUTED), on_click=_confirm,
                              style=ft.ButtonStyle(color=DANGER)),
            ],
            bgcolor=BG_CARD,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _open_halflife_calc(self, e=None):
        """Ouvre le calculateur de demi-vie en dialog."""
        from data.widgets import show_halflife_dialog
        show_halflife_dialog(self.page)

    def _show_selected_products_modal(self, e=None):
        """Popup tableau récap des produits sélectionnés — port de _show_selected_products."""
        selected = self.state["selected_products"]
        if not selected:
            self._snack("Aucun produit sélectionné.", WARNING)
            return

        rows = []
        for prod in selected:
            info = PRODUCT_INFO.get(prod, {})
            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(prod,                         size=11, color=ACCENT)),
                    ft.DataCell(ft.Text(info.get("utilite",    "—"),  size=11, color=TEXT)),
                    ft.DataCell(ft.Text(info.get("dose_min",   "—"),  size=11, color=TEXT_SUB)),
                    ft.DataCell(ft.Text(info.get("dose_max",   "—"),  size=11, color=TEXT_SUB)),
                    ft.DataCell(ft.Text(info.get("popularite", "—"),  size=11, color=TEXT_MUTED)),
                    ft.DataCell(ft.Text(info.get("dangerosite","—"),  size=11, color=WARNING)),
                    ft.DataCell(ft.Text(info.get("demi_vie",   "—"),  size=11, color=TEXT_MUTED)),
                    ft.DataCell(ft.Text(info.get("notes",      ""),   size=10, color="#cc9944")),
                ])
            )

        w = self.page.window.width if self.page.window else 420
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("🔍  Détails des produits sélectionnés",
                          color=ACCENT, size=14, weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.DataTable(
                        columns=[
                            ft.DataColumn(ft.Text("Produit",          size=11, color=TEXT_SUB)),
                            ft.DataColumn(ft.Text("Utilité",          size=11, color=TEXT_SUB)),
                            ft.DataColumn(ft.Text("Dose min",         size=11, color=TEXT_SUB)),
                            ft.DataColumn(ft.Text("Dose max",         size=11, color=TEXT_SUB)),
                            ft.DataColumn(ft.Text("Popularité",       size=11, color=TEXT_SUB)),
                            ft.DataColumn(ft.Text("Dangérosité",      size=11, color=TEXT_SUB)),
                            ft.DataColumn(ft.Text("Demi-vie",         size=11, color=TEXT_SUB)),
                            ft.DataColumn(ft.Text("Notes",            size=11, color=TEXT_SUB)),
                        ],
                        rows=rows,
                        column_spacing=10,
                        heading_row_color=BG_CARD2,
                        data_row_color={ft.ControlState.DEFAULT: BG_ROOT},
                        border=ft.Border.all(1, BORDER),
                        border_radius=8,
                    ),
                ], scroll=ft.ScrollMode.AUTO),
                width=min(w * 0.95, 960),
                height=400,
                bgcolor=BG_CARD,
            ),
            actions=[
                ft.TextButton(content=ft.Text("Fermer", color=TEXT_MUTED), on_click=lambda e: self._close_dlg(dlg)),
            ],
            bgcolor=BG_CARD,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    # ══════════════════════════════════════════════════════════════════════════
    #  HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    def _on_product_toggle(self, prod: str, checked: bool):
        sel = self.state["selected_products"]
        if checked and prod not in sel:
            sel.append(prod)
        elif not checked and prod in sel:
            sel.remove(prod)
        self._rebuild_doses()
        self._rebuild_advice()
        self._rebuild_injection_planner()
        self._rebuild_injection_preview()

    def _on_preset_change(self, preset: str):
        self.state["preset"] = preset
        length_map = {"12 semaines": 12, "16 semaines": 16, "Premier Cycle": 12}
        if preset in length_map:
            self.state["length"] = length_map[preset]
            if hasattr(self, "_length_field"):
                self._length_field.value = str(length_map[preset])
        if preset == "Premier Cycle":
            # Pré-sélectionner produits recommandés
            targets = ["Testosterone Enanthate", "HCG", "Anastrozole (Arimidex)", "Clomiphene (Clomid)"]
            for t in targets:
                if t in self._product_checks:
                    self._product_checks[t].value = True
                    if t not in self.state["selected_products"]:
                        self.state["selected_products"].append(t)
            # Pré-remplir doses
            defaults = {"Testosterone Enanthate":"400","HCG":"500","Anastrozole (Arimidex)":"0.25","Clomiphene (Clomid)":"50"}
            for p, d in defaults.items():
                self.state["product_doses"].setdefault(p, d)
        self._rebuild_doses()
        self._rebuild_advice()
        self._update_fin_date()
        self._safe_update()

    def _on_length_change(self, val: str):
        v = utils.parse_num(val, int, None, min_val=1, max_val=52)
        if v is not None:
            self.state["length"] = v
            if self._length_field:
                self._length_field.border_color = SUCCESS
        else:
            if self._length_field:
                self._length_field.border_color = DANGER if val.strip() else None
        self._update_fin_date()

    def _on_start_date_change(self, val: str):
        self.state["start_date"] = val.strip()
        self._update_fin_date()

    def _on_end_mode_change(self, val: str):
        self.state["end_mode"] = val
        self._refresh_pct_zone()
        self._safe_update()
        self._rebuild_doses()
        self._rebuild_advice()

    def _on_pct_mode_change(self, val: str):
        self.state["pct_mode"] = val
        self._refresh_pct_zone()
        self._safe_update()
        self._rebuild_doses()

    def _on_maintenance_change(self, val: str):
        self.state["maintenance_dose"] = val.strip()

    def _refresh_pct_zone(self):
        """Met à jour la zone dynamique PCT / Maintenance selon end_mode + pct_mode."""
        if not hasattr(self, "_pct_zone") or self._pct_zone is None:
            return
        self._pct_zone.controls.clear()
        mode = self.state.get("end_mode", "PCT")

        if mode == "PCT":
            pct_mode = self.state.get("pct_mode", "Normal")
            if pct_mode == "Agressif":
                c14, n14, c28, n28 = "100", "40", "50", "20"
                note = "S1–S2 : doses hautes · S3–S4 : doses intermédiaires · S5–S6 : Clomid 25 / Nolvadex 10"
            else:
                c14, n14, c28, n28 = "50", "20", "25", "10"
                note = "S1–S2 : J+14 (doses hautes) · S3–S4 : J+28 (doses basses)"

            # Préremplir les champs
            if self._pct_clomid_j14:
                self._pct_clomid_j14.value   = c14
                self._pct_nolvadex_j14.value = n14
                self._pct_clomid_j28.value   = c28
                self._pct_nolvadex_j28.value = n28
                self._pct_note.value = note

            # Sauvegarder dans state
            self.state.update({
                "pct_clomid_j14": c14, "pct_nolvadex_j14": n14,
                "pct_clomid_j28": c28, "pct_nolvadex_j28": n28,
            })

            self._pct_zone.controls.extend([
                ft.Text("Post Cycle Therapy — démarrage J+14", size=11,
                        color=ACCENT, weight=ft.FontWeight.BOLD),
                ft.Row([self._pct_clomid_j14, self._pct_clomid_j28], spacing=10, wrap=True),
                ft.Text("Réduction — J+28", size=11,
                        color=TEXT_SUB, weight=ft.FontWeight.BOLD),
                ft.Row([self._pct_nolvadex_j14, self._pct_nolvadex_j28], spacing=10, wrap=True),
                self._pct_note,
            ])
        else:
            self._pct_zone.controls.append(self._maint_field)

    def _update_fin_date(self):
        start_str = self.state.get("start_date", "")
        n = self.state.get("length", 12)
        if not start_str or not self._fin_label:
            if self._fin_label:
                self._fin_label.value = "—"
            return
        try:
            dt = datetime.datetime.strptime(start_str, "%d/%m/%Y")
            fin = (dt + datetime.timedelta(weeks=n)).strftime("%d/%m/%Y")
            self.state["fin_date"] = fin
            self._fin_label.value = fin
        except ValueError:
            self._fin_label.value = "date invalide"
        self._safe_update()

    def _on_export_pdf(self, e=None):
        """Export PDF du cycle complet."""
        try:
            from data.pdf_utils import export_cycle_pdf
            path = export_cycle_pdf(self.app_state, page=self.page)
            if path:
                self._snack(f"✔ PDF généré : {path}", SUCCESS)
        except Exception as ex:
            self._snack(f"Erreur PDF : {ex}", DANGER)

    def _on_generate(self, e):
        self._show_planning_modal()

    def _on_save(self, e):
        app_state = self.app_state
        if not app_state.get("current_user"):
            self._snack("Aucun profil sélectionné.", DANGER)
            return
        sel   = self.state["selected_products"]
        doses = self.state["product_doses"]
        parts = [f"{p}: {doses[p]}" if doses.get(p) else p for p in sel]
        produits_field = " | ".join(parts)
        note     = getattr(self._note_field, "value", "") or self.state.get("note", "")
        start    = self.state.get("start_date", "—") or "—"
        fin      = self.state.get("fin_date", "—") or "—"
        length   = str(self.state.get("length", 12))
        end_mode = self.state.get("end_mode", "PCT")
        import json as _json
        days_2x_json = _json.dumps(
            {k: list(v) for k, v in self.state.get("days_2x_config", {}).items()}
        )
        try:
            _db.cycle_insert(self._fake_app(), start, fin, length,
                             produits_field, note, end_mode)
            # Sauvegarder days_2x_config via le contextmanager — ne pas appeler con.close()
            from data.db import db_connection, _user_path_from_app
            with db_connection(_user_path_from_app(self._fake_app())) as con:
                con.execute("UPDATE cycle SET days_2x_config=? WHERE debut=?",
                            (days_2x_json, start))
            self._rebuild_history()
            self._snack(f"✔ Cycle du {start} sauvegardé.", SUCCESS)
        except Exception as ex:
            self._snack(f"Erreur : {ex}", DANGER)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _fake_app(self):
        """Objet minimal compatible avec les fonctions db qui attendent app.current_user."""
        class _FakeApp:
            def __init__(self, folder):
                self.current_user = folder
        return _FakeApp(self.app_state.get("current_user", ""))

    def _snack(self, msg: str, color: str = SUCCESS):
        from ui.snackbar import snack, _LEVEL_COLORS
        _col_to_level = {v: k for k, v in _LEVEL_COLORS.items()}
        level = _col_to_level.get(color, "success")
        snack(self.page, msg, level)

    def _safe_update(self):
        from ui.page_utils import safe_update
        safe_update(self.page)

    def _load_last_cycle(self):
        """Charge le cycle actif depuis la DB au démarrage."""
        try:
            row = _db.cycle_get_active(self._fake_app())
            if not row:
                return
            # Restaurer produits + doses depuis la chaîne stockée
            raw = row.get("produits_doses", "")
            if raw:
                parts = [p.strip() for p in raw.split("|")]
                for part in parts:
                    if ":" in part:
                        prod, dose = part.split(":", 1)
                        prod = prod.strip(); dose = dose.strip()
                    else:
                        prod = part.strip(); dose = ""
                    if prod in self._product_checks:
                        self._product_checks[prod].value = True
                        self.state["selected_products"].append(prod)
                        if dose:
                            self.state["product_doses"][prod] = dose

            try:
                self.state["length"] = int(row.get("longueur_sem", 12))
                if hasattr(self, "_length_field"):
                    self._length_field.value = str(self.state["length"])
            except Exception:
                pass

            start = row.get("debut", "")
            if start and start != "—" and hasattr(self, "_start_field"):
                self.state["start_date"] = start
                self._start_field.value = start

            note = row.get("note", "")
            if note and hasattr(self, "_note_field"):
                self.state["note"] = note
                self._note_field.value = note

            # Restaurer days_2x_config depuis la DB
            import json as _json
            try:
                raw_2x = row.get("days_2x_config", "{}")
                parsed_2x = _json.loads(raw_2x if isinstance(raw_2x, str) else "{}")
                for k, v in parsed_2x.items():
                    if isinstance(v, (list, tuple)) and len(v) >= 2:
                        self.state["days_2x_config"][k] = (int(v[0]), int(v[1]))
            except Exception:
                pass

            # Appliquer lundi/jeudi par défaut pour les produits 2x/sem sans config
            for prod in self.state["selected_products"]:
                if _inj.get_freq(prod) == _inj.FREQ_2X_SEM and prod not in self.state["days_2x_config"]:
                    self.state["days_2x_config"][prod] = (0, 3)

            self._rebuild_doses()
            self._rebuild_advice()
            self._rebuild_injection_planner()
            self._update_fin_date()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  ÉCRAN DE QUALIFICATION (disclaimer)
# ══════════════════════════════════════════════════════════════════════════════

class QualificationView:
    """
    Qualification multi-étapes avant accès au module cycle.
    Étapes : âge → expérience → QCM → confirmation
    """

    def __init__(self, page: ft.Page, app_state: dict, on_qualified):
        self.page       = page
        self.app_state  = app_state
        self.on_qualified = on_qualified
        self.state = {"step": 1, "answers": {}}

        self.root_col = ft.Column(spacing=0)
        self._show_step1()

    def get_view(self) -> ft.Column:
        return self.root_col

    def _clear(self):
        self.root_col.controls.clear()

    def _header(self, text: str, color: str = "#cc2222") -> ft.Column:
        return ft.Column([
            ft.Text(text, size=15, color=color, weight=ft.FontWeight.BOLD),
            ft.Divider(height=2, color=color),
        ], spacing=4)

    def _body(self, text: str, color: str = "#c0c0c0") -> ft.Text:
        return ft.Text(text, size=12, color=color)

    def _refuse(self, reason: str = ""):
        self._clear()
        self.root_col.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Text("⛔  ACCÈS REFUSÉ", size=22, color=DANGER,
                            weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=16),
                    ft.Text(reason or "Tu ne remplis pas les conditions d'accès.",
                            size=12, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                    ft.Container(height=20),
                    ft.Text("Cet outil est réservé aux adultes expérimentés qui ont pris leur décision "
                            "de façon autonome et éclairée, avec un suivi médical.",
                            size=11, color="#666666", text_align=ft.TextAlign.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.all(32),
            )
        )
        self.page.update()

    # ── Étape 1 : Âge ────────────────────────────────────────────────────────

    def _show_step1(self):
        self._clear()
        year_field = mk_entry(label="Année de naissance", hint="ex: 1990", width=200)
        err_text   = ft.Text("", size=11, color=DANGER)

        def _validate(e=None):
            try:
                birth_year = int(year_field.value.strip())
            except ValueError:
                err_text.value = "⚠  Saisis une année valide (ex: 1990)."; self.page.update(); return
            age = datetime.datetime.now().year - birth_year
            if age < 0 or birth_year < 1920:
                err_text.value = "⚠  Année invalide."; self.page.update(); return
            if age < 18:
                self._refuse("Tu es mineur(e).\n\nL'accès est totalement interdit. Concentre-toi sur ton entraînement naturel — à ton âge, ton potentiel hormonal est à son maximum."); return
            if age < 21:
                self._refuse(f"Tu as {age} ans.\n\nL'accès est refusé aux moins de 21 ans.\nTon axe HPTA n'est pas encore pleinement mature. Reviens après 21 ans avec un bilan médical complet."); return
            self._show_step2()

        self.root_col.controls.append(
            ft.Container(
                content=ft.Column([
                    self._header("ÉTAPE 1 / 4 — VÉRIFICATION DE L'ÂGE", "#cc2222"),
                    ft.Container(height=8),
                    self._body("Cette section contient des informations sur des substances hormonales pouvant provoquer des dommages irréversibles sur un organisme en développement.\n\nL'accès est STRICTEMENT INTERDIT aux personnes de moins de 21 ans."),
                    ft.Container(height=16),
                    ft.Text("Quelle est ton année de naissance ?", size=13, color=TEXT, weight=ft.FontWeight.BOLD),
                    ft.Container(height=6),
                    year_field,
                    err_text,
                    ft.Container(height=12),
                    ft.Row([
                        mk_btn("Continuer →", _validate, color="#1a4a1a", hover="#2a6a2a", width=160, height=40),
                    ]),
                ], spacing=8),
                padding=ft.Padding.all(24),
                bgcolor=BG_CARD, border_radius=R_CARD,
                border=ft.Border.all(1, BORDER),
                margin=ft.Margin.all(16),
            )
        )
        self.page.update()

    # ── Étape 2 : Expérience ─────────────────────────────────────────────────

    def _show_step2(self):
        self._clear()
        exp_q = [
            ("Depuis combien d'années pratiques-tu la musculation sérieusement ?",
             ["Moins de 2 ans","2 à 4 ans","5 ans ou plus"], "5 ans ou plus",
             "Moins de 5 ans d'entraînement = potentiel naturel non exploité."),
            ("As-tu réalisé un bilan hormonal complet (LH/FSH/Testo/SHBG/E2) ?",
             ["Non, jamais","Oui, partiellement","Oui, bilan complet avec résultats en main"],
             "Oui, bilan complet avec résultats en main",
             "Sans baseline hormonale, tu es aveugle sur l'impact du cycle."),
            ("As-tu un suivi médical actif (médecin du sport ou endocrinologue) ?",
             ["Non","J'en ai un mais il n'est pas au courant","Oui, mon médecin est informé"],
             "Oui, mon médecin est informé",
             "Un suivi médical est non négociable pour détecter les problèmes précocement."),
        ]

        dropdowns = []
        for q_text, opts, _, _ in exp_q:
            dd = mk_dropdown(q_text[:40] + "…", opts, value=opts[0], width=340)
            dropdowns.append((dd, opts[-1], _))

        err_text = ft.Text("", size=11, color=DANGER)

        def _validate(e=None):
            failed = [reason for (dd, expected, reason) in dropdowns if dd.value != expected]
            if failed:
                self._refuse("\n\n".join(failed)); return
            self._show_step3()

        controls = [
            self._header("ÉTAPE 2 / 4 — QUALIFICATION D'EXPÉRIENCE", "#cc6600"),
            ft.Container(height=8),
            self._body("Réponds honnêtement. Il n'y a pas de bonne réponse pour faire plaisir."),
            ft.Container(height=12),
        ]
        for i, (q_text, opts, _, _) in enumerate(exp_q):
            dd, _, _ = dropdowns[i]
            controls += [
                ft.Text(f"{i+1}. {q_text}", size=12, color=TEXT),
                dd,
                ft.Container(height=8),
            ]
        controls += [
            err_text,
            ft.Container(height=8),
            ft.Row([mk_btn("Continuer →", _validate, color="#cc6600", hover="#aa5500", width=160, height=40)]),
        ]

        self.root_col.controls.append(
            ft.Container(
                content=ft.Column(controls, spacing=6),
                padding=ft.Padding.all(24),
                bgcolor=BG_CARD, border_radius=R_CARD,
                border=ft.Border.all(1, BORDER),
                margin=ft.Margin.all(16),
            )
        )
        self.page.update()

    # ── Étape 3 : QCM ────────────────────────────────────────────────────────

    def _show_step3(self):
        self._clear()
        q_controls = []
        answer_groups = []

        for idx, q in enumerate(_KNOWLEDGE_QUESTIONS):
            selected_val = {"v": None}
            radio_group = ft.RadioGroup(
                content=ft.Column([
                    ft.Radio(value=c[0], label=c, label_style=ft.TextStyle(color=TEXT, size=12))
                    for c in q["choices"]
                ], spacing=4),
                on_change=lambda e, sv=selected_val: sv.update({"v": e.control.value}),
            )
            answer_groups.append((q["answer"], selected_val, q["explication"]))
            q_controls += [
                ft.Text(f"Q{idx+1}. {q['q']}", size=12, color=TEXT, weight=ft.FontWeight.BOLD),
                radio_group,
                ft.Container(height=8),
            ]

        err_text = ft.Text("", size=11, color=DANGER)

        def _validate(e=None):
            wrong = []
            for (correct, sv, expl) in answer_groups:
                if sv.get("v") != correct:
                    wrong.append(expl)
            if wrong:
                self._refuse("Tu as échoué au QCM.\n\n" + "\n\n".join(wrong[:2])); return
            self._show_step4()

        self.root_col.controls.append(
            ft.Container(
                content=ft.Column([
                    self._header("ÉTAPE 3 / 4 — QCM DE CONNAISSANCES", "#aa8800"),
                    ft.Container(height=8),
                    self._body("5 questions. Toutes doivent être correctes."),
                    ft.Container(height=12),
                    *q_controls,
                    err_text,
                    ft.Row([mk_btn("Valider →", _validate, color="#aa8800", hover="#887700", width=160, height=40)]),
                ], spacing=6, scroll=ft.ScrollMode.AUTO),
                padding=ft.Padding.all(24),
                bgcolor=BG_CARD, border_radius=R_CARD,
                border=ft.Border.all(1, BORDER),
                margin=ft.Margin.all(16),
                height=500,
            )
        )
        self.page.update()

    # ── Étape 4 : Confirmation ────────────────────────────────────────────────

    def _show_step4(self):
        self._clear()
        confirm_field = mk_entry(label="Phrase de confirmation", hint=_CONFIRM_PHRASE, width=340)
        err_text = ft.Text("", size=11, color=DANGER)

        def _validate(e=None):
            if confirm_field.value.strip().upper() != _CONFIRM_PHRASE:
                err_text.value = f"⚠  Saisis exactement : {_CONFIRM_PHRASE}"; self.page.update(); return
            # Marquer qualifié en DB
            class _F:
                def __init__(s, cu): s.current_user = cu
            try:
                _db.set_cycle_qualified(_F(self.app_state.get("current_user", "")))
            except Exception:
                pass
            self.on_qualified()

        self.root_col.controls.append(
            ft.Container(
                content=ft.Column([
                    self._header("ÉTAPE 4 / 4 — CONFIRMATION", "#44aa44"),
                    ft.Container(height=8),
                    self._body(
                        "Tu as répondu correctement à toutes les questions.\n\n"
                        "En confirmant, tu reconnais :\n"
                        "• Être majeur(e) et avoir plus de 21 ans\n"
                        "• Avoir un suivi médical actif\n"
                        "• Comprendre les risques irréversibles liés aux substances hormonales\n"
                        "• Avoir pris cette décision de façon autonome et éclairée\n\n"
                        f"Tape exactement : {_CONFIRM_PHRASE}"
                    ),
                    ft.Container(height=16),
                    confirm_field,
                    err_text,
                    ft.Container(height=12),
                    ft.Row([mk_btn("✓  CONFIRMER ET ACCÉDER", _validate, color=SUCCESS, hover=SUCCESS_HVR, width=240, height=44)]),
                ], spacing=8),
                padding=ft.Padding.all(24),
                bgcolor=BG_CARD, border_radius=R_CARD,
                border=ft.Border.all(1, BORDER),
                margin=ft.Margin.all(16),
            )
        )
        self.page.update()


# ══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE PUBLIC
# ══════════════════════════════════════════════════════════════════════════════

def build_cycle_screen(page: ft.Page, app_state: dict) -> ft.Column:
    """
    Point d'entrée principal.
    Vérifie si l'utilisateur est qualifié → affiche qualification ou module cycle.
    """
    # Vérification qualification en DB
    qualified = False
    try:
        class _F:
            def __init__(self, cu): self.current_user = cu
        qualified = _db.is_cycle_qualified(_F(app_state.get("current_user", "")))
    except Exception:
        pass

    result_col = ft.Column(spacing=0)

    if qualified:
        view = CycleView(page, app_state)
        result_col.controls.append(view.get_view())
    else:
        def _on_qualified():
            result_col.controls.clear()
            v = CycleView(page, app_state)
            result_col.controls.append(v.get_view())
            page.update()

        qual = QualificationView(page, app_state, on_qualified=_on_qualified)
        result_col.controls.append(qual.get_view())

    return result_col
