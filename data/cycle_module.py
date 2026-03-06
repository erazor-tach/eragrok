# cycle_module.py — version finale avec presets de cycle (12, 16, Personnalisé)
# Layout modifié : sections empilées verticalement (une sous l'autre)
import os
import csv
import re
import math
from pathlib import Path
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from tkcalendar import Calendar
from data import utils
from data import db as _db
from data.theme import (
    TH, mk_btn, mk_card, mk_card2, mk_entry,
    mk_textbox, mk_label, mk_title, mk_sep,
    mk_scrollframe, screen_header, apply_treeview_style,
)

# --- Catégories et items -----------------------------------------------------
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
    # ── Base cycle ────────────────────────────────────────────────────────────
    0: [
        "Sustanon 250/300/350",
        "Testosterone Enanthate",
        "Testosterone Cypionate",
        "Testosterone Propionate",
        "Testosterone Undecanoate (Nebido)",
    ],
    # ── Anabolisants injectables (sans testostérones) ─────────────────────────
    1: [
        "Boldenone Undecylenate (Equipoise)",
        "Drostanolone Enanthate (Masteron E)",
        "Drostanolone Propionate (Masteron P)",
        "Methenolone Enanthate (Primobolan)",
        "Nandrolone Decanoate (Deca)",
        "Nandrolone Phenylpropionate (NPP)",
        "Trenbolone Hexahydrobenzylcarbonate",
        "Trenbolone Acetate",
        "Trenbolone Enanthate",
        "Stanozolol Injection (Winstrol depot)",
        "Cut Stack (mix Tren/Mast/Test)",
    ],
    # ── Anabolisants oraux ────────────────────────────────────────────────────
    2: [
        "Mesterolone (Proviron)",
        "Methandienone (Dianabol)",
        "Oxandrolone (Anavar)",
        "Oxymetholone (Anadrol)",
        "Stanozolol oral (Winstrol)",
        "Turinabol",
        "Halotestin",
        "Primobolan tablets",
    ],
    # ── Peptides ──────────────────────────────────────────────────────────────
    3: [
        "Melanotan 2",
        "BPC-157",
        "TB-500",
        "CJC-1295 sans DAC",
        "CJC-1295 with DAC",
        "Ipamorelin",
        "GHRP-6",
        "GHRP-2",
        "HGH Fragment 176-191",
        "PEG MGF",
        "Tirzepatide",
        "Semaglutide",
    ],
    # ── Hormones ─────────────────────────────────────────────────────────────
    4: [
        "HGH Somatropin",
        "HCG",
        "Liothyronine T3",
        "Lévothyroxine T4",
        "Insulin (listed for completeness only)",
        "IGF-1 LR3",
    ],
    # ── PCT : uniquement Clomid + Nolvadex ───────────────────────────────────
    5: [
        "Clomiphene (Clomid)",
        "Tamoxifen (Nolvadex)",
    ],
    # ── Anti-Aromatases & Anti-Prolactine ─────────────────────────────────────
    6: [
        "Anastrozole (Arimidex)",
        "Exemestane (Aromasin)",
        "Letrozole (Femara)",
        "Cabergoline (Dostinex)",
    ],
}

# --- Informations produits (version corrigée) --------------------------------
PRODUCT_INFO = {
    "Boldenone Undecylenate (Equipoise)": {
        "utilite": "Masse maigre, vascularité, appétit",
        "dose_min": "300–400 mg/sem",
        "dose_max": "800–1200 mg/sem",
        "popularite": "★★★☆☆",
        "dangerosite": "★★★☆☆",
        "demi_vie": "~14 jours",
        "notes": "RBC très haut, anxiété, appétit incontrôlable",
    },
    "Drostanolone Enanthate (Masteron E)": {
        "utilite": "Hardness, anti-estro, sèche finale",
        "dose_min": "200–300 mg/sem",
        "dose_max": "600 mg/sem",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "~8–10 jours",
        "notes": "Chute cheveux si prédisposé, articulations sèches",
    },
    "Drostanolone Propionate (Masteron P)": {
        "utilite": "Hardness rapide, prépa contest",
        "dose_min": "300–400 mg/sem",
        "dose_max": "600–700 mg/sem",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "~3 jours",
        "notes": "Pins fréquents, effet plus aigu que Enanthate",
    },
    "Methenolone Enanthate (Primobolan)": {
        "utilite": "Masse très propre, zéro rétention",
        "dose_min": "400 mg/sem",
        "dose_max": "800–1000 mg/sem",
        "popularite": "★★★★☆",
        "dangerosite": "★☆☆☆☆",
        "demi_vie": "~10 jours",
        "notes": "Très sûr, cher, beaucoup de faux",
    },
    "Nandrolone Decanoate (Deca)": {
        "utilite": "Masse, récupération articulaire",
        "dose_min": "300 mg/sem",
        "dose_max": "600–800 mg/sem",
        "popularite": "★★★★★",
        "dangerosite": "★★★★☆",
        "demi_vie": "~7–15 jours",
        "notes": "Prolactine, 'Deca dick', rétention d'eau",
    },
    "Nandrolone Phenylpropionate (NPP)": {
        "utilite": "Deca rapide, moins de rétention",
        "dose_min": "300 mg/sem",
        "dose_max": "600 mg/sem",
        "popularite": "★★★★☆",
        "dangerosite": "★★★★☆",
        "demi_vie": "~4–5 jours",
        "notes": "Effets similaires à Deca mais kick plus rapide",
    },
    "Trenbolone Hexahydrobenzylcarbonate": {
        "utilite": "Force, densité, sèche extrême",
        "dose_min": "152–228 mg/sem",
        "dose_max": "300–400 mg/sem",
        "popularite": "★★★★★",
        "dangerosite": "★★★★★",
        "demi_vie": "~14 jours",
        "notes": "Sueurs, agressivité, cardio affecté, insomnie",
    },
    "Sustanon 250/300/350": {
        "utilite": "Base polyvalente, kick + longue durée",
        "dose_min": "250–375 mg/sem",
        "dose_max": "750–1000 mg/sem",
        "popularite": "★★★★★",
        "dangerosite": "★★★☆☆",
        "demi_vie": "mix 7–15 jours",
        "notes": "Œstrogènes variables selon batch",
    },
    "Testosterone Enanthate": {
        "utilite": "Base (masse/force)",
        "dose_min": "250–500 mg/sem",
        "dose_max": "1000–2000 mg/sem",
        "popularite": "★★★★★",
        "dangerosite": "★★★☆☆",
        "demi_vie": "~8–10 jours",
        "notes": "Œstrogènes, risque de gynécomastie sans IA",
    },
    "Testosterone Cypionate": {
        "utilite": "Similaire à Enanthate",
        "dose_min": "250–500 mg/sem",
        "dose_max": "1000–2000 mg/sem",
        "popularite": "★★★★★",
        "dangerosite": "★★★☆☆",
        "demi_vie": "~8–12 jours",
        "notes": "Effets similaires à Enanthate",
    },
    "Testosterone Propionate": {
        "utilite": "Base courte, sèche, kick rapide",
        "dose_min": "100 mg EOD",
        "dose_max": "150–200 mg EOD",
        "popularite": "★★★★☆",
        "dangerosite": "★★★☆☆",
        "demi_vie": "~2–3 jours",
        "notes": "Injections fréquentes, douloureuses",
    },
    "Trenbolone Acetate": {
        "utilite": "Force, sèche, recomposition extrême",
        "dose_min": "50–75 mg EOD",
        "dose_max": "100–150 mg EOD",
        "popularite": "★★★★★",
        "dangerosite": "★★★★★",
        "demi_vie": "~2–3 jours",
        "notes": "Cauchemars, cardio, agressivité, insomnie",
    },
    "Trenbolone Enanthate": {
        "utilite": "Tren longue durée",
        "dose_min": "200–300 mg/sem",
        "dose_max": "400–600 mg/sem",
        "popularite": "★★★★★",
        "dangerosite": "★★★★★",
        "demi_vie": "~8–10 jours",
        "notes": "Similaire à Acetate mais moins de 'pins'",
    },
    "Stanozolol Injection (Winstrol depot)": {
        "utilite": "Dureté, force sans prise de poids",
        "dose_min": "50 mg EOD",
        "dose_max": "100 mg EOD",
        "popularite": "★★★★☆",
        "dangerosite": "★★★★☆",
        "demi_vie": "~24 h",
        "notes": "Articulations sèches, impact sur le foie et cholestérol",
    },
    "Testosterone Undecanoate (Nebido)": {
        "utilite": "Testostérone longue durée",
        "dose_min": "1000 mg / 10–14 sem",
        "dose_max": "1000 mg / 8–10 sem",
        "popularite": "★★★☆☆",
        "dangerosite": "★★★☆☆",
        "demi_vie": "20–34 jours",
        "notes": "Très lent à monter/descendre",
    },
    "Cut Stack (mix Tren/Mast/Test)": {
        "utilite": "Coupe sèche ultra-agressive",
        "dose_min": "300–450 mg/sem (mix)",
        "dose_max": "600 mg/sem (mix)",
        "popularite": "★★★★☆",
        "dangerosite": "★★★★★",
        "demi_vie": "variable",
        "notes": "Cumul des effets secondaires des composants",
    },
    # Orals
    "Mesterolone (Proviron)": {
        "utilite": "Anti-œstro, libido, dureté",
        "dose_min": "25 mg/j",
        "dose_max": "50–100 mg/j",
        "popularite": "★★★★☆",
        "dangerosite": "★☆☆☆☆",
        "demi_vie": "~12 h",
        "notes": "Très sûr, souvent sous-dosé",
    },
    "Methandienone (Dianabol)": {
        "utilite": "Masse rapide + force",
        "dose_min": "20–30 mg/j",
        "dose_max": "50–80 mg/j",
        "popularite": "★★★★★",
        "dangerosite": "★★★★★",
        "demi_vie": "~4–6 h",
        "notes": "Hépatotoxicité, œstrogènes, rétention massive",
    },
    "Oxandrolone (Anavar)": {
        "utilite": "Sèche, force, perte graisse",
        "dose_min": "30–50 mg/j",
        "dose_max": "80–120 mg/j",
        "popularite": "★★★★★",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "~9–10 h",
        "notes": "Très cher, faux fréquent",
    },
    "Oxymetholone (Anadrol)": {
        "utilite": "Masse massive",
        "dose_min": "50 mg/j",
        "dose_max": "100–150 mg/j",
        "popularite": "★★★★☆",
        "dangerosite": "★★★★★",
        "demi_vie": "~8–9 h",
        "notes": "Foie très toxique, rétention importante",
    },
    "Stanozolol oral (Winstrol)": {
        "utilite": "Dureté, sèche, force",
        "dose_min": "30–50 mg/j",
        "dose_max": "80–100 mg/j",
        "popularite": "★★★★★",
        "dangerosite": "★★★★☆",
        "demi_vie": "~8–9 h",
        "notes": "Impact hépatique et articulations",
    },
    "Turinabol": {
        "utilite": "Masse maigre, force",
        "dose_min": "30–50 mg/j",
        "dose_max": "80–100 mg/j",
        "popularite": "★★★☆☆",
        "dangerosite": "★★★☆☆",
        "demi_vie": "~16 h",
        "notes": "Plus sûr que Dianabol",
    },
    "Halotestin": {
        "utilite": "Force pure (powerlifting)",
        "dose_min": "10–20 mg/j",
        "dose_max": "30–40 mg/j",
        "popularite": "★★★☆☆",
        "dangerosite": "★★★★★",
        "demi_vie": "~6–8 h",
        "notes": "Hépatotoxicité, agressivité",
    },
    "Primobolan tablets": {
        "utilite": "Coupe maigre qualité",
        "dose_min": "50–100 mg/j",
        "dose_max": "150 mg/j",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "~4–6 h",
        "notes": "Très cher, faux fréquent",
    },
    # Peptides / autres
    "Melanotan 2": {
        "utilite": "Bronzage, libido",
        "dose_min": "0.25–0.5 mg/j",
        "dose_max": "1–2 mg/j",
        "popularite": "★★★☆☆",
        "dangerosite": "★★★☆☆",
        "demi_vie": "—",
        "notes": "Nausées, érections spontanées",
    },
    "BPC-157": {
        "utilite": "Cicatrisation tendons/intestin",
        "dose_min": "250–500 mcg/j",
        "dose_max": "500–1000 mcg/j",
        "popularite": "★★★★★",
        "dangerosite": "★☆☆☆☆",
        "demi_vie": "—",
        "notes": "Très utilisé, profil de sécurité favorable",
    },
    "TB-500": {
        "utilite": "Cicatrisation, mobilité",
        "dose_min": "2–5 mg/sem",
        "dose_max": "7.5–10 mg/sem",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "Souvent combiné avec BPC-157",
    },
    "CJC-1295 sans DAC": {
        "utilite": "GH pulsatile",
        "dose_min": "100 mcg 3x/j",
        "dose_max": "200 mcg 3x/j",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "À combiner avec GHRP",
    },
    "CJC-1295 with DAC": {
        "utilite": "GH continue",
        "dose_min": "1–2 mg/sem",
        "dose_max": "2–4 mg/sem",
        "popularite": "★★★☆☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "Moins pulsatile",
    },
    "Ipamorelin": {
        "utilite": "GH doux, sélectif",
        "dose_min": "100–300 mcg 2–3x/j",
        "dose_max": "300 mcg 3x/j",
        "popularite": "★★★★☆",
        "dangerosite": "★☆☆☆☆",
        "demi_vie": "—",
        "notes": "Très sûr",
    },
    "GHRP-6": {
        "utilite": "GH + forte faim",
        "dose_min": "100 mcg 3x/j",
        "dose_max": "200 mcg 3x/j",
        "popularite": "★★★☆☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "Faim marquée",
    },
    "GHRP-2": {
        "utilite": "GH + appétit modéré",
        "dose_min": "100 mcg 3x/j",
        "dose_max": "200 mcg 3x/j",
        "popularite": "★★★☆☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "Moins d'appétit que GHRP-6",
    },
    "HGH Fragment 176-191": {
        "utilite": "Lipolyse ciblée",
        "dose_min": "250 mcg 2x/j",
        "dose_max": "500 mcg 2x/j",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "Pas d'effet GH global",
    },
    "PEG MGF": {
        "utilite": "Hypertrophie locale post-entraînement",
        "dose_min": "200 mcg post-ent",
        "dose_max": "400 mcg post-ent",
        "popularite": "★★★☆☆",
        "dangerosite": "★★★☆☆",
        "demi_vie": "—",
        "notes": "Site-specific",
    },
    "HCG": {
        "utilite": "Maintien testicules / testostérone",
        "dose_min": "250–500 UI 2x/sem",
        "dose_max": "1000–1500 UI 2x/sem",
        "popularite": "★★★★★",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "Peut augmenter œstrogènes",
    },
    "Tirzepatide": {
        "utilite": "Perte de poids",
        "dose_min": "2.5 mg/sem",
        "dose_max": "15 mg/sem",
        "popularite": "★★★★☆",
        "dangerosite": "★★★★☆",
        "demi_vie": "—",
        "notes": "Médicament officiel (Mounjaro)",
    },
    "Semaglutide": {
        "utilite": "Perte de poids",
        "dose_min": "0.25 mg/sem",
        "dose_max": "2.4 mg/sem",
        "popularite": "★★★★★",
        "dangerosite": "★★★★☆",
        "demi_vie": "—",
        "notes": "Médicament officiel (Ozempic/Wegovy)",
    },
    # Hormones / autres
    "HGH Somatropin": {
        "utilite": "Récupération, anti-âge, masse maigre",
        "dose_min": "2–4 UI/j",
        "dose_max": "6–10 UI/j",
        "popularite": "★★★★★",
        "dangerosite": "★★★★☆",
        "demi_vie": "—",
        "notes": "Cher, faux fréquent",
    },
    "Liothyronine T3": {
        "utilite": "Accélération métabolisme, perte de graisse",
        "dose_min": "25 mcg/j",
        "dose_max": "75–100 mcg/j",
        "popularite": "★★★★☆",
        "dangerosite": "★★★★☆",
        "demi_vie": "~1 jour",
        "notes": "Risque catabolisme musculaire si surdosé, sevrage progressif obligatoire",
        "oral": True,
    },
    "Lévothyroxine T4": {
        "utilite": "Métabolisme thyroïdien, énergie",
        "dose_min": "50–100 mcg/j",
        "dose_max": "200 mcg/j",
        "popularite": "★★★☆☆",
        "dangerosite": "★★★☆☆",
        "demi_vie": "~7 jours",
        "notes": "Conversion T4→T3, effets plus lents que T3 pure",
        "oral": True,
    },
    "IGF-1 LR3": {
        "utilite": "Hypertrophie locale + globale",
        "dose_min": "20–50 mcg/j",
        "dose_max": "80–120 mcg/j",
        "popularite": "★★★☆☆",
        "dangerosite": "★★★★★",
        "demi_vie": "—",
        "notes": "Très puissant, risque d'hypoglycémie",
    },
    # PCT / IA
    "Exemestane (Aromasin)": {
        "utilite": "Inhibiteur aromatase irréversible (stéroïdien)",
        "dose_min": "12.5 mg EOD",
        "dose_max": "25 mg/j",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "~24h",
        "notes": "Départ recommandé : 12.5 mg EOD. Prendre le lendemain de l'injection de testostérone. Impact modéré sur lipides. Avantage : légèrement anabolique.",
        "timing": "Lendemain injection testo — EOD",
        "oral": True,
    },
    "Letrozole (Femara)": {
        "utilite": "Inhibiteur aromatase très puissant",
        "dose_min": "0.25 mg EOD",
        "dose_max": "2.5 mg/j",
        "popularite": "★★★☆☆",
        "dangerosite": "★★★☆☆",
        "demi_vie": "~48h",
        "notes": "Départ : 0.25 mg EOD — très puissant, crash œstrogènes possible. Réserver aux cas résistants à l'Anastrozole.",
        "timing": "EOD — surveiller estradiol toutes les 4 semaines",
        "oral": True,
    },
    "Clomiphene (Clomid)": {
        "utilite": "Relance axe HPTA (PCT)",
        "dose_min": "25–50 mg/j",
        "dose_max": "100 mg/j",
        "popularite": "★★★★★",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "~5–7 jours",
        "notes": "PCT uniquement — commence 14 jours après dernière injection. Vision floue possible (réduire dose). Ne pas utiliser pendant le cycle.",
        "timing": "J14 post-cycle — matin à jeun",
        "oral": True,
    },
    "Tamoxifen (Nolvadex)": {
        "utilite": "Relance HPTA + bloc périphérique œstrogène (PCT)",
        "dose_min": "20 mg/j",
        "dose_max": "40 mg/j",
        "popularite": "★★★★★",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "~5–7 jours",
        "notes": "PCT uniquement — commence 14 jours après dernière injection. Complément idéal au Clomid. Ne pas combiner avec Letrozole (bloque absorption).",
        "timing": "J14 post-cycle — à prendre avec nourriture",
        "oral": True,
    },
    "Anastrozole (Arimidex)": {
        "utilite": "Inhibiteur aromatase réversible (pendant cycle)",
        "dose_min": "0.25 mg EOD",
        "dose_max": "1 mg/j",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "~48h",
        "notes": "Départ recommandé : 0.25 mg EOD à partir de S2. Prendre le lendemain de l'injection testo. Ajuster selon estradiol (cible 20–30 pg/mL). Baisser dose si douleurs articulaires.",
        "timing": "Lendemain injection testo — EOD à partir de S2",
        "oral": True,
    },
    "Cabergoline (Dostinex)": {
        "utilite": "Contrôle prolactine (Tren/Deca)",
        "dose_min": "0.25 mg 2x/sem",
        "dose_max": "0.5–1 mg 2x/sem",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "~65h",
        "notes": "Essentiel avec Trenbolone ou Nandrolone. Prendre de préférence le soir avec nourriture (nausées). Départ : 0.25 mg 2x/sem.",
        "timing": "Soir avec nourriture — 2x/semaine",
        "oral": True,
    },
}

