# ════════════════════════════════════════════════════════════════════════════
#  data/theme.py  —  ERAGROK  ·  Dark Bodybuilding Theme
#
#  ➜  Pour changer le look de toute l'appli : modifier UNIQUEMENT ce fichier.
#  ➜  Import dans les autres modules :
#       from data.theme import TH, mk_btn, mk_card, mk_entry, mk_label,
#                              mk_combo, mk_textbox, mk_sep, mk_badge,
#                              mk_radio, mk_checkbox, mk_scrollframe,
#                              apply_root_style, hero_header,
#                              screen_header, apply_treeview_style
# ════════════════════════════════════════════════════════════════════════════

import customtkinter as ctk

# ── mode global  (appelé une seule fois à l'import) ──────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# ════════════════════════════════════════════════════════════════════════════
#  CLASS TH  —  tous les tokens de design
# ════════════════════════════════════════════════════════════════════════════
class TH:

    # ── Fonds ────────────────────────────────────────────────────────────
    BG_ROOT    = "#080810"   # noir profond
    BG_SIDEBAR = "#0c0c1a"
    BG_CARD    = "#10101e"   # carte principale
    BG_CARD2   = "#17172a"   # carte imbriquée
    BG_INPUT   = "#1b1b2e"   # champ de saisie
    BG_HOVER   = "#22223a"   # survol neutre

    # ── Accent : orange forge ─────────────────────────────────────────
    ACCENT       = "#f97316"
    ACCENT_HOVER = "#ea580c"
    ACCENT_DIM   = "#3a1a06"   # fond badge
    ACCENT_GLOW  = "#fdba74"   # texte highlight

    # ── Couleurs fonctionnelles ───────────────────────────────────────
    SUCCESS     = "#22c55e" ; SUCCESS_HVR  = "#16a34a"
    DANGER      = "#ef4444" ; DANGER_HVR   = "#dc2626"
    WARNING     = "#f59e0b" ; WARNING_HVR  = "#d97706"
    PURPLE      = "#a855f7" ; PURPLE_HVR   = "#9333ea"
    BLUE        = "#3b82f6" ; BLUE_HVR     = "#2563eb"
    GRAY        = "#28283c" ; GRAY_HVR     = "#36364e"

    # ── Textes ────────────────────────────────────────────────────────
    TEXT        = "#eef2ff"   # principal
    TEXT_SUB    = "#818aaa"   # secondaire / labels
    TEXT_MUTED  = "#3c405a"   # désactivé / placeholder
    TEXT_ACCENT = "#f97316"   # titres de section

    # ── Bordures ──────────────────────────────────────────────────────
    BORDER      = "#1e1e38"

    # ── Rayons ────────────────────────────────────────────────────────
    R_BTN   = 22   # pill
    R_CARD  = 14
    R_INPUT = 10
    R_BADGE = 20

    # ── Polices ───────────────────────────────────────────────────────
    F_HERO  = ("Inter", 31, "bold")
    F_TITLE = ("Inter", 21, "bold")
    F_H2    = ("Inter", 16, "bold")
    F_H3    = ("Inter", 13, "bold")
    F_BODY  = ("Inter", 12)
    F_SMALL = ("Inter", 11)
    F_BTN   = ("Inter", 12, "bold")
    F_NAV   = ("Inter", 14)
    F_MONO  = ("Courier New", 11)

    # ── Hauteurs bouton ───────────────────────────────────────────────
    BTN_LG = 44
    BTN_MD = 38
    BTN_SM = 30


# ════════════════════════════════════════════════════════════════════════════
#  FACTORY WIDGETS  —  chaque fonction = 1 type de widget stylé
# ════════════════════════════════════════════════════════════════════════════

def mk_btn(parent, text, cmd,
           color=TH.ACCENT, hover=TH.ACCENT_HOVER,
           width=160, height=TH.BTN_MD,
           font=TH.F_BTN, radius=TH.R_BTN, **kw):
    """Bouton pill principal."""
    return ctk.CTkButton(
        parent, text=text, command=cmd,
        fg_color=color, hover_color=hover,
        text_color=TH.TEXT,
        width=width, height=height,
        corner_radius=radius, font=font, **kw)


def mk_ghost_btn(parent, text, cmd, width=224, height=44):
    """Bouton transparent – navigation sidebar."""
    return ctk.CTkButton(
        parent, text=text, command=cmd,
        fg_color="transparent", hover_color=TH.BG_HOVER,
        text_color=TH.TEXT, width=width, height=height,
        corner_radius=TH.R_INPUT, font=TH.F_NAV, anchor="w")


