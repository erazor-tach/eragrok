# ui/theme.py — THRESHOLD · Dark Forge Theme (Flet)
# ─────────────────────────────────────────────────────────────────────────────
# Tokens de design + factory widgets Flet.
# Mobile-first : tout en dp, responsive, touch-friendly (min 44dp tap targets).
# ─────────────────────────────────────────────────────────────────────────────
import flet as ft


# ════════════════════════════════════════════════════════════════════════════
#  TOKENS DE DESIGN
# ════════════════════════════════════════════════════════════════════════════

# Fonds
BG_ROOT    = "#080810"
BG_SIDEBAR = "#0c0c1a"
BG_CARD    = "#10101e"
BG_CARD2   = "#17172a"
BG_INPUT   = "#1b1b2e"
BG_HOVER   = "#22223a"

# Accent : orange forge
ACCENT       = "#f97316"
ACCENT_HOVER = "#ea580c"
ACCENT_DIM   = "#3a1a06"
ACCENT_GLOW  = "#fdba74"

# Fonctionnel
SUCCESS     = "#22c55e"
SUCCESS_HVR = "#16a34a"
DANGER      = "#ef4444"
DANGER_HVR  = "#dc2626"
WARNING     = "#f59e0b"
PURPLE      = "#a855f7"
BLUE        = "#3b82f6"
BLUE_HVR    = "#2563eb"
GRAY        = "#28283c"
GRAY_HVR    = "#36364e"

# Textes
TEXT        = "#eef2ff"
TEXT_SUB    = "#818aaa"
TEXT_MUTED  = "#3c405a"
TEXT_ACCENT = "#f97316"

# Bordures
BORDER      = "#1e1e38"

# Rayons
R_BTN   = 22
R_CARD  = 14
R_INPUT = 10


# ════════════════════════════════════════════════════════════════════════════
#  THEME FLET — appliqué à page.theme
# ════════════════════════════════════════════════════════════════════════════

def get_theme() -> ft.Theme:
    """Retourne le thème Flet THRESHOLD."""
    return ft.Theme(
        color_scheme_seed=ACCENT,
        color_scheme=ft.ColorScheme(
            primary=ACCENT,
            on_primary="#000000",
            secondary=ACCENT_GLOW,
            surface=BG_CARD,
            on_surface=TEXT,
            error=DANGER,
        ),
    )


def apply_page_style(page: ft.Page, title: str = "THRESHOLD"):
    """Configure la page avec le thème dark THRESHOLD."""
    page.title = title
    page.theme = get_theme()
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BG_ROOT
    page.padding = 0
    page.window.width = 420
    page.window.height = 900
    page.window.min_width = 360
    page.window.min_height = 600
    page.scroll = ft.ScrollMode.AUTO


# ════════════════════════════════════════════════════════════════════════════
#  FACTORY WIDGETS
# ════════════════════════════════════════════════════════════════════════════

def mk_card(content: list[ft.Control], color: str = BG_CARD, **kw) -> ft.Container:
    """Carte principale sombre arrondie."""
    return ft.Container(
        content=ft.Column(content, spacing=0),
        bgcolor=color,
        border_radius=R_CARD,
        border=ft.border.all(1, BORDER),
        padding=0,
        margin=ft.margin.only(bottom=12),
        **kw,
    )


def mk_card2(content: list[ft.Control], **kw) -> ft.Container:
    """Carte imbriquée (ton plus clair)."""
    return mk_card(content, color=BG_CARD2, **kw)


def mk_btn(text: str, on_click=None, color: str = ACCENT,
           hover: str = ACCENT_HOVER, width: int = 160, height: int = 40,
           icon: str = None, **kw) -> ft.ElevatedButton:
    """Bouton pill principal."""
    return ft.ElevatedButton(
        content=ft.Text(text, size=13, weight=ft.FontWeight.BOLD, color=TEXT),
        on_click=on_click,
        bgcolor=color,
        color=TEXT,
        width=width,
        height=height,
        icon=icon,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=R_BTN),
            overlay_color=hover,
        ),
        **kw,
    )


def mk_ghost_btn(text: str, on_click=None, width: int = 260,
                  height: int = 48, **kw) -> ft.TextButton:
    """Bouton transparent — navigation sidebar / bottom nav."""
    return ft.TextButton(
        content=ft.Text(text, size=14, color=TEXT),
        on_click=on_click,
        width=width,
        height=height,
        style=ft.ButtonStyle(
            color=TEXT,
            overlay_color=BG_HOVER,
            shape=ft.RoundedRectangleBorder(radius=R_INPUT),
        ),
        **kw,
    )


def mk_label(text: str, size: int = 13, color: str = TEXT,
             weight=None, **kw) -> ft.Text:
    """Label simple."""
    return ft.Text(text, size=size, color=color, weight=weight, **kw)


def mk_title(text: str, color: str = TEXT_ACCENT) -> ft.Text:
    """Titre de section accent."""
    return ft.Text(text, size=14, color=color, weight=ft.FontWeight.BOLD)