# ── Produits oraux : pas de calculateur vials ─────────────────────────────────
_ORAL_PRODUCTS = (
    set(CATEGORY_ITEMS.get(2, []))   # oraux anabolisants
    | set(CATEGORY_ITEMS.get(5, []))  # PCT
    | set(CATEGORY_ITEMS.get(6, []))  # IA (comprimés)
    | {"Liothyronine T3", "Lévothyroxine T4"}
)

# ── IA anti-aromatase (pendant cycle) — cat 6 ────────────────────────────────
_AI_PRODUCTS = set(CATEGORY_ITEMS.get(6, [])) - {"Cabergoline (Dostinex)"}

# ── Anti-prolactine ────────────────────────────────────────────────────────────
_ANTI_PROLACTIN = {"Cabergoline (Dostinex)"}

# ── Testostérones + composés aromatisants ────────────────────────────────────
_AROMATIZING_TEST = set(CATEGORY_ITEMS.get(0, [])) | {
    "Methandienone (Dianabol)", "Boldenone Undecylenate (Equipoise)",
}

# ── Produits hCG ─────────────────────────────────────────────────────────────
_HCG_PRODUCTS_SET = {"HCG"}

# ── PCT strict (J14 post-cycle) ───────────────────────────────────────────────
_PCT_STRICT = set(CATEGORY_ITEMS.get(5, []))

# ── Durée de wash-out par ester (en semaines) ─────────────────────────────────
_ESTER_WASHOUT = {
    "Testosterone Enanthate":          2,
    "Testosterone Cypionate":          2,
    "Testosterone Propionate":         1,   # 3 jours → arrondi 1 sem
    "Testosterone Undecanoate (Nebido)": 4,
    "Sustanon 250/300/350":            3,
    "Boldenone Undecylenate (Equipoise)": 4,
    "Nandrolone Decanoate (Deca)":     3,
    "Nandrolone Phenylpropionate (NPP)": 1,
    "Trenbolone Enanthate":            2,
    "Trenbolone Acetate":              1,
    "Trenbolone Hexahydrobenzylcarbonate": 3,
    "Drostanolone Enanthate (Masteron E)": 2,
    "Drostanolone Propionate (Masteron P)": 1,
    "Methenolone Enanthate (Primobolan)": 2,
    "Cut Stack (mix Tren/Mast/Test)":  2,
}

# ── Alertes bilan sanguin par produit ─────────────────────────────────────────
_BILAN_TRIGGERS = {
    "oraux":     "ALAT / ASAT (toxicité hépatique) toutes les 4 semaines",
    "boldenone": "Hématocrite toutes les 4 semaines (risque polyglobulie)",
    "prolactin": "Prolactine à S4 et S8 (Tren/Deca)",
    "lipides":   "Bilan lipidique HDL/LDL à S4 et S8",
    "hormonal":  "Bilan hormonal complet (Testo/LH/FSH/Estradiol) 4 semaines post-PCT",
}

# --- Helpers pour compatibilité thème -----------------------------------------
def _hover_attr(name: str):
    """Retourne la valeur hover depuis TH en testant les variantes courantes."""
    for suffix in ("_HVR", "_HOVER"):
        attr = f"{name}{suffix}"
        if hasattr(TH, attr):
            return getattr(TH, attr)
    return None


def _btn_safe(parent, text, cmd, color_attr, width=None, height=None, **kwargs):
    """
    Wrapper pour mk_btn qui évite de passer des clés en double à CTkButton.
    mk_btn semble déjà gérer la couleur en interne ; on évite donc d'envoyer
    'fg_color' ou 'hover_color' via **kwargs pour prévenir la duplication.
    """
    _ = getattr(TH, color_attr, None)
    _hover = _hover_attr(color_attr)

    params = {}
    if width is not None:
        params["width"] = width
    if height is not None:
        params["height"] = height
    for k, v in kwargs.items():
        if k in ("fg_color", "hover_color"):
            continue
        params[k] = v

    return mk_btn(parent, text, cmd, **params)


def _user_dir(app):
    d = os.path.join(utils.USERS_DIR, app.current_user)
    Path(d).mkdir(parents=True, exist_ok=True)
    return d


# --- Helpers pour cycle presets -----------------------------------------------
def _apply_cycle_preset(app, preset):
    """Applique un preset sur le champ longueur et, pour premier cycle, pré-sélectionne les produits."""
    length_map = {"12 semaines": "12", "16 semaines": "16", "Premier Cycle": "12"}
    val = length_map.get(preset)
    if val:
        try:
            app.cycle_length_var.set(val)
        except Exception:
            try:
                app.cycle_length_entry.delete(0, tk.END)
                app.cycle_length_entry.insert(0, val)
            except Exception:
                pass

    if preset == "Premier Cycle":
        # Pré-sélectionner : Testosterone Enanthate (cat0) + HCG (cat4) + Anastrozole (cat6)
        for cid, lb in getattr(app, "cycle_category_listboxes", {}).items():
            try:
                lb.selection_clear(0, tk.END)
                items = CATEGORY_ITEMS.get(cid, [])
                targets = {
                    0: "Testosterone Enanthate",
                    4: "HCG",
                    6: "Anastrozole (Arimidex)",
                    5: "Clomiphene (Clomid)",
                }
                target = targets.get(cid)
                if target and target in items:
                    lb.selection_set(items.index(target))
            except Exception:
                pass
        # Pré-remplir doses
        def _safe_preset():
            try:
                _preset_premier_cycle_doses(app)
            except Exception:
                pass
        app.root.after(100, _safe_preset)

    try:
        app.cycle_length_entry.pack_forget()
        app.cycle_length_entry.pack(side=tk.LEFT, padx=(4, 0))
        if preset == "Personnalisé":
            app.cycle_length_entry.configure(state="normal")
        else:
            app.cycle_length_entry.configure(state="readonly")
    except Exception:
        pass


def _preset_premier_cycle_doses(app):
    """Applique les doses conseillées pour un premier cycle."""
    defaults = {
        "Testosterone Enanthate": "400",
        "HCG":                    "500",
        "Anastrozole (Arimidex)": "0.25",
        "Clomiphene (Clomid)":    "50",
    }
    for prod, dose in defaults.items():
        entry = getattr(app, "cycle_product_doses", {}).get(prod)
        if entry:
            try:
                current = entry.get().strip()
                if not current:
                    entry.delete(0, tk.END)
                    entry.insert(0, dose)
            except Exception:
                pass
    _update_advice_summary(app)

# ══════════════════════════════════════════════════════════════════════════════
#  SYSTÈME DE QUALIFICATION

# Questions de connaissance — l'utilisateur doit tout réussir
_KNOWLEDGE_QUESTIONS = [
    {
        "q": "Qu'est-ce que la suppression de l'axe HPTA ?",
        "choices": [
            "A — Un effet bénéfique qui augmente la production naturelle de testostérone",
            "B — L'arrêt partiel ou total de la production hormonale naturelle par le cerveau",
            "C — Un simple déséquilibre temporaire sans conséquence",
            "D — Un terme désignant la prise de masse musculaire rapide",
        ],
        "answer": "B",
        "explication": "La suppression HPTA signifie que l'hypothalamus et l'hypophyse "
                       "cessent de stimuler les testicules. Sans PCT, cette suppression "
                       "peut devenir permanente (hypogonadisme définitif).",
    },
    {
        "q": "Quelle est la principale conséquence cardiovasculaire des stéroïdes anabolisants ?",
        "choices": [
            "A — Une amélioration de la circulation sanguine",
            "B — Une augmentation du HDL (bon cholestérol)",
            "C — Une chute du HDL, hausse du LDL, hypertrophie du ventricule gauche, risque d'infarctus",
            "D — Aucune conséquence documentée sur le cœur",
        ],
        "answer": "C",
        "explication": "Les AAS sont fortement associés à la cardiomyopathie, "
                       "à des profils lipidiques athérogènes et à des morts subites "
                       "cardiaques, y compris chez des athlètes jeunes.",
    },
    {
        "q": "Qu'est-ce que l'hépatotoxicité des stéroïdes oraux alkylés en C17-alpha ?",
        "choices": [
            "A — Une toxicité rénale sans gravité",
            "B — Une augmentation temporaire des enzymes hépatiques sans risque",
            "C — Une toxicité hépatique pouvant mener à la peliose, à la cholestase ou au carcinome hépatocellulaire",
            "D — Un terme marketing sans réalité clinique",
        ],
        "answer": "C",
        "explication": "Les oraux alkylés (Dianabol, Anadrol, Winstrol…) résistent "
                       "à la dégradation hépatique, provoquant une charge toxique directe "
                       "sur le foie pouvant être irréversible.",
    },
    {
        "q": "Quel est le rôle du PCT (Post Cycle Therapy) ?",
        "choices": [
            "A — Accélérer la prise de masse après le cycle",
            "B — Relancer l'axe hypothalamo-hypophyso-gonadique supprimé pour restaurer la production endogène de testostérone",
            "C — Éliminer les stéroïdes du corps plus rapidement",
            "D — Prévenir uniquement la rétention d'eau",
        ],
        "answer": "B",
        "explication": "Sans PCT adapté, l'axe HPTA peut rester supprimé des mois "
                       "ou de façon permanente, entraînant dépression profonde, "
                       "infertilité, perte musculaire et dépendance aux hormones exogènes.",
    },
    {
        "q": "Pourquoi l'usage de stéroïdes anabolisants avant 21 ans est-il particulièrement dangereux ?",
        "choices": [
            "A — Ce n'est pas plus dangereux qu'après 21 ans",
            "B — Parce que l'axe hormonal et les os sont encore en développement — fermeture prématurée des cartilages de croissance, suppression définitive possible de l'axe HPTA",
            "C — Uniquement à cause des risques d'acné",
            "D — Parce que les effets sont moins visibles à cet âge",
        ],
        "answer": "B",
        "explication": "Avant 21 ans, le système endocrinien n'est pas mature. "
                       "Une intervention exogène peut stopper définitivement le développement "
                       "naturel et causer des dommages irréversibles sur la croissance "
                       "et la fertilité.",
    },
]

