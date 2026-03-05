# cycle_module.py — version finale avec presets de cycle (12, 16, Personnalisé)
import os
import csv
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from tkcalendar import Calendar
from data import utils
from data.theme import (
    TH, mk_btn, mk_card, mk_card2, mk_entry,
    mk_textbox, mk_label, mk_title, mk_sep,
    mk_scrollframe, screen_header, apply_treeview_style,
)

# --- Catégories et items (version corrigée) ----------------------------------
CATEGORIES = {
    1: "Anabolisants injectables",
    2: "Anabolisants oraux",
    3: "Peptides",
    4: "Hormones",
    5: "Post Cycle Therapy (PCT)",
}

CATEGORY_ITEMS = {
    1: [
        "Boldenone Undecylenate (Equipoise)",
        "Drostanolone Enanthate (Masteron E)",
        "Drostanolone Propionate (Masteron P)",
        "Methenolone Enanthate (Primobolan)",
        "Nandrolone Decanoate (Deca)",
        "Nandrolone Phenylpropionate (NPP)",
        "Trenbolone Hexahydrobenzylcarbonate",
        "Sustanon 250/300/350",
        "Testosterone Enanthate",
        "Testosterone Cypionate",
        "Testosterone Propionate",
        "Trenbolone Acetate",
        "Trenbolone Enanthate",
        "Stanozolol Injection (Winstrol depot)",
        "Testosterone Undecanoate (Nebido)",
        "Cut Stack (mix Tren/Mast/Test)",
    ],
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
        "HCG",
        "Tirzepatide",
        "Semaglutide",
    ],
    4: [
        "HGH Somatropin",
        "Testosterone Enanthate",
        "Testosterone Cypionate",
        "Testosterone Propionate",
        "Testosterone Undecanoate",
        "hCG",
        "Insulin (listed for completeness only)",
        "IGF-1 LR3",
    ],
    5: [
        "Exemestane (Aromasin)",
        "Letrozole (Femara)",
        "Clomiphene (Clomid)",
        "Tamoxifen (Nolvadex)",
        "Anastrozole (Arimidex)",
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
        "utilite": "Inhibiteur aromatase irréversible",
        "dose_min": "12.5 mg/j ou EOD",
        "dose_max": "25 mg/j",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "Impact modéré sur lipides",
    },
    "Letrozole (Femara)": {
        "utilite": "Inhibiteur aromatase puissant",
        "dose_min": "0.25–0.5 mg EOD",
        "dose_max": "2.5 mg/j",
        "popularite": "★★★☆☆",
        "dangerosite": "★★★☆☆",
        "demi_vie": "—",
        "notes": "Crash œstro possible",
    },
    "Clomiphene (Clomid)": {
        "utilite": "Relance axe HPTA",
        "dose_min": "50 mg/j",
        "dose_max": "100–200 mg/j",
        "popularite": "★★★★★",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "Vision floue possible",
    },
    "Tamoxifen (Nolvadex)": {
        "utilite": "Relance + bloc périphérique œstrogène",
        "dose_min": "20 mg/j",
        "dose_max": "40 mg/j",
        "popularite": "★★★★★",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "Très utilisé en PCT",
    },
    "Anastrozole (Arimidex)": {
        "utilite": "Inhibiteur aromatase réversible",
        "dose_min": "0.5 mg EOD",
        "dose_max": "1 mg/j",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "Impact sur lipides",
    },
    "Cabergoline (Dostinex)": {
        "utilite": "Contrôle prolactine",
        "dose_min": "0.25 mg 2x/sem",
        "dose_max": "0.5–1 mg 2x/sem",
        "popularite": "★★★★☆",
        "dangerosite": "★★☆☆☆",
        "demi_vie": "—",
        "notes": "Essentiel avec Tren/Deca",
    },
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
    # On récupère les couleurs si besoin (mais on ne les injecte pas dans params)
    _ = getattr(TH, color_attr, None)
    _hover = _hover_attr(color_attr)

    params = {}
    if width is not None:
        params["width"] = width
    if height is not None:
        params["height"] = height
    # fusionner kwargs non conflictuels (ne pas inclure fg_color/hover_color)
    for k, v in kwargs.items():
        if k in ("fg_color", "hover_color"):
            continue
        params[k] = v

    # Passer text et cmd en positionnels pour respecter la signature mk_btn
    return mk_btn(parent, text, cmd, **params)


def _user_dir(app):
    d = os.path.join(utils.USERS_DIR, app.current_user)
    Path(d).mkdir(parents=True, exist_ok=True)
    return d