def mk_sep() -> ft.Divider:
    """Séparateur fin."""
    return ft.Divider(height=1, color=BORDER)


def mk_badge(text: str, color: str = ACCENT_DIM,
             text_color: str = ACCENT_GLOW) -> ft.Container:
    """Badge pill."""
    return ft.Container(
        content=ft.Text(text, size=11, color=text_color),
        bgcolor=color,
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=10, vertical=3),
    )


def mk_entry(label: str = "", hint: str = "", value: str = "",
             width: int = 260, on_change=None, **kw) -> ft.TextField:
    """Champ de saisie dark."""
    return ft.TextField(
        label=label,
        hint_text=hint,
        value=value,
        width=width,
        bgcolor=BG_INPUT,
        border_color=BORDER,
        focused_border_color=ACCENT,
        color=TEXT,
        label_style=ft.TextStyle(color=TEXT_SUB, size=12),
        hint_style=ft.TextStyle(color=TEXT_MUTED),
        border_radius=R_INPUT,
        text_size=13,
        on_change=on_change,
        **kw,
    )


def mk_dropdown(label: str, options: list[str], value: str = "",
                width: int = 260, on_change=None, **kw) -> ft.Dropdown:
    """Menu déroulant dark."""
    return ft.Dropdown(
        label=label,
        value=value,
        options=[ft.dropdown.Option(o) for o in options],
        width=width,
        bgcolor=BG_INPUT,
        border_color=BORDER,
        focused_border_color=ACCENT,
        color=TEXT,
        label_style=ft.TextStyle(color=TEXT_SUB, size=12),
        border_radius=R_INPUT,
        text_size=13,
        on_select=on_change,
        **kw,
    )


# ════════════════════════════════════════════════════════════════════════════
#  COMPOSANTS MACRO  (réutilisés partout)
# ════════════════════════════════════════════════════════════════════════════

def macro_box(label: str, value: str, sub: str = "",
              color: str = ACCENT_GLOW) -> ft.Container:
    """Box macro individuelle (Calories / Protéines / Glucides / Lipides / Fibres)."""
    return ft.Container(
        content=ft.Column([
            ft.Text(label, size=10, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
            ft.Text(value, size=16, color=color, weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER),
            ft.Text(sub, size=9, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
        ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=BG_CARD2,
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=8, vertical=8),
        expand=True,
    )


def macro_row(cal: float, cal_t: float, prot: float, prot_t: float,
              gluc: float, gluc_t: float, lip: float, lip_t: float,
              fiber: float = 0) -> ft.Row:
    """Ligne complète des 5 macros avec couleurs conditionnelles."""
    def _clr(got, tgt):
        if tgt <= 0: return TEXT_MUTED
        diff = abs(got / tgt * 100 - 100)
        if diff <= 5: return SUCCESS
        if diff <= 12: return ACCENT_GLOW
        return DANGER

    def _pct(got, tgt):
        return f"{got/tgt*100:.0f}%" if tgt > 0 else "—"

    fib_clr = SUCCESS if fiber >= 25 else (ACCENT_GLOW if fiber >= 15 else TEXT_MUTED)

    return ft.Row([
        macro_box("🔥 Cal",   f"{cal:.0f}",  f"/{cal_t:.0f} ({_pct(cal,cal_t)})",   _clr(cal,cal_t)),
        macro_box("🥩 Prot",  f"{prot:.0f}g", f"/{prot_t:.0f} ({_pct(prot,prot_t)})", _clr(prot,prot_t)),
        macro_box("🍚 Gluc",  f"{gluc:.0f}g", f"/{gluc_t:.0f} ({_pct(gluc,gluc_t)})", _clr(gluc,gluc_t)),
        macro_box("🥑 Lip",   f"{lip:.0f}g",  f"/{lip_t:.0f} ({_pct(lip,lip_t)})",   _clr(lip,lip_t)),
        macro_box("🌾 Fib",   f"{fiber:.0f}g", "reco ≥25",                           fib_clr),
    ], spacing=6)


# ════════════════════════════════════════════════════════════════════════════
#  NAVIGATION
# ════════════════════════════════════════════════════════════════════════════

def bottom_nav(page: ft.Page, selected: int = 0,
               on_change=None) -> ft.NavigationBar:
    """Barre de navigation mobile."""
    return ft.NavigationBar(
        selected_index=selected,
        on_change=on_change,
        bgcolor=BG_CARD,
        indicator_color=ACCENT_DIM,
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Dashboard"),
            ft.NavigationBarDestination(icon=ft.Icons.RESTAURANT, label="Nutrition"),
            ft.NavigationBarDestination(icon=ft.Icons.FITNESS_CENTER, label="Training"),
            ft.NavigationBarDestination(icon=ft.Icons.SCIENCE, label="Cycle"),
            ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Profil"),
        ],
    )