_CONFIRM_PHRASE = "J'AI PRIS MA DÉCISION EN CONNAISSANCE DE CAUSE"


def show_cycle_disclaimer(app):
    """
    Point d'entrée cycle. Vérifie d'abord le fichier de qualification sur disque.
    """
    # Vérifier sur disque (persiste entre sessions)
    user = getattr(app, "current_user", None)
    if user:
        try:
            if _db.is_cycle_qualified(app):
                app.cycle_disclaimer_shown = True
        except Exception:
            pass

    if getattr(app, "cycle_disclaimer_shown", False):
        show_cycle_screen(app)
        return
    _run_qualification(app)


def _run_qualification(app):
    """Lance la fenêtre de qualification multi-étapes."""

    dlg = ctk.CTkToplevel(app.root)
    dlg.title("⛔  Accès restreint — Qualification requise")
    dlg.geometry("820x780")
    dlg.minsize(700, 500)
    dlg.resizable(True, True)
    dlg.configure(fg_color="#0d0d0d")
    dlg.grab_set()
    dlg.focus_set()
    dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)

    # État interne
    state = {
        "step": 1,
        "answers": {},
        "score": 0,
    }

    # ── Zone scrollable — rechargée à chaque étape ────────────────────────────
    _scroll_container = [None]   # liste pour pouvoir la remplacer depuis les closures

    def _make_scroll():
        """Recrée un CTkScrollableFrame frais."""
        if _scroll_container[0] is not None:
            try:
                _scroll_container[0].destroy()
            except Exception:
                pass
        sf = ctk.CTkScrollableFrame(dlg, fg_color="transparent",
                                     scrollbar_button_color="#333333",
                                     scrollbar_button_hover_color="#555555")
        sf.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        _scroll_container[0] = sf
        return sf

    # Les helpers _header/_body/_clear opèrent sur content (alias vers le scrollframe courant)
    # On les définit comme closures qui lisent _scroll_container[0]

    def _clear():
        sf = _make_scroll()   # recrée le scrollframe = tout vide
        return sf             # retourne le nouveau content

    def _header(content, text, color="#cc2222"):
        ctk.CTkLabel(content, text=text, font=("Inter", 15, "bold"),
                     text_color=color, anchor="w",
                     wraplength=700).pack(anchor=tk.W, padx=28, pady=(22, 4))
        ctk.CTkFrame(content, fg_color=color, height=2).pack(fill=tk.X, padx=28, pady=(0, 16))

    def _body(content, text, color="#c0c0c0"):
        ctk.CTkLabel(content, text=text, font=("Inter", 12),
                     text_color=color, anchor="w",
                     justify="left", wraplength=720).pack(anchor=tk.W, padx=28, pady=(0, 12))

    def _refuse(reason=""):
        sf = _clear()
        ctk.CTkLabel(sf, text="⛔  ACCÈS REFUSÉ",
                     font=("Inter", 22, "bold"), text_color="#cc0000").pack(pady=(60, 16))
        ctk.CTkLabel(sf, text=reason or "Tu ne remplis pas les conditions d'accès.",
                     font=("Inter", 12), text_color="#888888",
                     wraplength=680, justify="center").pack(padx=28, pady=(0, 24))
        ctk.CTkLabel(
            sf,
            text="Cet outil est réservé aux adultes expérimentés qui ont déjà pris leur décision "
                 "de façon autonome et éclairée, accompagnés d'un suivi médical.\n\n"
                 "Si tu envisages d'utiliser des substances hormonales sans ce background, "
                 "consulte d'abord un médecin endocrinologue ou du sport.",
            font=("Inter", 11), text_color="#666666",
            wraplength=680, justify="center",
        ).pack(padx=28)
        ctk.CTkButton(
            sf, text="Fermer", width=140, height=38,
            fg_color="#333333", hover_color="#444444", text_color="#aaaaaa",
            command=dlg.destroy,
        ).pack(pady=30)

    # ════════════════════════════════════════════════════════════════════════
    #  ÉTAPE 1 — ÂGE
    # ════════════════════════════════════════════════════════════════════════
    def _step1():
        sf = _clear()
        _header(sf, "ÉTAPE 1 / 4 — VÉRIFICATION DE L'ÂGE", "#cc2222")
        _body(sf,
            "Cette section contient des informations sur des substances hormonales et anabolisantes "
            "qui peuvent provoquer des dommages irréversibles sur un organisme en développement.\n\n"
            "L'accès est STRICTEMENT INTERDIT aux personnes de moins de 21 ans.\n"
            "En dessous de 21 ans, l'axe hormonal n'est pas mature. "
            "Une interférence exogène peut stopper définitivement ton développement naturel, "
            "détruire ta fertilité et créer une dépendance hormonale à vie."
        )
        ctk.CTkLabel(sf, text="Quelle est ton année de naissance ?",
                     font=("Inter", 13, "bold"), text_color="#dddddd").pack(anchor=tk.W, padx=28, pady=(8, 4))

        year_var = tk.StringVar()
        year_entry = ctk.CTkEntry(sf, textvariable=year_var, width=120,
                                   placeholder_text="ex: 1990",
                                   font=("Inter", 14), height=40)
        year_entry.pack(anchor=tk.W, padx=28, pady=(0, 16))
        year_entry.focus_set()

        err_lbl = ctk.CTkLabel(sf, text="", font=("Inter", 11), text_color="#ff4444")
        err_lbl.pack(anchor=tk.W, padx=28)

        def _validate_age():
            try:
                birth_year = int(year_var.get().strip())
            except ValueError:
                err_lbl.configure(text="⚠  Saisis une année valide (ex: 1990).")
                return
            current_year = datetime.now().year
            age = current_year - birth_year
            if age < 0 or birth_year < 1920:
                err_lbl.configure(text="⚠  Année invalide.")
                return
            if age < 18:
                _refuse(
                    "Tu es mineur(e).\n\n"
                    "L'accès à ces informations t'est totalement interdit. "
                    "Concentre-toi sur ton entraînement naturel — à ton âge, "
                    "ton potentiel hormonal est à son maximum. "
                    "Les substances exogènes ne feraient que le détruire."
                )
                return
            if age < 21:
                _refuse(
                    f"Tu as {age} ans.\n\n"
                    "L'accès est refusé aux moins de 21 ans.\n\n"
                    "Ton axe HPTA n'est pas encore pleinement mature. "
                    "Une suppression à cet âge peut être définitive. "
                    "Reviens dans quelques années, si tu maintiens cette décision après "
                    "un bilan médical complet avec un endocrinologue."
                )
                return
            state["step"] = 2
            _step2()

        btn_frame = ctk.CTkFrame(sf, fg_color="transparent")
        btn_frame.pack(anchor=tk.W, padx=28, pady=(8, 40))
        ctk.CTkButton(btn_frame, text="Continuer →", width=160, height=40,
                      fg_color="#1a4a1a", hover_color="#2a6a2a", text_color="#aaffaa",
                      command=_validate_age).pack(side=tk.LEFT, padx=(0, 12))
        ctk.CTkButton(btn_frame, text="Quitter", width=120, height=40,
                      fg_color="#2a0000", hover_color="#3a0000", text_color="#ff8888",
                      command=dlg.destroy).pack(side=tk.LEFT)

    # ════════════════════════════════════════════════════════════════════════
    #  ÉTAPE 2 — QUALIFICATION D'EXPÉRIENCE
    # ════════════════════════════════════════════════════════════════════════
    def _step2():
        sf = _clear()
        _header(sf, "ÉTAPE 2 / 4 — QUALIFICATION D'EXPÉRIENCE", "#cc6600")
        _body(sf,
            "Réponds honnêtement. Il n'y a pas de bonne réponse pour faire plaisir — "
            "il y a uniquement des réponses qui montrent si tu es prêt(e) ou non.\n\n"
            "Un utilisateur non préparé ne met pas seulement sa santé en danger : "
            "il se retrouve seul face à des effets secondaires qu'il ne comprend pas, "
            "sans savoir quoi faire ni à qui parler.",
            "#999999",
        )

        questions = [
            (
                "Depuis combien d'années pratiques-tu la musculation de façon sérieuse et régulière ?",
                ["Moins de 2 ans", "2 à 4 ans", "5 ans ou plus"],
                "5 ans ou plus",
                "Moins de 5 ans d'entraînement sérieux signifie que tu n'as pas exploité "
                "ton potentiel naturel. Les substances ne compensent pas le manque de bases.",
            ),
            (
                "As-tu déjà réalisé un bilan hormonal complet (testostérone totale/libre, LH, FSH, SHBG, estradiol) ?",
                ["Non, jamais", "Oui, partiellement", "Oui, bilan complet avec résultats en main"],
                "Oui, bilan complet avec résultats en main",
                "Sans connaître ta baseline hormonale, tu es aveugle. "
                "Tu ne peux pas évaluer l'impact du cycle ni détecter une suppression durable.",
            ),
            (
                "Es-tu suivi(e) par un médecin (endocrinologue, médecin du sport, ou généraliste informé) ?",
                ["Non", "J'envisage de consulter", "Oui, suivi médical actif"],
                "Oui, suivi médical actif",
                "Sans suivi médical, tu n'as personne pour détecter une complication cardiovasculaire, "
                "hépatique ou hormonale à temps. Les urgences ne sont pas un plan B acceptable.",
            ),
            (
                "Connais-tu ta tension artérielle actuelle et ton bilan lipidique (HDL/LDL) ?",
                ["Non", "Approximativement", "Oui, valeurs récentes en main"],
                "Oui, valeurs récentes en main",
                "Les stéroïdes anabolisants détruisent le profil lipidique et augmentent la pression "
                "artérielle. Sans baseline, tu ne verras pas venir l'accident cardiaque.",
            ),
        ]

        q_vars = []
        for q_text, choices, correct, expl in questions:
            ctk.CTkLabel(sf, text=q_text, font=("Inter", 11, "bold"),
                         text_color="#cccccc", anchor="w",
                         wraplength=720).pack(anchor=tk.W, padx=28, pady=(12, 4))
            var = tk.StringVar(value="")
            for ch in choices:
                ctk.CTkRadioButton(
                    sf, text=ch, variable=var, value=ch,
                    font=("Inter", 11), text_color="#aaaaaa",
                    fg_color="#884400", hover_color="#aa5500",
                ).pack(anchor=tk.W, padx=44, pady=2)
            q_vars.append((var, correct, expl))

        err_lbl2 = ctk.CTkLabel(sf, text="", font=("Inter", 11),
                                 text_color="#ff4444", wraplength=720)
        err_lbl2.pack(anchor=tk.W, padx=28, pady=(8, 0))

        def _validate_exp():
            failures = []
            for (var, correct, explication) in q_vars:
                if var.get() == "":
                    err_lbl2.configure(text="⚠  Réponds à toutes les questions.")
                    return
                if var.get() != correct:
                    failures.append(explication)
            if failures:
                reason = "Tu ne remplis pas les prérequis d'expérience.\n\n"
                reason += "\n\n".join(f"• {f}" for f in failures)
                _refuse(reason)
                return
            state["step"] = 3
            _step3()

        btn_frame2 = ctk.CTkFrame(sf, fg_color="transparent")
        btn_frame2.pack(anchor=tk.W, padx=28, pady=(12, 40))
        ctk.CTkButton(btn_frame2, text="Continuer →", width=160, height=40,
                      fg_color="#1a4a1a", hover_color="#2a6a2a", text_color="#aaffaa",
                      command=_validate_exp).pack(side=tk.LEFT, padx=(0, 12))
        ctk.CTkButton(btn_frame2, text="Quitter", width=120, height=40,
                      fg_color="#2a0000", hover_color="#3a0000", text_color="#ff8888",
                      command=dlg.destroy).pack(side=tk.LEFT)

    # ════════════════════════════════════════════════════════════════════════
    #  ÉTAPE 3 — TEST DE CONNAISSANCE (5 questions, 5/5 obligatoires)
    # ════════════════════════════════════════════════════════════════════════
    def _step3():
        sf = _clear()
        _header(sf, "ÉTAPE 3 / 4 — TEST DE CONNAISSANCE MÉDICALE", "#886600")
        _body(sf,
            "5 questions. Tu dois répondre correctement à TOUTES.\n"
            "Ce test ne cherche pas à t'éliminer arbitrairement — il vérifie que tu comprends "
            "réellement ce que tu vas faire à ton corps. Si tu ne connais pas ces réponses, "
            "tu n'es pas prêt(e). Informe-toi d'abord.",
            "#888888",
        )

        q_vars3 = []
        for i, qdata in enumerate(_KNOWLEDGE_QUESTIONS):
            ctk.CTkLabel(
                sf,
                text=f"Q{i+1} — {qdata['q']}",
                font=("Inter", 11, "bold"), text_color="#cccccc",
                anchor="w", wraplength=720,
            ).pack(anchor=tk.W, padx=28, pady=(14, 4))
            var = tk.StringVar(value="")
            for ch in qdata["choices"]:
                letter = ch[0]
                ctk.CTkRadioButton(
                    sf, text=ch, variable=var, value=letter,
                    font=("Inter", 11), text_color="#aaaaaa",
                    fg_color="#665500", hover_color="#887700",
                ).pack(anchor=tk.W, padx=44, pady=2)
            q_vars3.append((var, qdata["answer"], qdata["explication"]))

        err_lbl3 = ctk.CTkLabel(sf, text="", font=("Inter", 11),
                                 text_color="#ff4444", wraplength=720)
        err_lbl3.pack(anchor=tk.W, padx=28, pady=(8, 0))

        def _validate_knowledge():
            wrong = []
            for i, (var, correct, expl) in enumerate(q_vars3):
                if var.get() == "":
                    err_lbl3.configure(text="⚠  Réponds à toutes les questions.")
                    return
                if var.get() != correct:
                    wrong.append(f"Q{i+1} : {expl}")
            if wrong:
                reason = (
                    f"Tu as répondu incorrectement à {len(wrong)}/5 question(s).\n\n"
                    "Tu dois tout réussir. Voici ce que tu n'as pas compris :\n\n"
                    + "\n\n".join(f"• {w}" for w in wrong)
                    + "\n\nInforme-toi sérieusement avant de revenir. "
                    "Ces lacunes peuvent te coûter ta santé."
                )
                _refuse(reason)
                return
            state["step"] = 4
            _step4()

        btn_frame3 = ctk.CTkFrame(sf, fg_color="transparent")
        btn_frame3.pack(anchor=tk.W, padx=28, pady=(12, 40))
        ctk.CTkButton(btn_frame3, text="Valider mes réponses →", width=200, height=40,
                      fg_color="#1a4a1a", hover_color="#2a6a2a", text_color="#aaffaa",
                      command=_validate_knowledge).pack(side=tk.LEFT, padx=(0, 12))
        ctk.CTkButton(btn_frame3, text="Quitter", width=120, height=40,
                      fg_color="#2a0000", hover_color="#3a0000", text_color="#ff8888",
                      command=dlg.destroy).pack(side=tk.LEFT)

    # ════════════════════════════════════════════════════════════════════════
    #  ÉTAPE 4 — ENGAGEMENT ACTIF + AVERTISSEMENT FINAL
    # ════════════════════════════════════════════════════════════════════════
    def _step4():
        sf = _clear()
        _header(sf, "ÉTAPE 4 / 4 — ENGAGEMENT FINAL", "#446644")
        _body(sf,
            "Tu as passé les étapes de qualification. Ce n'est pas une autorisation.\n\n"
            "Ce que tu t'apprêtes à utiliser peut :\n"
            "  — Supprimer définitivement ta production hormonale naturelle\n"
            "  — Provoquer un infarctus, un AVC ou une mort subite\n"
            "  — Détruire ton foie, tes reins, ta fertilité\n"
            "  — Créer une dépendance psychologique et physique à long terme\n"
            "  — Aggraver ou déclencher des troubles psychiatriques\n\n"
            "Aucun gain musculaire ne justifie ces risques si tu n'as pas pesé chaque conséquence. "
            "Ce logiciel est un outil de suivi pour ceux qui ont déjà pris leur décision. "
            "Il ne te conseille pas de l'utiliser. Il ne valide pas ton choix. "
            "Il t'aide simplement à ne pas te blesser davantage si tu es décidé(e).",
            "#888888",
        )
        ctk.CTkLabel(
            sf,
            text=f'Pour confirmer, recopie exactement la phrase suivante :\n"{_CONFIRM_PHRASE}"',
            font=("Inter", 12, "bold"), text_color="#aaaaaa",
            wraplength=720, anchor="w",
        ).pack(anchor=tk.W, padx=28, pady=(12, 6))

        confirm_var = tk.StringVar()
        confirm_entry = ctk.CTkEntry(
            sf, textvariable=confirm_var, width=680, height=44,
            placeholder_text="Recopie la phrase ici…",
            font=("Inter", 13),
        )
        confirm_entry.pack(anchor=tk.W, padx=28, pady=(0, 8))
        confirm_entry.focus_set()

        err_lbl4 = ctk.CTkLabel(sf, text="", font=("Inter", 11), text_color="#ff4444")
        err_lbl4.pack(anchor=tk.W, padx=28)

        def _final_confirm():
            typed = confirm_var.get().strip().casefold()
            if typed != _CONFIRM_PHRASE.casefold():
                err_lbl4.configure(
                    text=f'⚠  Phrase incorrecte. Recopie exactement : "{_CONFIRM_PHRASE}"'
                )
                return
            # Sauvegarder sur disque pour cet utilisateur
            if getattr(app, "current_user", None):
                try: _db.set_cycle_qualified(app)
                except Exception: pass
            dlg.destroy()
            app.cycle_disclaimer_shown = True
            show_cycle_screen(app)

        btn_frame4 = ctk.CTkFrame(sf, fg_color="transparent")
        btn_frame4.pack(anchor=tk.W, padx=28, pady=(14, 40))
        ctk.CTkButton(
            btn_frame4, text="✅  Confirmer l'accès", width=200, height=44,
            fg_color="#1a3a1a", hover_color="#2a5a2a", text_color="#88cc88",
            font=("Inter", 13, "bold"),
            command=_final_confirm,
        ).pack(side=tk.LEFT, padx=(0, 16))
        ctk.CTkButton(
            btn_frame4, text="❌  Quitter — je ne suis pas prêt(e)", width=280, height=44,
            fg_color="#2a0000", hover_color="#3a0000", text_color="#ff8888",
            font=("Inter", 12),
            command=dlg.destroy,
        ).pack(side=tk.LEFT)

    # Lancement
    _step1()