def mk_card(parent, color=TH.BG_CARD, **kw):
    """Carte primaire sombre arrondie."""
    return ctk.CTkFrame(parent, fg_color=color,
                        corner_radius=TH.R_CARD,
                        border_width=1, border_color=TH.BORDER, **kw)


def mk_card2(parent, **kw):
    """Carte imbriquée (ton légèrement plus clair)."""
    return ctk.CTkFrame(parent, fg_color=TH.BG_CARD2,
                        corner_radius=TH.R_CARD,
                        border_width=1, border_color=TH.BORDER, **kw)


def mk_entry(parent, width=260, placeholder="", **kw):
    """Champ de saisie dark arrondi."""
    return ctk.CTkEntry(
        parent, width=width,
        fg_color=TH.BG_INPUT, border_color=TH.BORDER,
        text_color=TH.TEXT,
        placeholder_text=placeholder,
        placeholder_text_color=TH.TEXT_MUTED,
        corner_radius=TH.R_INPUT, font=TH.F_BODY, **kw)


def mk_combo(parent, values, width=260, **kw):
    """Combobox dark arrondie."""
    return ctk.CTkComboBox(
        parent, values=values, state="readonly", width=width,
        fg_color=TH.BG_INPUT, border_color=TH.BORDER,
        button_color=TH.ACCENT, button_hover_color=TH.ACCENT_HOVER,
        dropdown_fg_color=TH.BG_CARD2,
        dropdown_hover_color=TH.BG_HOVER,
        text_color=TH.TEXT, dropdown_text_color=TH.TEXT,
        corner_radius=TH.R_INPUT, font=TH.F_BODY, **kw)


def mk_textbox(parent, height=100, **kw):
    """Zone texte multi-lignes dark."""
    return ctk.CTkTextbox(
        parent, fg_color=TH.BG_INPUT, border_color=TH.BORDER,
        border_width=1, text_color=TH.TEXT,
        corner_radius=TH.R_INPUT, font=TH.F_BODY, height=height, **kw)


def mk_label(parent, text, size="body", color=None, anchor='w', **kw):
    """Label sémantique (hero / title / h2 / h3 / body / small)."""
    fonts = {
        "hero":  TH.F_HERO,  "title": TH.F_TITLE,
        "h2":    TH.F_H2,    "h3":    TH.F_H3,
        "body":  TH.F_BODY,  "small": TH.F_SMALL,
    }
    return ctk.CTkLabel(
        parent, text=text,
        font=fonts.get(size, TH.F_BODY),
        text_color=color or TH.TEXT,
        anchor=anchor, **kw)


def mk_title(parent, text, color=TH.TEXT_ACCENT):
    """Label titre de section couleur accent."""
    return ctk.CTkLabel(parent, text=text,
                        font=TH.F_H3, text_color=color, anchor='w')


def mk_sep(parent, vertical=False):
    """Séparateur 1 px."""
    if vertical:
        return ctk.CTkFrame(parent, fg_color=TH.BORDER,
                            width=1, corner_radius=0)
    return ctk.CTkFrame(parent, fg_color=TH.BORDER,
                        height=1, corner_radius=0)


def mk_badge(parent, text,
             color=TH.ACCENT_DIM, text_color=TH.ACCENT_GLOW):
    """Badge pill coloré."""
    return ctk.CTkLabel(parent, text=f"  {text}  ",
                        font=TH.F_SMALL, fg_color=color,
                        text_color=text_color,
                        corner_radius=TH.R_BADGE)


def mk_scrollframe(parent, **kw):
    """
    ScrollableFrame dark — avec fix scroll molette pour exe PyInstaller.
    CTkScrollableFrame perd les bindings <MouseWheel> dans un .exe frozen.
    On rebind explicitement sur le canvas interne + propagation sur les enfants.
    """
    sf = ctk.CTkScrollableFrame(
        parent, fg_color=TH.BG_ROOT,
        scrollbar_button_color=TH.GRAY,
        scrollbar_button_hover_color=TH.ACCENT,
        corner_radius=0, **kw)

    def _scroll(event):
        # Récupérer le canvas interne de CTkScrollableFrame
        canvas = getattr(sf, "_parent_canvas", None)
        if canvas is None:
            # Chercher le canvas enfant direct
            for child in sf.winfo_children():
                if child.winfo_class() == "Canvas":
                    canvas = child
                    break
        if canvas:
            try:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass

    def _bind_scroll(widget):
        """Bind récursif sur tous les enfants pour garantir la réception."""
        widget.bind("<MouseWheel>", _scroll, add="+")      # Windows
        widget.bind("<Button-4>",   lambda e: _scroll(type("E",(),{"delta":120})()), add="+")  # Linux
        widget.bind("<Button-5>",   lambda e: _scroll(type("E",(),{"delta":-120})()), add="+") # Linux
        for child in widget.winfo_children():
            try: _bind_scroll(child)
            except Exception: pass

    # Bind après que le frame est visible
    def _after_map(event=None, s=sf):
        try: _bind_scroll(s)
        except Exception: pass

    sf.bind("<Map>", _after_map, add="+")
    return sf