# --- Helpers pour cycle presets (affichage longueur sans popup) ---------------
def _apply_cycle_preset(app, preset):
    """Applique un preset sur le champ longueur (en semaines) et gère visibilité."""
    if preset == "12 semaines":
        try:
            app.cycle_length_var.set("12")
        except Exception:
            try:
                app.cycle_length_entry.delete(0, tk.END)
                app.cycle_length_entry.insert(0, "12")
            except Exception:
                pass
        # masquer le champ longueur (par défaut)
        try:
            app.cycle_length_entry.pack_forget()
        except Exception:
            pass
    elif preset == "16 semaines":
        try:
            app.cycle_length_var.set("16")
        except Exception:
            try:
                app.cycle_length_entry.delete(0, tk.END)
                app.cycle_length_entry.insert(0, "16")
            except Exception:
                pass
        try:
            app.cycle_length_entry.pack_forget()
        except Exception:
            pass
    elif preset == "Personnalisé":
        # afficher le champ longueur pour saisie
        try:
            # pack it if not already packed
            if not app.cycle_length_entry.winfo_ismapped():
                app.cycle_length_entry.pack(side=tk.LEFT, padx=(0, 8))
        except Exception:
            pass


# ── Disclaimer modal ---------------------------------------------------------
def show_cycle_disclaimer(app):
    if getattr(app, "cycle_disclaimer_shown", False):
        show_cycle_screen(app)
        return

    dlg = ctk.CTkToplevel(app.root)
    dlg.title("Avertissement — Cycle hormonal")
    dlg.geometry("660x440")
    dlg.configure(fg_color=TH.BG_CARD)
    dlg.grab_set()
    dlg.focus_set()

    ctk.CTkLabel(dlg, text="⚠️  AVERTISSEMENT MÉDICAL", font=TH.F_H2, text_color=TH.WARNING).pack(
        anchor=tk.W, padx=28, pady=(22, 8)
    )
    mk_sep(dlg).pack(fill=tk.X, padx=28, pady=(0, 14))

    txt = (
        "Les produits anabolisants et hormones (testostérone, hCG, etc.) peuvent "
        "provoquer des effets secondaires graves et irréversibles : troubles "
        "cardiaques, déséquilibres hormonaux, atteintes hépatiques.\n\n"
        "Consultez impérativement un médecin avant toute utilisation.\n\n"
        "En cliquant sur « ACCEPTER » vous reconnaissez avoir été informé(e) de "
        "ces risques et vous assumez l'entière responsabilité de l'usage de ces "
        "informations à titre strictement personnel."
    )
    tb = mk_textbox(dlg, height=180)
    tb.pack(padx=28, pady=(0, 4))
    tb.insert("1.0", txt)
    tb.configure(state="disabled")

    row = ctk.CTkFrame(dlg, fg_color="transparent")
    row.pack(pady=18)

    def _accept_and_continue():
        dlg.destroy()
        app.cycle_disclaimer_shown = True
        show_cycle_screen(app)

    accept_btn = _btn_safe(row, "✅  ACCEPTER", _accept_and_continue, "SUCCESS", width=160, height=TH.BTN_LG)
    accept_btn.pack(side=tk.LEFT, padx=16)
    refuse_btn = _btn_safe(row, "❌  REFUSER", dlg.destroy, "DANGER", width=160, height=TH.BTN_LG)
    refuse_btn.pack(side=tk.LEFT, padx=16)


# ── Modal récapitulatif des produits sélectionnés ----------------------------
def _show_selected_products(app, selected_products):
    dlg = ctk.CTkToplevel(app.root)
    dlg.title("Détails des produits sélectionnés")
    dlg.geometry("900x360")
    dlg.configure(fg_color=TH.BG_CARD)
    dlg.grab_set()
    dlg.focus_set()

    mk_title(dlg, "Détails des produits sélectionnés").pack(anchor=tk.W, padx=16, pady=(12, 6))
    mk_sep(dlg).pack(fill=tk.X, padx=16, pady=(0, 8))

    cols = ("Produit", "Utilité principale", "Dose mini (typique)", "Dose maxi (typique)", "Notes / Demi-vie")
    tree = ttk.Treeview(dlg, columns=cols, show="headings", height=10)
    for c in cols:
        tree.heading(c, text=c)
        if c == "Produit":
            tree.column(c, width=240, anchor=tk.W)
        elif c == "Utilité principale":
            tree.column(c, width=260, anchor=tk.W)
        else:
            tree.column(c, width=140, anchor=tk.CENTER)
    tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    for prod in selected_products:
        info = PRODUCT_INFO.get(prod)
        if info:
            util = info.get("utilite", "")
            dmin = info.get("dose_min", "")
            dmax = info.get("dose_max", "")
            notes = f"{info.get('notes','')} / {info.get('demi_vie','')}"
        else:
            util = "Information non disponible"
            dmin = ""
            dmax = ""
            notes = ""
        tree.insert("", tk.END, values=(prod, util, dmin, dmax, notes))

    btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
    btn_row.pack(pady=8)
    _btn_safe(btn_row, "Fermer", dlg.destroy, "ACCENT", width=120, height=TH.BTN_SM).pack()