# ── Modal récapitulatif des produits sélectionnés -----------------------------
def _show_selected_products(app, selected_products):
    dlg = ctk.CTkToplevel(app.root)
    dlg.title("Détails des produits sélectionnés")
    dlg.geometry("1200x480")
    dlg.configure(fg_color=TH.BG_CARD)
    dlg.grab_set()
    dlg.focus_set()

    mk_title(dlg, "Détails des produits sélectionnés").pack(anchor=tk.W, padx=16, pady=(12, 6))
    mk_sep(dlg).pack(fill=tk.X, padx=16, pady=(0, 8))

    # Toutes les colonnes de PRODUCT_INFO
    cols = (
        "Produit",
        "Utilité principale",
        "Dose minimale",
        "Dose maximale",
        "Popularité",
        "Dangérosité",
        "Demi-vie",
        "Notes",
    )
    wrap = ctk.CTkFrame(dlg, fg_color="transparent")
    wrap.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))

    vsb = ttk.Scrollbar(wrap, orient="vertical")
    hsb = ttk.Scrollbar(dlg, orient="horizontal")

    tree = ttk.Treeview(wrap, columns=cols, show="headings", height=12,
                        yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)

    col_widths = {
        "Produit": 230,
        "Utilité principale": 220,
        "Dose minimale": 130,
        "Dose maximale": 130,
        "Popularité": 90,
        "Dangérosité": 90,
        "Demi-vie": 90,
        "Notes": 280,
    }
    for c in cols:
        tree.heading(c, text=c)
        anchor = tk.W if c in ("Produit", "Utilité principale", "Notes") else tk.CENTER
        tree.column(c, width=col_widths.get(c, 120), anchor=anchor, minwidth=60)

    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.LEFT, fill=tk.Y)
    hsb.pack(fill=tk.X, padx=12, pady=(0, 4))

    for prod in selected_products:
        info = PRODUCT_INFO.get(prod)
        if info:
            tree.insert("", tk.END, values=(
                prod,
                info.get("utilite", ""),
                info.get("dose_min", ""),
                info.get("dose_max", ""),
                info.get("popularite", ""),
                info.get("dangerosite", ""),
                info.get("demi_vie", ""),
                info.get("notes", ""),
            ))
        else:
            tree.insert("", tk.END, values=(prod, "Information non disponible", "", "", "", "", "", ""))

    btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
    btn_row.pack(pady=8)
    _btn_safe(btn_row, "Fermer", dlg.destroy, "ACCENT", width=120, height=TH.BTN_SM).pack()


# ── helper : liste des produits sélectionnés (noms) ---------------------------
def _gather_selected_products(app):
    selected_products = []
    for cid, lb in getattr(app, "cycle_category_listboxes", {}).items():
        try:
            picks = [lb.get(i) for i in lb.curselection()]
            for p in picks:
                if p and p not in selected_products:
                    selected_products.append(p)
        except Exception:
            continue
    return selected_products


def _btn_show_selection(app):
    selected = _gather_selected_products(app)
    if not selected:
        messagebox.showinfo("ERAGROK", "Aucun produit sélectionné.")
        return
    _show_selected_products(app, selected)


# ── Persistance ---------------------------------------------------------------
def _refresh(app):
    if not hasattr(app, "cycle_tree"):
        return
    for r in app.cycle_tree.get_children():
        app.cycle_tree.delete(r)
    try:
        data_rows = _db.cycle_get_all(app)
        for row in reversed(data_rows[-10:]):
            app.cycle_tree.insert("", tk.END, values=(
                row.get("debut",""), row.get("fin_estimee",""),
                row.get("longueur_sem",""), row.get("produits_doses",""),
                row.get("note","")))
    except Exception:
        pass


def _save(app):
    if not getattr(app, "current_user", None):
        messagebox.showerror("ERAGROK", "Sélectionne un élève.")
        return
    try:
        start_date = app.cycle_start_var.get().strip() or "—"
        note = app.cycle_note_text.get("1.0", tk.END).strip()

        # Longueur
        try:
            length_val = app.cycle_length_var.get().strip()
        except Exception:
            try:
                length_val = app.cycle_length_entry.get().strip()
            except Exception:
                length_val = ""

        # Date de fin estimée
        try:
            fin_text = app.cycle_fin_label.cget("text")
        except Exception:
            fin_text = "—"

        # Produits sélectionnés + doses saisies
        produits_doses = []
        for prod, entry in getattr(app, "cycle_product_doses", {}).items():
            try:
                dose = entry.get().strip()
            except Exception:
                dose = ""
            if dose:
                produits_doses.append(f"{prod}: {dose}")
            else:
                produits_doses.append(prod)
        produits_field = " | ".join(produits_doses)

        _db.cycle_insert(app, start_date, fin_text, length_val, produits_field, note)

        # Reset
        try:
            app.cycle_note_text.delete("1.0", tk.END)
        except Exception:
            pass
        for lb in getattr(app, "cycle_category_listboxes", {}).values():
            try:
                lb.selection_clear(0, tk.END)
            except Exception:
                pass
        try:
            app.cycle_start_var.set("")
        except Exception:
            pass
        try:
            app.cycle_fin_label.configure(text="—")
        except Exception:
            pass
        try:
            app.cycle_length_var.set("12")
        except Exception:
            pass
        try:
            app.cycle_length_entry.pack_forget()
        except Exception:
            pass
        _rebuild_dose_fields(app)
        _refresh(app)
        messagebox.showinfo("ERAGROK", f"✔  Cycle du {start_date} sauvegardé.")
    except Exception as e:
        messagebox.showerror("ERAGROK", str(e))


# ── Helpers calendrier popup et calcul date fin ───────────────────────────────
def _pick_start_date(app):
    """Ouvre un popup calendrier. Le clic sur un jour valide et ferme."""
    popup = ctk.CTkToplevel(app.root)
    popup.title("Choisir la date de début")
    popup.resizable(False, False)
    popup.configure(fg_color=TH.BG_CARD)
    popup.grab_set()
    popup.focus_set()

    mk_label(popup, "Cliquez sur le jour de début du cycle", size="small",
             color=TH.TEXT_SUB).pack(padx=20, pady=(14, 6))
    mk_sep(popup).pack(fill=tk.X, padx=16, pady=(0, 10))

    _cal_style = dict(
        background=TH.BG_CARD2, foreground=TH.TEXT,
        selectbackground=TH.ACCENT, selectforeground=TH.TEXT,
        bordercolor=TH.BORDER,
        headersbackground=TH.BG_CARD, headersforeground=TH.TEXT_SUB,
        normalforeground=TH.TEXT, weekendforeground=TH.ACCENT_GLOW,
        font=("Inter", 10), headersfont=("Inter", 10, "bold"),
    )
    cal = Calendar(popup, selectmode="day", **_cal_style)
    cal.pack(padx=16, pady=(0, 8))

    def _on_day_selected(event=None):
        selected = cal.get_date()          # format MM/DD/YY (tkcalendar default)
        try:
            dt = datetime.strptime(selected, "%m/%d/%y")
            formatted = dt.strftime("%d/%m/%Y")
        except ValueError:
            formatted = selected
        try:
            app.cycle_start_var.set(formatted)
        except Exception:
            pass
        _update_fin_date(app)
        popup.destroy()

    cal.bind("<<CalendarSelected>>", _on_day_selected)
    _btn_safe(popup, "Valider", _on_day_selected, "SUCCESS", width=120,
              height=TH.BTN_SM).pack(pady=(0, 14))


def _update_fin_date(app):
    """Recalcule la date de fin à partir de la date de début + longueur en semaines."""
    try:
        start_str = app.cycle_start_var.get().strip()
        label = getattr(app, "cycle_fin_label", None)
        if not label:
            return
        if not start_str:
            label.configure(text="—")
            return
        try:
            start_dt = datetime.strptime(start_str, "%d/%m/%Y")
        except ValueError:
            label.configure(text="date invalide")
            return
        try:
            weeks = int(app.cycle_length_var.get().strip())
        except (ValueError, AttributeError):
            weeks = 12
        end_dt = start_dt + timedelta(weeks=weeks)
        label.configure(text=end_dt.strftime("%d/%m/%Y"))
    except Exception:
        pass


# ── Helpers calcul de dose ────────────────────────────────────────────────────

def _parse_dose_range(dose_str: str):
    """
    Extrait (lo, hi) depuis '250–500 mg/sem' ou '25 mcg/j'.
    Ignore les nombres qui suivent immédiatement 'x' (ex: 2x/sem).
    Retourne (None, None) si non parsable.
    """
    if not dose_str or dose_str.strip() in ("—", "", "-"):
        return (None, None)
    # Supprimer les occurrences Nx/sem (2x/sem, 3x/sem) avant extraction
    cleaned = re.sub(r'\d+[xX]/\S*', '', dose_str)
    nums = re.findall(r'\d+(?:[.,]\d+)?', cleaned.replace('–', '-').replace('—', '-'))
    vals = [float(n.replace(',', '.')) for n in nums]
    if not vals:
        return (None, None)
    return (vals[0], vals[-1])


def _dose_color(entered_str: str, dose_min_str: str, dose_max_str: str):
    """
    Retourne la couleur à appliquer sur la valeur saisie :
      vert   (#44cc44) — dans la fourchette recommandée (≤ hi_min)
      orange (#ff8800) — dépasse le conseillé mais reste sous le max
      rouge  (#cc3333) — dépasse le maximum absolu
      gris   (#888888) — non parsable / vide
    """
    try:
        val = float(re.findall(r'\d+(?:[.,]\d+)?', entered_str)[0].replace(',', '.'))
    except (IndexError, ValueError):
        return "#888888"
    _, hi_min = _parse_dose_range(dose_min_str)
    _, hi_max = _parse_dose_range(dose_max_str)
    if hi_min is not None and val <= hi_min:
        return "#44cc44"
    if hi_max is not None and val <= hi_max:
        return "#ff8800"
    return "#cc3333"


def _recommended_dose(dose_min_str: str) -> str:
    """Retourne la fourchette haute du min comme dose conseillée."""
    _, hi = _parse_dose_range(dose_min_str)
    if hi is None:
        return "—"
    unit = ""
    m = re.search(r'[a-zA-ZéàüùôîêûæœÉ/]+.*', dose_min_str)
    if m:
        unit = " " + m.group(0).strip()
    if hi == int(hi):
        return f"{int(hi)}{unit}"
    return f"{hi}{unit}"


def _calc_vials(dose_str: str, conc_str: str, vol_str: str, weeks: int) -> str:
    """Calcule le nombre de vials nécessaires pour le cycle."""
    try:
        dose  = float(re.findall(r'\d+(?:[.,]\d+)?', dose_str)[0].replace(',', '.'))
        conc  = float(re.findall(r'\d+(?:[.,]\d+)?', conc_str)[0].replace(',', '.'))
        vol   = float(re.findall(r'\d+(?:[.,]\d+)?', vol_str)[0].replace(',', '.'))
        if conc <= 0 or vol <= 0:
            return "—"
        mg_per_vial = conc * vol
        total_mg    = dose * weeks
        n_vials     = math.ceil(total_mg / mg_per_vial)
        return f"{n_vials} vial(s)  ({int(total_mg)} mg total  /  {int(mg_per_vial)} mg/vial)"
    except (IndexError, ValueError, ZeroDivisionError):
        return "—"


# ── Résumé/Recommandations dynamique ─────────────────────────────────────────