def mk_radio(parent, text, value, variable, **kw):
    """RadioButton stylé accent."""
    return ctk.CTkRadioButton(
        parent, text=text, value=value, variable=variable,
        fg_color=TH.ACCENT, hover_color=TH.ACCENT_HOVER,
        text_color=TH.TEXT, font=TH.F_SMALL, **kw)


def mk_checkbox(parent, text, variable, **kw):
    """Checkbox stylée accent."""
    return ctk.CTkCheckBox(
        parent, text=text, variable=variable,
        fg_color=TH.ACCENT, hover_color=TH.ACCENT_HOVER,
        checkmark_color=TH.TEXT, text_color=TH.TEXT,
        font=TH.F_BODY, corner_radius=6, **kw)


# ════════════════════════════════════════════════════════════════════════════
#  HELPERS MISE EN PAGE
# ════════════════════════════════════════════════════════════════════════════

def apply_root_style(root, title="ERAGROK", geometry="1340x900"):
    root.title(title)
    root.geometry(geometry)
    root.configure(bg=TH.BG_ROOT)


def hero_header(parent, title="⚡  ERAGROK", subtitle="COACH BODYBUILDING"):
    """Barre hero – écran d'accueil."""
    hero = ctk.CTkFrame(parent, fg_color=TH.BG_CARD,
                        corner_radius=0, height=82)
    hero.pack(fill='x')
    hero.pack_propagate(False)
    ctk.CTkLabel(hero, text=title,
                 font=TH.F_HERO, text_color=TH.ACCENT).pack(
        side='left', padx=32, pady=14)
    ctk.CTkLabel(hero, text=subtitle,
                 font=TH.F_SMALL, text_color=TH.TEXT_MUTED).pack(
        side='left', padx=6, pady=32)
    # ligne déco accent
    ctk.CTkFrame(parent, fg_color=TH.ACCENT,
                 height=3, corner_radius=0).pack(fill='x')
    return hero


def screen_header(parent, title, user_name="", back_cmd=None):
    """Barre de titre – écrans internes."""
    outer = ctk.CTkFrame(parent, fg_color=TH.BG_CARD,
                         corner_radius=0)
    outer.pack(fill='x')
    bar = ctk.CTkFrame(outer, fg_color="transparent", height=58)
    bar.pack(fill='x', padx=20)
    bar.pack_propagate(False)
    ctk.CTkLabel(bar, text=title,
                 font=TH.F_TITLE, text_color=TH.TEXT).pack(
        side='left', pady=10)
    if user_name:
        mk_badge(bar, user_name.upper()).pack(side='left', padx=10, pady=18)
    if back_cmd:
        mk_btn(bar, "←  Retour", back_cmd,
               color=TH.GRAY, hover=TH.GRAY_HVR,
               width=120, height=TH.BTN_SM).pack(side='right', pady=13)
    ctk.CTkFrame(parent, fg_color=TH.ACCENT,
                 height=2, corner_radius=0).pack(fill='x')
    return outer


def apply_treeview_style(style_name):
    """Style ttk.Treeview cohérent avec le thème dark."""
    from tkinter import ttk
    s = ttk.Style()
    try:
        s.theme_use('clam')
    except Exception:
        pass
    s.configure(f"{style_name}.Treeview",
                background=TH.BG_CARD2, foreground=TH.TEXT,
                fieldbackground=TH.BG_CARD2, rowheight=28,
                font=("Inter", 11), borderwidth=0)
    s.configure(f"{style_name}.Treeview.Heading",
                background=TH.BG_CARD, foreground=TH.TEXT_SUB,
                font=("Inter", 11, "bold"), relief='flat')
    s.map(f"{style_name}.Treeview",
          background=[('selected', TH.ACCENT_DIM)],
          foreground=[('selected', TH.ACCENT_GLOW)])