# ── Écran Cycle (avec positions inversées : Catégories à gauche, Calendrier/Données à droite) ----------
def show_cycle_screen(app):
    for w in app.content.winfo_children():
        w.destroy()

    screen_header(app.content, "💉  CYCLE HORMONAL", user_name=getattr(app, "selected_user_name", ""), back_cmd=app.show_dashboard)

    scroll = mk_scrollframe(app.content)
    scroll.pack(fill=tk.BOTH, expand=True)

    cols = ctk.CTkFrame(scroll, fg_color="transparent")
    cols.pack(fill=tk.BOTH, expand=True, padx=28, pady=20)
    cols.columnconfigure(0, weight=0)
    cols.columnconfigure(1, weight=1)

    # LEFT COLUMN: Catégories et éléments (inversé)
    left = mk_card(cols)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
    mk_title(left, "CATÉGORIES ET ÉLÉMENTS (sélection multiple possible)").pack(anchor=tk.W, padx=16, pady=(14, 6))
    mk_sep(left).pack(fill=tk.X, padx=16, pady=(0, 10))

    app.cycle_category_listboxes = {}
    cb_row = ctk.CTkFrame(left, fg_color="transparent")
    cb_row.pack(fill=tk.X, padx=16, pady=(0, 8))
    left_col = ctk.CTkFrame(cb_row, fg_color="transparent")
    right_col = ctk.CTkFrame(cb_row, fg_color="transparent")
    left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
    right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

    items = list(CATEGORIES.items())
    for idx, (cid, cname) in enumerate(items):
        parent = left_col if idx % 2 == 0 else right_col
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill=tk.X, pady=6)

        mk_label(row, f"{cname}", size="small", color=TH.TEXT_SUB, width=180).pack(side=tk.LEFT)

        lb_frame = tk.Frame(row, bg="")
        lb_frame.pack(side=tk.LEFT, padx=8)

        scrollbar = tk.Scrollbar(lb_frame, orient=tk.VERTICAL)
        lb = tk.Listbox(lb_frame, selectmode=tk.MULTIPLE, exportselection=False, height=4, yscrollcommand=scrollbar.set, width=36)
        scrollbar.config(command=lb.yview)
        lb.pack(side=tk.LEFT, fill=tk.Y)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        for it in CATEGORY_ITEMS.get(cid, []):
            lb.insert(tk.END, it)

        sel_label = mk_label(row, "0 sélectionné(s)", size="tiny", color=TH.TEXT_MUTED, width=120)
        sel_label.pack(side=tk.LEFT, padx=(8, 0))

        def _on_select(event, lb=lb, lbl=sel_label):
            sel = lb.curselection()
            lbl.configure(text=f"{len(sel)} sélectionné(s)")

        lb.bind("<<ListboxSelect>>", _on_select)
        app.cycle_category_listboxes[cid] = lb

    # RIGHT COLUMN: Calendrier + Données du cycle
    right = ctk.CTkFrame(cols, fg_color="transparent")
    right.grid(row=0, column=1, sticky="nsew")

    # Calendrier (maintenu dans la colonne droite)
    cal_card = mk_card(right)
    cal_card.pack(fill=tk.X, pady=(0, 14))
    mk_title(cal_card, "DATE DE LA PRISE").pack(anchor=tk.W, padx=16, pady=(14, 6))
    mk_sep(cal_card).pack(fill=tk.X, padx=16, pady=(0, 10))

    _cal_style = dict(
        background=TH.BG_CARD2, foreground=TH.TEXT,
        selectbackground=TH.ACCENT, selectforeground=TH.TEXT,
        bordercolor=TH.BORDER,
        headersbackground=TH.BG_CARD, headersforeground=TH.TEXT_SUB,
        normalforeground=TH.TEXT, weekendforeground=TH.ACCENT_GLOW,
        font=("Inter", 10), headersfont=("Inter", 10, "bold"),
    )
    app.cycle_date_entry = Calendar(cal_card, selectmode="day", **_cal_style)
    app.cycle_date_entry.pack(padx=16, pady=(0, 16))

    # Saisie (données du cycle) — placé sous le calendrier dans la colonne droite
    data_card = mk_card(right)
    data_card.pack(fill=tk.X, pady=(0, 14))
    mk_title(data_card, "DONNÉES DU CYCLE").pack(anchor=tk.W, padx=16, pady=(14, 6))
    mk_sep(data_card).pack(fill=tk.X, padx=16, pady=(0, 12))

    app.cycle_entries = {}
    fields = [
        ("Dose testostérone", "Dose testo (mg/sem)", "mg/sem", "Ex: 250"),
        ("hCG", "hCG (UI/sem)", "UI/sem", "Ex: 500"),
        ("Phase", "Phase (blast/cruise)", None, "blast / cruise"),
    ]
    for display, key, unit, ph in fields:
        r = ctk.CTkFrame(data_card, fg_color="transparent")
        r.pack(fill=tk.X, padx=16, pady=6)
        mk_label(r, f"{display}", size="small", color=TH.TEXT_SUB, width=180).pack(side=tk.LEFT)
        e = mk_entry(r, width=190, placeholder=ph)
        e.pack(side=tk.LEFT, padx=8)
        if unit:
            mk_label(r, unit, size="small", color=TH.TEXT_MUTED).pack(side=tk.LEFT)
        app.cycle_entries[key] = e

    # --- Sélecteur de type de cycle et longueur (ajout sans popup)
    preset_frame = ctk.CTkFrame(data_card, fg_color="transparent")
    preset_frame.pack(fill=tk.X, padx=16, pady=(6, 8))

    mk_label(preset_frame, "Type de cycle", size="small", color=TH.TEXT_SUB, width=180).pack(side=tk.LEFT)
    app.cycle_preset_var = tk.StringVar(value="12 semaines")
    presets = ["12 semaines", "16 semaines", "Personnalisé"]
    try:
        preset_menu = ctk.CTkOptionMenu(preset_frame, values=presets, variable=app.cycle_preset_var,
                                        command=lambda v: _apply_cycle_preset(app, v))
    except Exception:
        preset_menu = tk.OptionMenu(preset_frame, app.cycle_preset_var, *presets, command=lambda v: _apply_cycle_preset(app, v))
    preset_menu.pack(side=tk.LEFT, padx=8)

    mk_label(preset_frame, "Longueur (sem)", size="small", color=TH.TEXT_MUTED).pack(side=tk.LEFT, padx=(12, 6))
    app.cycle_length_var = tk.StringVar(value="12")
    length_entry = mk_entry(preset_frame, width=80, placeholder="sem")
    # l'entrée est cachée par défaut ; elle n'apparaît que si "Personnalisé" est sélectionné
    try:
        length_entry.configure(textvariable=app.cycle_length_var)
    except Exception:
        length_entry.insert(0, app.cycle_length_var.get())
    # ne pas packer la longueur ici (masquée par défaut)
    app.cycle_length_entry = length_entry

    # Note
    note_card = mk_card(right)
    note_card.pack(fill=tk.X, pady=(0, 14))
    mk_title(note_card, "NOTES / OBSERVATIONS").pack(anchor=tk.W, padx=16, pady=(14, 6))
    mk_sep(note_card).pack(fill=tk.X, padx=16, pady=(0, 10))
    app.cycle_note_text = mk_textbox(note_card, height=100)
    app.cycle_note_text.pack(fill=tk.X, padx=16, pady=(0, 14))

    # boutons voir détails sélection + sauvegarder
    btn_row = ctk.CTkFrame(right, fg_color="transparent")
    btn_row.pack(fill=tk.X, padx=16, pady=(0, 14))
    _btn_safe(btn_row, "🔎  Voir détails sélection", lambda: _btn_show_selection(app), "ACCENT", width=200, height=TH.BTN_LG).pack(side=tk.LEFT)
    _btn_safe(btn_row, "💾  SAUVEGARDER LE CYCLE", lambda: _save(app), "SUCCESS", width=200, height=TH.BTN_LG).pack(side=tk.RIGHT)

    # Historique
    hist_card = mk_card(right)
    hist_card.pack(fill=tk.BOTH, expand=True)
    mk_title(hist_card, "HISTORIQUE (5 dernières)").pack(anchor=tk.W, padx=16, pady=(14, 6))
    mk_sep(hist_card).pack(fill=tk.X, padx=16, pady=(0, 8))

    apply_treeview_style("Cycle")
    cols_t = ("Date", "Testo mg/sem", "hCG UI/sem", "Phase", "Note", "Categories", "Longueur (sem)")
    app.cycle_tree = ttk.Treeview(hist_card, columns=cols_t, show="headings", height=5)
    for c in cols_t:
        app.cycle_tree.heading(c, text=c)
        if c == "Note":
            app.cycle_tree.column(c, width=200, anchor=tk.W)
        elif c == "Categories":
            app.cycle_tree.column(c, width=300, anchor=tk.W)
        elif c == "Produit":
            app.cycle_tree.column(c, width=240, anchor=tk.W)
        else:
            app.cycle_tree.column(c, width=110, anchor=tk.CENTER)
    app.cycle_tree.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 14))

    # appliquer preset initial (masque longueur sauf si personnalisé)
    _apply_cycle_preset(app, app.cycle_preset_var.get())

    _refresh(app)