def _update_advice_summary(app):
    """Met à jour le bloc résumé avec recommandations, timing et alertes."""
    frame = getattr(app, "cycle_advice_frame", None)
    if frame is None:
        return
    # Guard : le frame peut avoir été détruit si l'utilisateur a navigué ailleurs
    try:
        if not frame.winfo_exists():
            app.cycle_advice_frame = None
            return
        for w in frame.winfo_children():
            w.destroy()
    except Exception:
        app.cycle_advice_frame = None
        return

    selected = _gather_selected_products(app)
    if not selected:
        ctk.CTkLabel(frame, text="(aucun produit sélectionné)",
                     font=TH.F_SMALL, text_color=TH.TEXT_MUTED).pack(
            anchor=tk.W, padx=16, pady=8)
        return

    try:
        n_weeks = int(app.cycle_length_var.get().strip())
    except Exception:
        n_weeks = 12

    # ── Alertes manquants ─────────────────────────────────────────────────────
    has_testo      = any(p in _AROMATIZING_TEST for p in selected)
    has_ai         = any(p in _AI_PRODUCTS for p in selected)
    has_hcg        = any(p in _HCG_PRODUCTS_SET for p in selected)
    has_tren_deca  = any("Trenbolone" in p or "Nandrolone" in p or "Deca" in p for p in selected)
    has_caber      = any("Cabergoline" in p for p in selected)
    has_oraux      = any(p in set(CATEGORY_ITEMS.get(2, [])) for p in selected)
    has_boldenone  = any("Boldenone" in p for p in selected)

    # Wash-out le plus long
    max_washout = max((_ESTER_WASHOUT.get(p, 0) for p in selected), default=2)
    if max_washout < 2:
        max_washout = 2

    alerts = []
    if has_testo and not has_ai:
        alerts.append(
            "⚠️  TESTO sans IA — ajoute Anastrozole 0.25 mg EOD ou Exemestane 12.5 mg EOD\n"
            "   → Sans IA : gynécomastie, rétention eau, hypertension"
        )
    if has_testo and not has_hcg:
        alerts.append(
            "⚠️  TESTO sans hCG — atrophie testiculaire progressive\n"
            "   → HCG 500 UI 2–3x/sem à partir de S3 (veille injection testo)"
        )
    if has_tren_deca and not has_caber:
        alerts.append(
            "⚠️  Tren/Deca sans Cabergoline — risque prolactine élevée\n"
            "   → Cabergoline 0.25 mg 2x/sem dès S1"
        )

    # Alertes bilan sanguin
    bilan_parts = []
    if has_oraux:
        bilan_parts.append("ALAT/ASAT S4 et S8 (hépatotoxicité oraux)")
    if has_boldenone:
        bilan_parts.append("Hématocrite S4 et S8 (polyglobulie Boldenone)")
    if has_tren_deca:
        bilan_parts.append("Prolactine S4 et S8 (Tren/Deca)")
    if has_testo or has_ai:
        bilan_parts.append("Lipides HDL/LDL S4 et S8")
    bilan_parts.append("Bilan hormonal complet 4 sem post-PCT (LH/FSH/Testo/Estradiol)")
    if bilan_parts:
        alerts.append(
            "🩸  BILANS SANGUINS RECOMMANDÉS :\n   → "
            + "\n   → ".join(bilan_parts)
        )

    # Wash-out ester
    max_w_prod = max(selected, key=lambda p: _ESTER_WASHOUT.get(p, 0), default=None)
    if max_w_prod and _ESTER_WASHOUT.get(max_w_prod, 0) > 0:
        alerts.append(
            f"⏳  Wash-out calculé : {max_washout} semaine(s) "
            f"(ester le plus long : {max_w_prod})"
        )

    if alerts:
        alert_frame = ctk.CTkFrame(frame, fg_color="#2a1010", corner_radius=8)
        alert_frame.pack(fill=tk.X, padx=14, pady=(4, 8))
        for a in alerts:
            ctk.CTkLabel(alert_frame, text=a, font=("Inter", 10, "bold"),
                         text_color="#ff6644", anchor="w",
                         wraplength=860, justify="left").pack(
                anchor=tk.W, padx=12, pady=4)

    # ── Fiche par produit ─────────────────────────────────────────────────────
    for prod in selected:
        info    = PRODUCT_INFO.get(prod, {})
        d_min   = info.get("dose_min",   "—")
        d_max   = info.get("dose_max",   "—")
        rec     = _recommended_dose(d_min)
        notes   = info.get("notes",      "")
        timing  = info.get("timing",     "")

        row = ctk.CTkFrame(frame, fg_color=TH.BG_CARD2, corner_radius=6)
        row.pack(fill=tk.X, padx=14, pady=3)

        ctk.CTkLabel(row, text=f"💊 {prod}", font=("Inter", 11, "bold"),
                     text_color=TH.ACCENT, anchor="w").pack(
            anchor=tk.W, padx=12, pady=(8, 2))

        ctk.CTkLabel(
            row,
            text=f"  Dose conseillée : {rec}  |  Plage : {d_min} → {d_max}",
            font=TH.F_SMALL, text_color="#aaddaa", anchor="w",
        ).pack(anchor=tk.W, padx=12, pady=1)

        if timing:
            ctk.CTkLabel(row, text=f"  🕐 Timing : {timing}",
                         font=("Inter", 10), text_color="#88aaff", anchor="w").pack(
                anchor=tk.W, padx=12, pady=1)

        # Dose saisie + total
        dose_entry = getattr(app, "cycle_product_doses", {}).get(prod)
        if dose_entry:
            try:
                dose_val = dose_entry.get().strip()
            except Exception:
                dose_val = ""
            if dose_val:
                color = _dose_color(dose_val, d_min, d_max)
                nums  = re.findall(r'\d+(?:[.,]\d+)?', dose_val)
                if nums:
                    dose_f = float(nums[0].replace(',', '.'))
                    total  = int(dose_f * n_weeks)
                    ctk.CTkLabel(
                        row,
                        text=f"  Dose saisie : {dose_val}/sem  →  {total} mg sur {n_weeks} semaines",
                        font=TH.F_SMALL, text_color=color, anchor="w",
                    ).pack(anchor=tk.W, padx=12, pady=1)

        if notes:
            ctk.CTkLabel(row, text=f"  ⚠  {notes}",
                         font=("Inter", 10), text_color="#cc9944",
                         anchor="w", wraplength=860).pack(
                anchor=tk.W, padx=12, pady=(2, 8))
        else:
            ctk.CTkFrame(row, fg_color="transparent", height=6).pack()


# ── Reconstruction dynamique des champs de dose ───────────────────────────────
def _rebuild_dose_fields(app):
    """
    Reconstruit le contenu de app.cycle_dose_frame avec des cartes riches
    par produit sélectionné : infos, dose colorée, calculateur de vials.
    Déclenche aussi la mise à jour du résumé.
    """
    frame = getattr(app, "cycle_dose_frame", None)
    if frame is None:
        return

    # Sauvegarder les valeurs actuelles
    old_doses = {}
    old_conc  = {}
    old_vol   = {}
    for prod, entry in getattr(app, "cycle_product_doses", {}).items():
        try:
            old_doses[prod] = entry.get().strip()
        except Exception:
            pass
    for prod, d in getattr(app, "_vial_conc_vars", {}).items():
        try:
            old_conc[prod] = d.get()
        except Exception:
            pass
    for prod, d in getattr(app, "_vial_vol_vars", {}).items():
        try:
            old_vol[prod] = d.get()
        except Exception:
            pass

    for w in frame.winfo_children():
        w.destroy()

    selected = _gather_selected_products(app)
    app.cycle_product_doses  = {}
    app._vial_conc_vars       = {}
    app._vial_vol_vars        = {}
    app._vial_updaters        = {}   # ← init avant la boucle

    # Défini ICI pour être accessible dans les closures de la boucle
    def _update_vial_result(prod):
        fn = app._vial_updaters.get(prod)
        if fn:
            fn()

    if not selected:
        ctk.CTkLabel(
            frame, text="← Sélectionnez des produits dans les listes ci-dessus",
            font=TH.F_SMALL, text_color=TH.TEXT_MUTED,
        ).pack(anchor=tk.W, padx=16, pady=12)
        _update_advice_summary(app)
        return

    try:
        n_weeks = int(app.cycle_length_var.get().strip())
    except Exception:
        n_weeks = 12

    for prod in selected:
        info      = PRODUCT_INFO.get(prod, {})
        dose_min  = info.get("dose_min",  "—")
        dose_max  = info.get("dose_max",  "—")
        utilite   = info.get("utilite",   "—")
        demi_vie  = info.get("demi_vie",  "—")
        danger    = info.get("dangerosite", "—")
        rec       = _recommended_dose(dose_min)

        # ── Carte produit ─────────────────────────────────────────────────────
        card = ctk.CTkFrame(frame, fg_color="#1a1f1a", corner_radius=10)
        card.pack(fill=tk.X, padx=12, pady=5)

        # Ligne 1 — Nom + métadonnées
        hdr = ctk.CTkFrame(card, fg_color="#222922", corner_radius=0)
        hdr.pack(fill=tk.X, padx=0, pady=(0, 0))

        ctk.CTkLabel(hdr, text=f"  💊  {prod}", font=("Inter", 12, "bold"),
                     text_color=TH.ACCENT, anchor="w").pack(
            side=tk.LEFT, padx=(8, 16), pady=6)
        ctk.CTkLabel(hdr, text=f"Utilité : {utilite}",
                     font=("Inter", 10), text_color="#999999",
                     anchor="w").pack(side=tk.LEFT, padx=(0, 16))
        ctk.CTkLabel(hdr, text=f"Demi-vie : {demi_vie}",
                     font=("Inter", 10), text_color="#777777").pack(
            side=tk.LEFT, padx=(0, 16))
        ctk.CTkLabel(hdr, text=f"Risque : {danger}",
                     font=("Inter", 10), text_color="#aa6633").pack(
            side=tk.LEFT)

        # Ligne 2 — Plages + conseillé
        info_row = ctk.CTkFrame(card, fg_color="transparent")
        info_row.pack(fill=tk.X, padx=12, pady=(6, 2))
        ctk.CTkLabel(info_row,
                     text=f"Plage min : {dose_min}    Plage max : {dose_max}",
                     font=("Inter", 10), text_color="#888888").pack(
            side=tk.LEFT, padx=(0, 24))
        ctk.CTkLabel(info_row,
                     text=f"✅ Dose conseillée : {rec}",
                     font=("Inter", 10, "bold"), text_color="#44cc88").pack(
            side=tk.LEFT)

        # Ligne 3 — Saisie dose + indicateur couleur
        dose_row = ctk.CTkFrame(card, fg_color="transparent")
        dose_row.pack(fill=tk.X, padx=12, pady=(4, 2))

        ctk.CTkLabel(dose_row, text="Dose utilisée :", font=TH.F_SMALL,
                     text_color=TH.TEXT_SUB, width=120).pack(side=tk.LEFT)

        dose_var = tk.StringVar(value=old_doses.get(prod, ""))
        dose_entry = ctk.CTkEntry(
            dose_row, textvariable=dose_var, width=110, height=32,
            placeholder_text="ex: 500",
            font=("Inter", 12),
        )
        dose_entry.pack(side=tk.LEFT, padx=(4, 4))

        ctk.CTkLabel(dose_row, text="/ semaine", font=("Inter", 10),
                     text_color="#666666").pack(side=tk.LEFT, padx=(0, 16))

        # Indicateur de couleur dynamique
        color_lbl = ctk.CTkLabel(dose_row, text="—", font=("Inter", 10, "bold"),
                                  text_color="#888888", width=300, anchor="w")
        color_lbl.pack(side=tk.LEFT)

        def _make_dose_trace(dv=dose_var, cl=color_lbl, dmn=dose_min, dmx=dose_max, p=prod):
            def _on_dose_change(*_):
                val = dv.get().strip()
                if not val:
                    cl.configure(text="—", text_color="#888888")
                    _update_advice_summary(app)
                    return
                color = _dose_color(val, dmn, dmx)
                _, hi_min = _parse_dose_range(dmn)
                _, hi_max = _parse_dose_range(dmx)
                try:
                    entered = float(re.findall(r'\d+(?:[.,]\d+)?', val)[0].replace(',', '.'))
                    if hi_min and entered <= hi_min:
                        msg = "✅ Dans la fourchette recommandée"
                    elif hi_max and entered <= hi_max:
                        msg = "⚠  Dépasse le conseillé — surveiller"
                    else:
                        msg = "🔴 Dépasse le maximum — risque élevé"
                except Exception:
                    msg = "—"
                cl.configure(text=msg, text_color=color)
                _update_advice_summary(app)
                _update_vial_result(p)
            return _on_dose_change

        dose_var.trace_add("write", _make_dose_trace())
        app.cycle_product_doses[prod] = dose_entry

        is_oral = prod in _ORAL_PRODUCTS

        # ── Calculateur de vials (injectables uniquement) ─────────────────────
        if not is_oral:
            vial_row = ctk.CTkFrame(card, fg_color="transparent")
            vial_row.pack(fill=tk.X, padx=12, pady=(4, 8))

            ctk.CTkLabel(vial_row, text="Calculateur vials :", font=("Inter", 10),
                         text_color="#666666", width=130).pack(side=tk.LEFT)

            ctk.CTkLabel(vial_row, text="Conc.", font=("Inter", 10),
                         text_color="#777777").pack(side=tk.LEFT)
            conc_var = tk.StringVar(value=old_conc.get(prod, ""))
            ctk.CTkEntry(vial_row, textvariable=conc_var, width=70, height=28,
                         placeholder_text="mg/ml",
                         font=("Inter", 10)).pack(side=tk.LEFT, padx=(4, 4))
            ctk.CTkLabel(vial_row, text="mg/ml", font=("Inter", 10),
                         text_color="#555555").pack(side=tk.LEFT, padx=(0, 12))

            ctk.CTkLabel(vial_row, text="Vol.", font=("Inter", 10),
                         text_color="#777777").pack(side=tk.LEFT)
            vol_var = tk.StringVar(value=old_vol.get(prod, ""))
            ctk.CTkEntry(vial_row, textvariable=vol_var, width=60, height=28,
                         placeholder_text="ml",
                         font=("Inter", 10)).pack(side=tk.LEFT, padx=(4, 4))
            ctk.CTkLabel(vial_row, text="ml/vial", font=("Inter", 10),
                         text_color="#555555").pack(side=tk.LEFT, padx=(0, 16))

            vial_result = ctk.CTkLabel(vial_row, text="", font=("Inter", 10, "bold"),
                                        text_color=TH.ACCENT, anchor="w", width=380)
            vial_result.pack(side=tk.LEFT)

            app._vial_conc_vars[prod] = conc_var
            app._vial_vol_vars[prod]  = vol_var

            def _make_vial_updater(p=prod, cv=conc_var, vv=vol_var, rl=vial_result,
                                    dv=dose_var):
                def _update(*_):
                    try:
                        wks = int(app.cycle_length_var.get().strip())
                    except Exception:
                        wks = 12
                    res = _calc_vials(dv.get(), cv.get(), vv.get(), wks)
                    rl.configure(text=f"→ {res}" if res != "—" else "")
                return _update

            updater = _make_vial_updater()
            conc_var.trace_add("write", updater)
            vol_var.trace_add("write",  updater)
            dose_var.trace_add("write", updater)
            app._vial_updaters[prod] = updater
            def _safe_vial(fn=_make_vial_updater()):
                try:
                    f = getattr(app, "cycle_advice_frame", None)
                    if f is None or not f.winfo_exists():
                        return
                    fn()
                except Exception:
                    pass
            app.root.after(50, _safe_vial)
        else:
            # Oraux : juste un petit badge
            ctk.CTkFrame(card, fg_color="transparent", height=2).pack()
            ctk.CTkLabel(card, text="  💊 Forme orale — pas de calcul de vials",
                         font=("Inter", 9), text_color="#555555",
                         anchor="w").pack(anchor=tk.W, padx=14, pady=(0, 8))
            # Stocker quand même les vars vides pour cohérence
            conc_var = tk.StringVar(value="")
            vol_var  = tk.StringVar(value="")
            app._vial_conc_vars[prod] = conc_var
            app._vial_vol_vars[prod]  = vol_var

    # Relancer le résumé
    # Relancer seulement si le frame est encore vivant
    def _safe_update():
        f = getattr(app, "cycle_advice_frame", None)
        try:
            if f and f.winfo_exists():
                _update_advice_summary(app)
        except Exception:
            pass
    app.root.after(60, _safe_update)


# ══════════════════════════════════════════════════════════════════════════════
#  GÉNÉRATEUR DE PLANNING DE CYCLE
# ══════════════════════════════════════════════════════════════════════════════

# ── Protocoles Clomid/Nolvadex ────────────────────────────────────────────────
_PCT_NORMAL = [
    (1, 2, "Clomid 50 mg/j",  "Nolvadex 20 mg/j"),
    (3, 4, "Clomid 25 mg/j",  "Nolvadex 20 mg/j"),
]
_PCT_AGRESSIF = [
    (1, 2, "Clomid 100 mg/j (→50 après J10)", "Nolvadex 40 mg/j"),
    (3, 4, "Clomid 50 mg/j",                  "Nolvadex 20 mg/j"),
    (5, 6, "Clomid 25 mg/j",                  "Nolvadex 10 mg/j"),
]


def _is_hcg(name: str) -> bool:
    return name.strip().upper() == "HCG"


def _build_cycle_plan(app, end_option: str, pct_mode: str) -> list[dict]:
    """
    Construit la liste de semaines du planning complet.

    Règles :
    - Produits "Base cycle" + injectables + oraux + peptides non-PCT → actifs dès S1
    - hCG → démarre S3 (2 semaines après le début du cycle)
    - Exemestane / Letrozole / Anastrozole / Cabergoline (IA/prolactine) → traités
      comme produits normaux (pendant le cycle, dose utilisateur)
    - Clomiphene (Clomid) + Tamoxifen (Nolvadex) → démarrent 14 jours (2 sem wash-out)
      après la dernière prise, avec le protocole Normal ou Agressif
    - Cruise / TRT → maintien 4 semaines, sans PCT strict
    """
    try:
        n_weeks = int(app.cycle_length_var.get().strip())
    except (ValueError, AttributeError):
        n_weeks = 12

    try:
        start_str = app.cycle_start_var.get().strip()
        start_dt  = datetime.strptime(start_str, "%d/%m/%Y") if start_str else None
    except ValueError:
        start_dt = None

    # Récupérer tous les produits sélectionnés + doses
    product_doses = getattr(app, "cycle_product_doses", {})

    main_products  = {}   # produits actifs pendant le cycle
    hcg_products   = {}   # hCG : démarre S3
    pct_strict     = {}   # Clomid / Nolvadex : après wash-out
    ia_products    = {}   # IA / anti-prolactine cat 6 : pendant le cycle

    for prod, entry in product_doses.items():
        try:
            dose = entry.get().strip()
        except Exception:
            dose = ""
        if prod in _PCT_STRICT:
            pct_strict[prod] = dose
        elif _is_hcg(prod):
            hcg_products[prod] = dose
        elif prod in set(CATEGORY_ITEMS.get(6, [])):   # cat6 = IA
            ia_products[prod] = dose
        else:
            main_products[prod] = dose

    # Fusionner IA dans main pour affichage pendant cycle
    all_cycle_products = {**main_products, **ia_products}

    # Wash-out dynamique selon l'ester le plus long sélectionné
    max_washout = 2   # défaut 2 semaines
    for prod in main_products:
        w = _ESTER_WASHOUT.get(prod, 0)
        if w > max_washout:
            max_washout = w

    def _date_str(week_offset: int) -> str:
        if start_dt is None:
            return ""
        return (start_dt + timedelta(weeks=week_offset)).strftime("%d/%m/%Y")

    def _fmt(d: dict) -> str:
        parts = [f"{n}: {v}" if v else n for n, v in d.items()]
        return "  |  ".join(parts)

    plan  = []
    abs_w = 0

    # ── Phase CYCLE ───────────────────────────────────────────────────────────
    for w in range(1, n_weeks + 1):
        abs_w += 1
        hcg_str = _fmt(hcg_products) if (w >= 3 and hcg_products) else (
            "⏳ démarrage S3" if (w < 3 and hcg_products) else ""
        )
        plan.append({
            "week_num":   abs_w,
            "label":      f"Semaine {w}",
            "date_start": _date_str(w - 1),
            "phase":      "CYCLE",
            "produits":   _fmt(all_cycle_products),
            "hcg":        hcg_str,
            "pct_info":   "",
        })

    # ── Phase post-cycle ──────────────────────────────────────────────────────
    if end_option == "PCT":
        washout_label = f"Wash-out ({max_washout} sem — ester sélectionné)"
        for w in range(1, max_washout + 1):
            abs_w += 1
            plan.append({
                "week_num":   abs_w,
                "label":      f"Wash-out S{w}",
                "date_start": _date_str(n_weeks + w - 1),
                "phase":      "WASHOUT",
                "produits":   "— Arrêt de tous les produits du cycle —",
                "hcg":        "",
                "pct_info":   f"Clomid + Nolvadex démarrent à J{max_washout * 7}",
            })

        # PCT strict : Clomid + Nolvadex selon protocole
        protocol        = _PCT_AGRESSIF if pct_mode == "Agressif" else _PCT_NORMAL
        pct_weeks_total = protocol[-1][1]

        # Construire la liste des produits PCT non-strict sélectionnés
        pct_strict_selected = list(pct_strict.keys())

        for pct_w in range(1, pct_weeks_total + 1):
            abs_w += 1
            clomid_lbl = nolva_lbl = ""
            for (s, e, cl, nv) in protocol:
                if s <= pct_w <= e:
                    clomid_lbl = cl
                    nolva_lbl  = nv
                    break

            # N'afficher que les molécules que l'utilisateur a cochées
            pct_lines = []
            if "Clomiphene (Clomid)" in pct_strict and clomid_lbl:
                pct_lines.append(clomid_lbl)
            if "Tamoxifen (Nolvadex)" in pct_strict and nolva_lbl:
                pct_lines.append(nolva_lbl)

            plan.append({
                "week_num":   abs_w,
                "label":      f"PCT S{pct_w}",
                "date_start": _date_str(n_weeks + 2 + pct_w - 1),
                "phase":      "PCT",
                "produits":   "",
                "hcg":        "",
                "pct_info":   "  +  ".join(pct_lines) if pct_lines else "— (aucun PCT sélectionné)",
            })

    elif end_option in ("Cruise", "TRT"):
        maintenance = getattr(app, "cycle_maintenance_dose_var", None)
        dose_txt = ""
        if maintenance:
            try:
                dose_txt = maintenance.get().strip()
            except Exception:
                pass
        if dose_txt:
            prod_label = f"Testostérone — {dose_txt} mg/sem (maintien {end_option})"
        else:
            prod_label = f"Protocole {end_option} — dose de maintien (à renseigner)"
        for w in range(1, 5):
            abs_w += 1
            plan.append({
                "week_num":   abs_w,
                "label":      f"{end_option} S{w}",
                "date_start": _date_str(n_weeks + w - 1),
                "phase":      end_option.upper(),
                "produits":   prod_label,
                "hcg":        "",
                "pct_info":   "",
            })

    return plan


def _show_cycle_generator(app):
    """Modal planning — lit app.cycle_end_var et app.cycle_pct_mode_var."""
    selected = _gather_selected_products(app)
    if not selected:
        messagebox.showinfo("ERAGROK", "Sélectionnez au moins un produit avant de générer le planning.")
        return

    dlg = ctk.CTkToplevel(app.root)
    dlg.title("\U0001f9ec  Générateur de planning de cycle")
    dlg.geometry("1260x780")
    dlg.configure(fg_color=TH.BG_CARD)
    dlg.grab_set()
    dlg.focus_set()

    mk_title(dlg, "  \U0001f9ec  PLANNING DE CYCLE — Semaine par semaine").pack(
        anchor=tk.W, padx=20, pady=(16, 4))
    mk_sep(dlg).pack(fill=tk.X, padx=20, pady=(0, 8))

    # ── Résumé détection ──────────────────────────────────────────────────────
    info_frame = ctk.CTkFrame(dlg, fg_color=TH.BG_CARD2, corner_radius=8)
    info_frame.pack(fill=tk.X, padx=20, pady=(0, 6))
    pct_selected = [p for p in selected if p in _PCT_STRICT]
    hcg_selected = [p for p in selected if _is_hcg(p)]
    pct_ia       = [p for p in selected if p in set(CATEGORY_ITEMS.get(6, []))]
    has_testo    = any(p in _AROMATIZING_TEST for p in selected)
    has_ai       = any(p in _AI_PRODUCTS for p in selected)
    info_parts = []
    if hcg_selected:
        info_parts.append("\U0001f489 hCG \u2192 démarrage S3, veille injection testo")
    if pct_selected:
        info_parts.append(f"\U0001f48a PCT strict J14 \u2192 {', '.join(pct_selected)}")
    if pct_ia:
        info_parts.append(f"\U0001f6e1\ufe0f IA cycle \u2192 {', '.join(pct_ia)}")
    if has_testo and not has_ai:
        info_parts.append("\u26a0\ufe0f TESTO SANS IA DÉTECTÉE — risque gynécomastie")
    ctk.CTkLabel(
        info_frame,
        text="  " + "   |   ".join(info_parts) if info_parts else "  Aucun hCG ni PCT sélectionné",
        font=TH.F_SMALL, text_color=TH.TEXT_SUB, anchor="w",
    ).pack(fill=tk.X, padx=12, pady=8)

    # ── Options — synchronisées avec écran principal ──────────────────────────
    opt_frame = ctk.CTkFrame(dlg, fg_color=TH.BG_CARD2, corner_radius=10)
    opt_frame.pack(fill=tk.X, padx=20, pady=(0, 8))
    ctk.CTkLabel(opt_frame, text="Fin de cycle :", font=TH.F_SMALL,
                 text_color=TH.TEXT_SUB).grid(row=0, column=0, padx=(16, 8), pady=10, sticky="w")
    end_var      = getattr(app, "cycle_end_var",      tk.StringVar(value="PCT"))
    pct_mode_var = getattr(app, "cycle_pct_mode_var", tk.StringVar(value="Normal"))
    for i, (opt, col) in enumerate([("PCT", TH.ACCENT), ("Cruise", "#40c0e0"), ("TRT", "#c080ff")]):
        ctk.CTkRadioButton(opt_frame, text=opt, variable=end_var, value=opt,
                           font=TH.F_SMALL, text_color=TH.TEXT,
                           fg_color=col, hover_color=TH.ACCENT_DIM,
                           ).grid(row=0, column=i+1, padx=10, pady=10, sticky="w")
    ctk.CTkLabel(opt_frame, text="Mode PCT :", font=TH.F_SMALL,
                 text_color=TH.TEXT_SUB).grid(row=0, column=4, padx=(24, 8), pady=10, sticky="w")
    for i, (mode, color) in enumerate([("Normal", TH.ACCENT), ("Agressif", TH.WARNING)]):
        ctk.CTkRadioButton(opt_frame, text=mode, variable=pct_mode_var, value=mode,
                           font=TH.F_SMALL, text_color=TH.TEXT,
                           fg_color=color, hover_color=TH.ACCENT_DIM,
                           ).grid(row=0, column=5+i, padx=10, pady=10, sticky="w")
    gen_btn = _btn_safe(opt_frame, "\u26a1  Générer", lambda: None,
                        "SUCCESS", width=160, height=TH.BTN_LG)
    gen_btn.grid(row=0, column=7, padx=(20, 16), pady=10)

    # ── Treeview ──────────────────────────────────────────────────────────────
    tree_frame = ctk.CTkFrame(dlg, fg_color="transparent")
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 4))
    cols  = ("Semaine", "Date début", "Phase", "Produits & IA", "hCG / Timing", "PCT / Protocole")
    col_w = {"Semaine": 88, "Date début": 98, "Phase": 78,
             "Produits & IA": 370, "hCG / Timing": 200, "PCT / Protocole": 270}
    apply_treeview_style("Generator")
    vsb = ttk.Scrollbar(tree_frame, orient="vertical")
    hsb = ttk.Scrollbar(dlg, orient="horizontal")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                        height=18, style="Generator.Treeview",
                        yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)
    for c in cols:
        tree.heading(c, text=c)
        anchor = tk.CENTER if c in ("Semaine", "Date début", "Phase") else tk.W
        tree.column(c, width=col_w.get(c, 120), anchor=anchor, minwidth=50)
    tree.tag_configure("CYCLE",   background="#182218", foreground=TH.TEXT)
    tree.tag_configure("HCG_OFF", background="#182218", foreground="#666666")
    tree.tag_configure("WASHOUT", background="#2a2010", foreground="#e0b040")
    tree.tag_configure("PCT",     background="#1a1a2e", foreground="#9999ff")
    tree.tag_configure("CRUISE",  background="#182030", foreground="#40c0e0")
    tree.tag_configure("TRT",     background="#201828", foreground="#c080ff")
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.pack(side=tk.LEFT, fill=tk.Y)
    hsb.pack(fill=tk.X, padx=20, pady=(0, 2))

    legend_lbl = ctk.CTkLabel(dlg, text="Cliquez sur \u26a1 Générer",
                               font=TH.F_SMALL, text_color=TH.TEXT_MUTED)
    legend_lbl.pack(pady=(0, 2))
    color_row = ctk.CTkFrame(dlg, fg_color="transparent")
    color_row.pack(pady=(0, 10))
    for lbl, col in [("\U0001f7e2 Cycle", "#4aaa4a"), ("\U0001f7e1 Wash-out", "#e0b040"),
                     ("\U0001f535 PCT", "#9999ff"), ("\U0001f6a7 Cruise", "#40c0e0"), ("\U0001f7e3 TRT", "#c080ff")]:
        ctk.CTkLabel(color_row, text=lbl, font=TH.F_SMALL, text_color=col).pack(side=tk.LEFT, padx=12)

    def _generate():
        plan = _build_cycle_plan(app, end_var.get(), pct_mode_var.get())
        for r in tree.get_children():
            tree.delete(r)
        for entry in plan:
            phase = entry["phase"]
            tag = "HCG_OFF" if (phase == "CYCLE" and "\u23f3" in entry.get("hcg", "")) else (
                phase if phase in ("CYCLE", "WASHOUT", "PCT", "CRUISE", "TRT") else "CYCLE")
            tree.insert("", tk.END, tags=(tag,), values=(
                entry["label"], entry["date_start"], phase,
                entry["produits"], entry["hcg"], entry["pct_info"],
            ))
        n_c = sum(1 for r in plan if r["phase"] == "CYCLE")
        n_w = sum(1 for r in plan if r["phase"] == "WASHOUT")
        n_p = sum(1 for r in plan if r["phase"] == "PCT")
        n_e = sum(1 for r in plan if r["phase"] in ("CRUISE", "TRT"))
        legend_lbl.configure(text=(
            f"\u2705 Cycle : {n_c} sem  |  \u23f3 Wash-out : {n_w} sem  |  "
            f"\U0001f48a PCT : {n_p} sem  |  \U0001f535 {end_var.get()} : {n_e} sem  |  "
            f"TOTAL : {n_c+n_w+n_p+n_e} semaines"
        ))

    gen_btn.configure(command=_generate)
    end_var.trace_add("write", lambda *_: _generate())
    pct_mode_var.trace_add("write", lambda *_: _generate())
    _generate()