# helper construire liste de produits sélectionnés (noms)
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


def _refresh(app):
    if not hasattr(app, "cycle_tree"):
        return
    for r in app.cycle_tree.get_children():
        app.cycle_tree.delete(r)
    fichier = os.path.join(utils.USERS_DIR, getattr(app, "current_user", ""), "cycle.csv")
    if not os.path.exists(fichier):
        return
    try:
        with open(fichier, "r", newline="", encoding="utf-8") as f:
            reader = list(csv.reader(f))
        data_rows = reader[1:] if len(reader) > 1 else []
        for row in reversed(data_rows[-5:]):
            while len(row) < 7:
                row.append("")
            app.cycle_tree.insert("", tk.END, values=(row[0], row[1], row[2], row[3], row[4], row[5], row[6]))
    except Exception:
        pass


def _save(app):
    if not getattr(app, "current_user", None):
        messagebox.showerror("ERAGROK", "Sélectionne un élève.")
        return
    try:
        date = app.cycle_date_entry.get_date()
        testo = app.cycle_entries.get("Dose testo (mg/sem)").get().strip() or "0"
        hcg = app.cycle_entries.get("hCG (UI/sem)").get().strip() or "0"
        phase = app.cycle_entries.get("Phase (blast/cruise)").get().strip() or ""
        note = app.cycle_note_text.get("1.0", tk.END).strip()

        selected = []
        for cid, lb in getattr(app, "cycle_category_listboxes", {}).items():
            try:
                picks = [lb.get(i) for i in lb.curselection()]
                if picks:
                    selected.append(f"{CATEGORIES.get(cid, str(cid))}: " + "; ".join(picks))
            except Exception:
                continue
        categories_field = "; ".join(selected)

        d = _user_dir(app)
        fichier = os.path.join(d, "cycle.csv")
        header = ["Date", "Dose testo (mg/sem)", "hCG (UI/sem)", "Phase (blast/cruise)", "Note", "Categories", "Longueur (sem)"]
        if not os.path.exists(fichier):
            with open(fichier, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(header)
        # récupérer longueur
        try:
            length_val = app.cycle_length_var.get().strip()
        except Exception:
            try:
                length_val = app.cycle_length_entry.get().strip()
            except Exception:
                length_val = ""
        with open(fichier, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([date, testo, hcg, phase, note, categories_field, length_val])

        # clear inputs
        for e in app.cycle_entries.values():
            try:
                e.delete(0, tk.END)
            except Exception:
                pass
        try:
            app.cycle_note_text.delete("1.0", tk.END)
        except Exception:
            pass
        for lb in getattr(app, "cycle_category_listboxes", {}).values():
            try:
                lb.selection_clear(0, tk.END)
            except Exception:
                pass

        # reset longueur si textvariable liée and hide it
        try:
            app.cycle_length_var.set("12")
        except Exception:
            try:
                app.cycle_length_entry.delete(0, tk.END)
                app.cycle_length_entry.insert(0, "12")
            except Exception:
                pass
        try:
            app.cycle_length_entry.pack_forget()
        except Exception:
            pass

        _refresh(app)
        messagebox.showinfo("ERAGROK", f"✔  Cycle du {date} sauvegardé.")
    except Exception as e:
        messagebox.showerror("ERAGROK", str(e))