def _export_cycle_pdf(app):
    """Génère un PDF du cycle avec planning, doses, recommandations et alertes."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
    except ImportError:
        messagebox.showerror("ERAGROK", "Module reportlab manquant.\nInstalle-le via : pip install reportlab")
        return

    selected = _gather_selected_products(app)
    if not selected:
        messagebox.showinfo("ERAGROK", "Aucun produit sélectionné.")
        return

    user     = getattr(app, "current_user", "utilisateur")
    try:    n_weeks = int(app.cycle_length_var.get().strip())
    except: n_weeks = 12
    end_mode = getattr(app, "cycle_end_var", None)
    pct_mode = getattr(app, "cycle_pct_mode_var", None)
    end_str  = end_mode.get() if end_mode else "PCT"
    pct_str  = pct_mode.get() if pct_mode else "Normal"
    sv       = getattr(app, "cycle_start_var", None)
    start_txt = sv.get() if sv else "—"

    out_dir  = os.path.join(utils.USERS_DIR, user)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    filename = os.path.join(out_dir, f"cycle_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf")

    doc    = SimpleDocTemplate(filename, pagesize=A4,
                               rightMargin=18*mm, leftMargin=18*mm,
                               topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    CACCENT = colors.HexColor("#4aaa4a")
    CWARN   = colors.HexColor("#cc8800")
    CDANGER = colors.HexColor("#cc3333")
    CWHITE  = colors.HexColor("#cccccc")
    CMUTED  = colors.HexColor("#888888")
    s_title  = ParagraphStyle("T", parent=styles["Title"],   fontSize=16, textColor=CACCENT, spaceAfter=4)
    s_h2     = ParagraphStyle("H", parent=styles["Heading2"], fontSize=11, textColor=CACCENT, spaceBefore=8, spaceAfter=3)
    s_body   = ParagraphStyle("B", parent=styles["Normal"],  fontSize=9,  textColor=CWHITE,  spaceAfter=3)
    s_warn   = ParagraphStyle("W", parent=styles["Normal"],  fontSize=9,  textColor=CWARN,   spaceAfter=3)
    s_danger = ParagraphStyle("D", parent=styles["Normal"],  fontSize=9,  textColor=CDANGER, spaceAfter=3)
    s_muted  = ParagraphStyle("M", parent=styles["Normal"],  fontSize=8,  textColor=CMUTED,  spaceAfter=2)

    story = []
    story.append(Paragraph("ERAGROK — Planning de Cycle Hormonal", s_title))
    story.append(Paragraph(
        f"Utilisateur : {user}  |  Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}  |  "
        f"Début : {start_txt}  |  Durée : {n_weeks} sem  |  Fin : {end_str} ({pct_str})", s_muted))
    story.append(HRFlowable(width="100%", thickness=1, color=CACCENT, spaceAfter=6))
    story.append(Paragraph(
        "Ce document est un outil de suivi personnel. Il ne constitue pas un avis médical.", s_warn))
    story.append(Spacer(1, 5))

    # Produits & doses
    story.append(Paragraph("Produits sélectionnés", s_h2))
    rows = [["Produit", "Dose/sem", "Plage min", "Plage max", "Conseillé", "Forme"]]
    for prod in selected:
        info  = PRODUCT_INFO.get(prod, {})
        d_min = info.get("dose_min", "—")
        d_max = info.get("dose_max", "—")
        rec   = _recommended_dose(d_min)
        entry = getattr(app, "cycle_product_doses", {}).get(prod)
        dose  = ""
        if entry:
            try: dose = entry.get().strip()
            except: pass
        forme = "Oral" if prod in _ORAL_PRODUCTS else "Injectable"
        rows.append([prod, dose or "—", d_min, d_max, rec, forme])
    tbl = Table(rows, colWidths=[56*mm, 22*mm, 30*mm, 30*mm, 22*mm, 22*mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0),  colors.HexColor("#1a3a1a")),
        ("TEXTCOLOR",      (0,0),(-1,0),  CACCENT),
        ("FONTSIZE",       (0,0),(-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [colors.HexColor("#111811"), colors.HexColor("#151f15")]),
        ("TEXTCOLOR",      (0,1),(-1,-1), CWHITE),
        ("GRID",           (0,0),(-1,-1), 0.3, colors.HexColor("#2a4a2a")),
        ("PADDING",        (0,0),(-1,-1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6))

    # Alertes
    alerts = []
    has_testo = any(p in _AROMATIZING_TEST for p in selected)
    if has_testo and not any(p in _AI_PRODUCTS for p in selected):
        alerts.append("Testostérone sans IA — risque gynécomastie/hypertension")
    if has_testo and not any(p in _HCG_PRODUCTS_SET for p in selected):
        alerts.append("Testostérone sans hCG — risque atrophie testiculaire")
    if any("Trenbolone" in p or "Nandrolone" in p for p in selected) and not any("Cabergoline" in p for p in selected):
        alerts.append("Tren/Deca sans Cabergoline — risque prolactine élevée")
    if alerts:
        story.append(Paragraph("Alertes", s_h2))
        for a in alerts:
            story.append(Paragraph(f"ATTENTION : {a}", s_danger))
        story.append(Spacer(1,4))

    # Planning
    plan = _build_cycle_plan(app, end_str, pct_str)
    if plan:
        story.append(Paragraph("Planning semaine par semaine", s_h2))
        pr = [["Semaine", "Date", "Phase", "Produits & IA", "hCG", "PCT"]]
        for e in plan:
            pr.append([e["label"], e["date_start"], e["phase"],
                        (e["produits"][:55]+"…" if len(e["produits"])>55 else e["produits"]),
                        (e["hcg"][:28]+"…" if len(e["hcg"])>28 else e["hcg"]),
                        (e["pct_info"][:38]+"…" if len(e["pct_info"])>38 else e["pct_info"])])
        phcol = {"CYCLE": "#182218","WASHOUT": "#2a2010","PCT": "#1a1a2e","CRUISE": "#182030","TRT": "#201828"}
        pts = [("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1a3a1a")),
               ("TEXTCOLOR",(0,0),(-1,0),CACCENT),("FONTSIZE",(0,0),(-1,-1),7),
               ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#2a4a2a")),
               ("PADDING",(0,0),(-1,-1),3),("TEXTCOLOR",(0,1),(-1,-1),CWHITE)]
        for i,e in enumerate(plan,1):
            pts.append(("BACKGROUND",(0,i),(-1,i),colors.HexColor(phcol.get(e["phase"],"#111811"))))
        p_tbl = Table(pr, colWidths=[22*mm,22*mm,18*mm,60*mm,30*mm,30*mm])
        p_tbl.setStyle(TableStyle(pts))
        story.append(p_tbl)
        story.append(Spacer(1,6))

    # Notes produit
    story.append(Paragraph("Notes par produit", s_h2))
    for prod in selected:
        info   = PRODUCT_INFO.get(prod, {})
        notes  = info.get("notes","")
        timing = info.get("timing","")
        if notes or timing:
            story.append(Paragraph(f"<b>{prod}</b>", s_body))
            if timing: story.append(Paragraph(f"  Timing : {timing}", s_muted))
            if notes:  story.append(Paragraph(f"  {notes}", s_warn))

    nw = getattr(app, "cycle_note_text", None)
    if nw:
        try:
            un = nw.get("1.0", tk.END).strip()
            if un:
                story.append(Paragraph("Notes personnelles", s_h2))
                story.append(Paragraph(un, s_body))
        except: pass

    story.append(Spacer(1,8))
    story.append(Paragraph(
        "Consultez un endocrinologue ou médecin du sport avant tout protocole hormonal.", s_muted))
    try:
        doc.build(story)
        messagebox.showinfo("ERAGROK", f"PDF exporté :\n{filename}")
    except Exception as e:
        messagebox.showerror("ERAGROK", f"Erreur export PDF :\n{e}")




def _load_cycle_into_ui(app, cycle_dict):
    """
    Charge un enregistrement de cycle (dict SQLite) dans tous les widgets UI.
    Sélectionne les produits dans les listboxes et remet les doses.
    """
    if not cycle_dict:
        return

    debut        = cycle_dict.get("debut", "")
    longueur_sem = str(cycle_dict.get("longueur_sem", "12")).strip()
    fin_estimee  = cycle_dict.get("fin_estimee", "—")
    produits_s   = cycle_dict.get("produits_doses", "")
    note_s       = cycle_dict.get("note", "")

    # ── Longueur ────────────────────────────────────────────────────────
    try:
        app.cycle_length_var.set(longueur_sem)
    except Exception:
        try:
            app.cycle_length_entry.delete(0, tk.END)
            app.cycle_length_entry.insert(0, longueur_sem)
        except Exception:
            pass
    if longueur_sem == "12":
        try: app.cycle_preset_var.set("12 semaines")
        except Exception: pass
    elif longueur_sem == "16":
        try: app.cycle_preset_var.set("16 semaines")
        except Exception: pass
    else:
        try: app.cycle_preset_var.set("Personnalisé")
        except Exception: pass

    # ── Date de début ────────────────────────────────────────────────────
    try:
        app.cycle_start_var.set(debut)
    except Exception:
        pass
    try:
        app.cycle_fin_label.configure(text=fin_estimee)
    except Exception:
        pass

    # ── Note ────────────────────────────────────────────────────────────
    try:
        app.cycle_note_text.delete("1.0", tk.END)
        if note_s:
            app.cycle_note_text.insert("1.0", note_s)
    except Exception:
        pass

    # ── Produits & doses ────────────────────────────────────────────────
    if not produits_s:
        return

    entries = [e.strip() for e in produits_s.split("|") if e.strip()]
    # Construire un dict {nom_produit: dose}
    prod_doses = {}
    for entry in entries:
        parts = entry.split(":", 1)
        name  = parts[0].strip()
        dose  = parts[1].strip() if len(parts) > 1 else ""
        prod_doses[name] = dose

    # Effacer toutes les sélections listbox
    for cid, lb in getattr(app, "cycle_category_listboxes", {}).items():
        try:
            lb.selection_clear(0, tk.END)
        except Exception:
            pass

    # Sélectionner chaque produit dans sa listbox
    for cid, lb in getattr(app, "cycle_category_listboxes", {}).items():
        items = CATEGORY_ITEMS.get(cid, [])
        for i, item in enumerate(items):
            if item in prod_doses:
                try:
                    lb.selection_set(i)
                except Exception:
                    pass

    # Reconstruire les champs de dose (synchrone)
    _rebuild_dose_fields(app)

    # Remplir les doses après que les widgets soient créés
    def _fill_doses():
        dose_map = getattr(app, "cycle_product_doses", {})
        for prod_name, dose in prod_doses.items():
            entry = dose_map.get(prod_name)
            if entry:
                try:
                    entry.delete(0, tk.END)
                    entry.insert(0, dose)
                except Exception:
                    pass
        _update_advice_summary(app)

    try:
        app.root.after(80, _fill_doses)
    except Exception:
        _fill_doses()


def _delete_selected_cycle(app):
    """Supprime le cycle sélectionné dans l'historique."""
    sel = app.cycle_tree.selection()
    if not sel:
        messagebox.showinfo("ERAGROK", "Sélectionne un cycle dans l'historique.")
        return
    vals = app.cycle_tree.item(sel[0], "values")
    debut = vals[0] if vals else ""
    if not messagebox.askyesno("Confirmer", f"Supprimer le cycle du {debut} ?\nIrréversible."):
        return
    try:
        from data.db import get_user_db_from_app
        con = get_user_db_from_app(app)
        con.execute("DELETE FROM cycle WHERE debut=?", (debut,))
        con.commit(); con.close()
        _refresh(app)
        messagebox.showinfo("ERAGROK", "✔ Cycle supprimé.")
    except Exception as e:
        messagebox.showerror("ERAGROK", str(e))


def _load_selected_cycle(app):
    """Charge le cycle sélectionné dans l'historique vers les champs UI."""
    sel = app.cycle_tree.selection()
    if not sel:
        messagebox.showinfo("ERAGROK", "Sélectionne un cycle dans l'historique.")
        return
    vals = app.cycle_tree.item(sel[0], "values")
    cycle_dict = {
        "debut":          vals[0] if len(vals) > 0 else "",
        "fin_estimee":    vals[1] if len(vals) > 1 else "",
        "longueur_sem":   vals[2] if len(vals) > 2 else "12",
        "produits_doses": vals[3] if len(vals) > 3 else "",
        "note":           vals[4] if len(vals) > 4 else "",
    }
    _load_cycle_into_ui(app, cycle_dict)
    messagebox.showinfo("ERAGROK", f"✔ Cycle du {cycle_dict['debut']} chargé.")

def show_cycle_screen(app):
    for w in app.content.winfo_children():
        w.destroy()

    screen_header(
        app.content, "💉  CYCLE HORMONAL",
        user_name=getattr(app, "selected_user_name", ""),
        back_cmd=app.show_dashboard,
    )

    scroll = mk_scrollframe(app.content)
    scroll.pack(fill=tk.BOTH, expand=True)

    PAD = dict(fill="x", padx=28)

    # ── BLOC 1 : Catégories et éléments ───────────────────────────────────────
    cat_card = mk_card(scroll)
    cat_card.pack(**PAD, pady=(20, 10))

    cat_hdr = ctk.CTkFrame(cat_card, fg_color="transparent")
    cat_hdr.pack(fill=tk.X, padx=16, pady=(14, 6))
    mk_title(cat_hdr, "  🧪  CATÉGORIES ET ÉLÉMENTS  (sélection multiple possible)").pack(side=tk.LEFT)
    mk_sep(cat_card).pack(fill=tk.X, padx=16, pady=(0, 10))

    app.cycle_category_listboxes = {}

    for cid, cname in CATEGORIES.items():
        row = ctk.CTkFrame(cat_card, fg_color="transparent")
        row.pack(fill=tk.X, padx=16, pady=6)

        mk_label(row, cname, size="small", color=TH.TEXT_SUB, width=200).pack(
            side=tk.LEFT, anchor="n", pady=2
        )

        lb_frame = tk.Frame(row, bg=TH.BG_CARD2)
        lb_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))

        scrollbar = tk.Scrollbar(lb_frame, orient=tk.VERTICAL)
        lb = tk.Listbox(
            lb_frame,
            selectmode=tk.MULTIPLE,
            exportselection=False,
            height=4,
            yscrollcommand=scrollbar.set,
            bg=TH.BG_CARD2,
            fg=TH.TEXT,
            selectbackground=TH.ACCENT_DIM,
            selectforeground=TH.ACCENT_GLOW,
            relief="flat",
            bd=0,
            font=("Inter", 10),
            activestyle="none",
        )
        scrollbar.config(command=lb.yview)
        lb.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        for it in CATEGORY_ITEMS.get(cid, []):
            lb.insert(tk.END, it)

        sel_label = mk_label(row, "0 sélectionné(s)", size="small", color=TH.TEXT_MUTED, width=120)
        sel_label.pack(side=tk.LEFT, anchor="n", padx=(8, 0), pady=2)

        def _on_select(event, lb=lb, lbl=sel_label):
            lbl.configure(text=f"{len(lb.curselection())} sélectionné(s)")
            _rebuild_dose_fields(app)

        lb.bind("<<ListboxSelect>>", _on_select)
        app.cycle_category_listboxes[cid] = lb

    ctk.CTkFrame(cat_card, fg_color="transparent", height=8).pack()

    # ── BLOC 2 : Doses dynamiques par produit ─────────────────────────────────
    dose_card = mk_card(scroll)
    dose_card.pack(**PAD)
    mk_title(dose_card, "  💉  DOSES PAR PRODUIT").pack(anchor=tk.W, padx=16, pady=(14, 6))
    mk_sep(dose_card).pack(fill=tk.X, padx=16, pady=(0, 6))

    # En-tête des colonnes
    hdr = ctk.CTkFrame(dose_card, fg_color="transparent")
    hdr.pack(fill=tk.X, padx=12, pady=(0, 2))
    ctk.CTkLabel(hdr, text="Produit", font=TH.F_SMALL, text_color=TH.TEXT_MUTED,
                 anchor="w", width=260).pack(side=tk.LEFT, padx=(12, 8))
    ctk.CTkLabel(hdr, text="Plage de doses (référence)", font=TH.F_SMALL,
                 text_color=TH.TEXT_MUTED, anchor="w", width=260).pack(side=tk.LEFT, padx=(0, 12))
    ctk.CTkLabel(hdr, text="Dose utilisée", font=TH.F_SMALL,
                 text_color=TH.TEXT_MUTED, anchor="w", width=160).pack(side=tk.LEFT)

    # Zone dynamique — contenu reconstruit à chaque sélection
    app.cycle_dose_frame = ctk.CTkFrame(dose_card, fg_color="transparent")
    app.cycle_dose_frame.pack(fill=tk.X, pady=(0, 8))
    app.cycle_product_doses = {}
    _rebuild_dose_fields(app)   # état initial (vide)

    # ── BLOC 3 : Données du cycle (début + longueur) ──────────────────────────
    data_card = mk_card(scroll)
    data_card.pack(**PAD)
    mk_title(data_card, "  💊  DONNÉES DU CYCLE").pack(anchor=tk.W, padx=16, pady=(14, 6))
    mk_sep(data_card).pack(fill=tk.X, padx=16, pady=(0, 12))

    # Longueur / preset
    preset_frame = ctk.CTkFrame(data_card, fg_color="transparent")
    preset_frame.pack(fill=tk.X, padx=16, pady=(0, 4))
    mk_label(preset_frame, "Type de cycle", size="small", color=TH.TEXT_SUB, width=180).pack(side=tk.LEFT)
    app.cycle_preset_var = tk.StringVar(value="12 semaines")
    presets = ["12 semaines", "16 semaines", "Personnalisé", "Premier Cycle"]
    try:
        preset_menu = ctk.CTkOptionMenu(
            preset_frame, values=presets, variable=app.cycle_preset_var,
            command=lambda v: (_apply_cycle_preset(app, v), _update_fin_date(app)),
        )
    except Exception:
        preset_menu = tk.OptionMenu(
            preset_frame, app.cycle_preset_var, *presets,
            command=lambda v: (_apply_cycle_preset(app, v), _update_fin_date(app)),
        )
    preset_menu.pack(side=tk.LEFT, padx=8)
    mk_label(preset_frame, "Longueur (sem)", size="small", color=TH.TEXT_MUTED).pack(side=tk.LEFT, padx=(16, 6))
    app.cycle_length_var = tk.StringVar(value="12")
    length_entry = mk_entry(preset_frame, width=80, placeholder="sem")
    try:
        length_entry.configure(textvariable=app.cycle_length_var)
    except Exception:
        length_entry.insert(0, app.cycle_length_var.get())
    app.cycle_length_entry = length_entry
    app.cycle_length_var.trace_add("write", lambda *_: (
        _update_fin_date(app),
        [fn() for fn in getattr(app, "_vial_updaters", {}).values()],
    ))

    # ── Fin de cycle : PCT / Cruise / TRT ─────────────────────────────────────
    mk_sep(data_card).pack(fill=tk.X, padx=16, pady=(10, 0))
    end_frame = ctk.CTkFrame(data_card, fg_color="transparent")
    end_frame.pack(fill=tk.X, padx=16, pady=(10, 4))
    mk_label(end_frame, "Fin de cycle", size="small", color=TH.TEXT_SUB, width=180).pack(side=tk.LEFT)
    app.cycle_end_var = tk.StringVar(value="PCT")
    for opt, color in [("PCT", TH.ACCENT), ("Cruise", "#40c0e0"), ("TRT", "#c080ff")]:
        ctk.CTkRadioButton(
            end_frame, text=opt, variable=app.cycle_end_var, value=opt,
            font=TH.F_SMALL, text_color=TH.TEXT,
            fg_color=color, hover_color=TH.ACCENT_DIM,
        ).pack(side=tk.LEFT, padx=(0, 16))

    # ── Mode PCT : Normal / Agressif ──────────────────────────────────────────
    pct_frame = ctk.CTkFrame(data_card, fg_color="transparent")
    pct_frame.pack(fill=tk.X, padx=16, pady=(4, 4))
    mk_label(pct_frame, "Mode PCT", size="small", color=TH.TEXT_SUB, width=180).pack(side=tk.LEFT)
    app.cycle_pct_mode_var = tk.StringVar(value="Normal")
    for mode, col in [("Normal", TH.ACCENT), ("Agressif", TH.WARNING)]:
        ctk.CTkRadioButton(
            pct_frame, text=mode, variable=app.cycle_pct_mode_var, value=mode,
            font=TH.F_SMALL, text_color=TH.TEXT,
            fg_color=col, hover_color=TH.ACCENT_DIM,
        ).pack(side=tk.LEFT, padx=(0, 16))

    # ── Dose de maintien TRT / Cruise (dynamique) ─────────────────────────────
    app.cycle_maintenance_dose_var = tk.StringVar(value="")
    maintenance_frame = ctk.CTkFrame(data_card, fg_color="transparent")
    maintenance_frame.pack(fill=tk.X, padx=16, pady=(2, 6))

    def _update_maintenance_visibility(*_):
        for w in maintenance_frame.winfo_children():
            w.destroy()
        mode = app.cycle_end_var.get()
        if mode in ("TRT", "Cruise"):
            color = "#c080ff" if mode == "TRT" else "#40c0e0"
            mk_label(maintenance_frame, f"Dose {mode} (maintien)",
                     size="small", color=TH.TEXT_SUB, width=180).pack(side=tk.LEFT)
            e = mk_entry(maintenance_frame, width=110, placeholder="ex: 125")
            try:
                e.configure(textvariable=app.cycle_maintenance_dose_var)
            except Exception:
                pass
            e.pack(side=tk.LEFT, padx=(8, 6))
            ctk.CTkLabel(maintenance_frame, text="mg/sem",
                         font=("Inter", 10), text_color="#666666").pack(side=tk.LEFT)
            if mode == "TRT":
                ctk.CTkLabel(maintenance_frame,
                             text="  (typiquement 100–200 mg/sem Testo E ou C)",
                             font=("Inter", 10), text_color=color).pack(side=tk.LEFT, padx=(10, 0))
            else:
                ctk.CTkLabel(maintenance_frame,
                             text="  (typiquement 200–300 mg/sem — dose réduite du cycle)",
                             font=("Inter", 10), text_color=color).pack(side=tk.LEFT, padx=(10, 0))

    app.cycle_end_var.trace_add("write", _update_maintenance_visibility)
    _update_maintenance_visibility()

    # Début de cycle
    mk_sep(data_card).pack(fill=tk.X, padx=16, pady=(10, 0))
    start_frame = ctk.CTkFrame(data_card, fg_color="transparent")
    start_frame.pack(fill=tk.X, padx=16, pady=8)
    mk_label(start_frame, "Début de cycle", size="small", color=TH.TEXT_SUB, width=180).pack(side=tk.LEFT)
    app.cycle_start_var = tk.StringVar(value="")
    start_entry = mk_entry(start_frame, width=130, placeholder="JJ/MM/AAAA")
    try:
        start_entry.configure(textvariable=app.cycle_start_var, state="readonly", cursor="hand2")
    except Exception:
        pass
    start_entry.pack(side=tk.LEFT, padx=(8, 6))
    start_entry.bind("<Button-1>", lambda e: _pick_start_date(app))
    _btn_safe(start_frame, "📅", lambda: _pick_start_date(app), "ACCENT", width=40, height=32).pack(side=tk.LEFT, padx=(0, 24))
    mk_label(start_frame, "Fin estimée :", size="small", color=TH.TEXT_MUTED).pack(side=tk.LEFT, padx=(0, 8))
    app.cycle_fin_label = ctk.CTkLabel(start_frame, text="—", font=TH.F_SMALL, text_color=TH.ACCENT)
    app.cycle_fin_label.pack(side=tk.LEFT)

    ctk.CTkFrame(data_card, fg_color="transparent", height=8).pack()

    # ── BLOC 4 : Notes / observations ─────────────────────────────────────────
    note_card = mk_card(scroll)
    note_card.pack(**PAD)
    mk_title(note_card, "  📝  NOTES / OBSERVATIONS").pack(anchor=tk.W, padx=16, pady=(14, 6))
    mk_sep(note_card).pack(fill=tk.X, padx=16, pady=(0, 10))
    app.cycle_note_text = mk_textbox(note_card, height=100)
    app.cycle_note_text.pack(fill=tk.X, padx=16, pady=(0, 14))

    # ── BLOC 4b : Résumé & Recommandations (dynamique) ────────────────────────
    advice_card = mk_card(scroll)
    advice_card.pack(**PAD)
    mk_title(advice_card, "  📋  RÉSUMÉ & RECOMMANDATIONS").pack(anchor=tk.W, padx=16, pady=(14, 6))
    mk_sep(advice_card).pack(fill=tk.X, padx=16, pady=(0, 6))
    app.cycle_advice_frame = ctk.CTkFrame(advice_card, fg_color="transparent")
    app.cycle_advice_frame.pack(fill=tk.X, pady=(0, 10))
    _update_advice_summary(app)

    # ── BLOC 5 : Boutons ──────────────────────────────────────────────────────
    btn_row = ctk.CTkFrame(scroll, fg_color="transparent")
    btn_row.pack(fill=tk.X, padx=28, pady=(0, 10))
    _btn_safe(btn_row, "🧬  Générer le planning",  lambda: _show_cycle_generator(app), "WARNING", width=200, height=TH.BTN_LG).pack(side=tk.LEFT, padx=(0, 10))
    _btn_safe(btn_row, "📄  Exporter PDF",          lambda: _export_cycle_pdf(app),    "ACCENT",  width=170, height=TH.BTN_LG).pack(side=tk.LEFT, padx=(0, 10))
    _btn_safe(btn_row, "💾  SAUVEGARDER",           lambda: _save(app),                "SUCCESS", width=180, height=TH.BTN_LG).pack(side=tk.LEFT)

    # ── BLOC 6 : Historique ────────────────────────────────────────────────────
    hist_card = mk_card(scroll)
    hist_card.pack(fill=tk.X, padx=28, pady=(10, 28))
    mk_title(hist_card, "  📋  HISTORIQUE DES PRISES").pack(anchor=tk.W, padx=16, pady=(14, 6))
    mk_sep(hist_card).pack(fill=tk.X, padx=16, pady=(0, 8))

    apply_treeview_style("Cycle")
    cols_t = ("Début", "Fin estimée", "Longueur (sem)", "Produits & doses", "Note")
    app.cycle_tree = ttk.Treeview(
        hist_card, columns=cols_t, show="headings",
        height=8, selectmode="browse", style="Cycle.Treeview",
    )
    col_w = {"Début": 110, "Fin estimée": 110, "Longueur (sem)": 110, "Produits & doses": 500, "Note": 220}
    for c in cols_t:
        app.cycle_tree.heading(c, text=c)
        anchor = tk.W if c in ("Produits & doses", "Note") else tk.CENTER
        app.cycle_tree.column(c, width=col_w.get(c, 120), anchor=anchor)

    vsb = ttk.Scrollbar(hist_card, orient="vertical", command=app.cycle_tree.yview)
    hsb = ttk.Scrollbar(hist_card, orient="horizontal", command=app.cycle_tree.xview)
    app.cycle_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree_wrap = ctk.CTkFrame(hist_card, fg_color="transparent")
    tree_wrap.pack(fill=tk.X, padx=16, pady=(0, 4))
    app.cycle_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, in_=tree_wrap)
    vsb.pack(side=tk.RIGHT, fill=tk.Y, in_=tree_wrap)
    hsb.pack(fill=tk.X, padx=16, pady=(0, 16))

    # ── Boutons historique ────────────────────────────────────────────────────
    hist_btn_row = ctk.CTkFrame(hist_card, fg_color="transparent")
    hist_btn_row.pack(fill=tk.X, padx=16, pady=(4, 16))
    _btn_safe(hist_btn_row, "📂  Charger ce cycle",
              lambda: _load_selected_cycle(app),
              "ACCENT", width=200, height=TH.BTN_MD).pack(side=tk.LEFT, padx=(0, 10))
    _btn_safe(hist_btn_row, "🗑  Supprimer ce cycle",
              lambda: _delete_selected_cycle(app),
              "DANGER", width=200, height=TH.BTN_MD).pack(side=tk.LEFT)
    mk_label(hist_btn_row,
             "  Sélectionne une ligne dans l'historique puis clique",
             size="small", color=TH.TEXT_MUTED).pack(side=tk.LEFT, padx=16)

    # ── init : appliquer preset + charger dernier cycle ────────────────────────
    _apply_cycle_preset(app, app.cycle_preset_var.get())
    _refresh(app)

    # Auto-charger le dernier cycle sauvegardé
    def _auto_load():
        try:
            last = _db.cycle_get_last(app)
            if last:
                _load_cycle_into_ui(app, last)
        except Exception:
            pass
    try:
        app.root.after(150, _auto_load)
    except Exception:
        pass