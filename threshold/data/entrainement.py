# data/entrainement.py — THRESHOLD · Module Entraînement (Flet)
# ─────────────────────────────────────────────────────────────────────────────
# Port complet d'entrainement_module.py d'ERAGROK vers Flet.
# Logique métier identique, UI reconstruite en composants Flet mobile-first.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import calendar
import datetime
import json
import random
from typing import Optional

import flet as ft

from ui.theme import (
    ACCENT, ACCENT_DIM, ACCENT_GLOW, ACCENT_HOVER,
    BG_CARD, BG_CARD2, BG_INPUT, BG_ROOT,
    BORDER, BLUE, BLUE_HVR, DANGER, DANGER_HVR,
    GRAY, GRAY_HVR, PURPLE, SUCCESS, SUCCESS_HVR,
    TEXT, TEXT_ACCENT, TEXT_MUTED, TEXT_SUB, WARNING,
    R_CARD, R_INPUT,
    mk_btn, mk_card, mk_dropdown, mk_entry,
    mk_label, mk_sep, mk_title, mk_badge,
)
from data import db as _db, utils
from data import training_techniques as tt

# ── Logique métier extraite (proposition #9) ──────────────────────────────────
from data.logic.entrainement_logic import (
    _parse_date, _fmt_tech, _pool, _gen_month_lines,
)

DATE_FMT = "%d/%m/%Y"
TS_FMT   = "%Y-%m-%d %H:%M"
DAY_FR   = {0:"Lun", 1:"Mar", 2:"Mer", 3:"Jeu", 4:"Ven", 5:"Sam", 6:"Dim"}
GROUPES  = ["Pecs","Dos","Cuisses","Épaules","Bras","Fessiers","Mollets","Abdominaux","Full body","Alpha body"]
WE_OPTIONS = ["Off","Pecs","Cuisses","Épaules","Dos","Bras"]


# ══════════════════════════════════════════════════════════════════════════════
#  CLASSE PRINCIPALE — EntrainementView
# ══════════════════════════════════════════════════════════════════════════════

class EntrainementView:
    """
    Module entraînement complet :
    - Onglets : Catalogue / Planning / Programme / Historique
    - Logique métier identique à ERAGROK
    """

    def __init__(self, page: ft.Page, app_state: dict):
        self.page      = page
        self.app_state = app_state

        self.state = {
            "selected_date":   datetime.date.today(),
            "view_mode":       "Jour",       # Jour | Semaine | Mois
            "last_tech":       None,         # dict technique sélectionnée
            "programme_lines": [],           # lignes du programme courant
            "groupes":         set(),        # groupes musculaires cochés
            "prog_name":       "Standard",
            "gen_cats":        {"SARCOPLASMIQUE", "MIXTE", "MYOFIBRILLAIRE"},
            "sat_focus":       "Off",
            "sun_focus":       "Off",
            "note":            "",
            "tab":             0,            # 0=Catalogue 1=Planning 2=Programme 3=Historique
        }

        # Contrôles réactifs
        self._tab_body:     Optional[ft.Column] = None
        self._plan_col:     Optional[ft.Column] = None
        self._prog_col:     Optional[ft.Column] = None
        self._hist_col:     Optional[ft.Column] = None
        self._detail_text:  Optional[ft.Text]   = None
        self._search_field: Optional[ft.TextField] = None
        self._tech_col:     Optional[ft.Column] = None
        self._date_field:   Optional[ft.TextField] = None

        self.root_col  = ft.Stack(expand=True)
        self._main_col = ft.Column(spacing=0, expand=True)
        self._modal_layer = ft.Container(visible=False, expand=True,
                                          bgcolor="#80000000",
                                          alignment=ft.alignment.Alignment(0, 1))
        self.root_col.controls = [self._main_col, self._modal_layer]
        self._build_all()
        self._load_last_programme()

    def get_view(self) -> ft.Column:
        return self.root_col

    # ══════════════════════════════════════════════════════════════════════════
    #  CONSTRUCTION UI
    # ══════════════════════════════════════════════════════════════════════════

    def _build_all(self):
        self._main_col.controls.clear()
        self._main_col.controls.append(self._build_hero())
        scroll_col = ft.Column(
            spacing=0, expand=True, scroll=ft.ScrollMode.AUTO,
            controls=[
                self._collapsible_section("  📋  PROGRAMME",
                                          self._build_programme_tab, collapsed=False),
                self._collapsible_section("  📅  PLANNING",
                                          self._build_planning_tab, collapsed=True),
                self._collapsible_section("  🕐  HISTORIQUE",
                                          self._build_historique_tab, collapsed=True),
                self._collapsible_section("  📚  CATALOGUE",
                                          self._build_catalogue_tab, collapsed=True),
                self._collapsible_section("  🏋  EXERCICES",
                                          self._build_exercices_tab, collapsed=True),
            ],
        )
        self._main_col.controls.append(scroll_col)

    def _collapsible_section(self, title: str, builder_fn,
                              collapsed: bool = True) -> ft.Container:
        """Section collapsible — même pattern que dashboard et nutrition."""
        icon_ref = ft.Ref[ft.Text]()
        body_ref = ft.Ref[ft.Container]()
        state    = {"open": not collapsed, "built": False}

        def _toggle(e=None):
            state["open"] = not state["open"]
            icon_ref.current.value = "▲" if state["open"] else "▼"
            if state["open"] and not state["built"]:
                try:
                    body_ref.current.content = builder_fn()
                    state["built"] = True
                except Exception:
                    body_ref.current.content = ft.Text(
                        "Erreur chargement", color=TEXT_MUTED, size=12)
            body_ref.current.visible = state["open"]
            try: e.page.update()
            except Exception: pass

        header = ft.Container(
            content=ft.Row([
                ft.Text(title, size=13, color=TEXT_ACCENT,
                        weight=ft.FontWeight.BOLD, expand=True),
                ft.Text("▼" if collapsed else "▲",
                        size=12, color=ACCENT, ref=icon_ref),
            ], spacing=8),
            on_click=_toggle,
            bgcolor=BG_CARD,
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )

        if not collapsed:
            try:
                initial_content = builder_fn()
                state["built"] = True
            except Exception as _ex:
                import traceback; traceback.print_exc()
                initial_content = ft.Text(f"Erreur: {_ex}", color=DANGER, size=11)
        else:
            initial_content = ft.Container()

        body = ft.Container(
            content=initial_content,
            visible=not collapsed,
            ref=body_ref,
            expand=True,
        )

        return ft.Container(
            content=ft.Column([header, body], spacing=0),
            bgcolor=BG_CARD,
            border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            margin=ft.margin.only(bottom=8),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
        )

    def _build_hero(self) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("🏋  ENTRAÎNEMENT", size=22, color=ACCENT,
                            weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    mk_badge(self.app_state.get("user_info", {}).get("name", "").upper() or "—"),
                ]),
                ft.Text("Catalogue · Planning · Programme · Historique",
                        size=11, color=TEXT_MUTED),
            ], spacing=4),
            bgcolor=BG_CARD,
            padding=ft.padding.symmetric(horizontal=20, vertical=16),
            margin=ft.margin.only(bottom=3),
        )

    # ── Onglet 0 : Catalogue ─────────────────────────────────────────────────

    def _build_catalogue_tab(self) -> ft.Container:
        self._search_field = mk_entry(
            label="🔍 Rechercher", hint="nom de technique...", width=280,
            on_change=lambda e: self._rebuild_tech_list(e.control.value),
        )
        self._detail_text = ft.Text("", size=12, color=TEXT_SUB)
        self._tech_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)
        self._selected_tech_container = None

        self._rebuild_tech_list("")

        self._btn_modifier  = mk_btn("✏ Modifier",   self._on_tech_edit,
                                     color=ACCENT,  hover=ACCENT_HOVER, width=130, height=38)
        self._btn_supprimer = mk_btn("🗑 Supprimer", self._on_tech_delete,
                                     color=DANGER,  hover=DANGER_HVR,   width=130, height=38)
        btn_ajouter = mk_btn("➕ Nouvelle", self._on_tech_add,
                             color=SUCCESS, hover=SUCCESS_HVR, width=150, height=38)

        return ft.Container(
            content=ft.Column([
                ft.Container(content=self._search_field,
                             padding=ft.padding.symmetric(horizontal=12, vertical=8)),
                ft.Container(
                    content=self._tech_col,
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=12),
                ),
                ft.Container(
                    content=ft.Column([
                        mk_title("  🔎  DÉTAIL TECHNIQUE"),
                        mk_sep(),
                        ft.Container(content=self._detail_text,
                                     padding=ft.Padding.all(10)),
                    ]),
                    bgcolor=BG_CARD2, border_radius=10,
                    margin=ft.margin.symmetric(horizontal=12),
                    padding=ft.padding.symmetric(vertical=8),
                ),
                ft.Container(
                    content=ft.Row([btn_ajouter, self._btn_modifier, self._btn_supprimer],
                                   spacing=8, wrap=True),
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                ),
            ], spacing=0),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            margin=ft.margin.symmetric(horizontal=12, vertical=6),
        )

    def _rebuild_tech_list(self, query: str = ""):
        if self._tech_col is None:
            return
        self._tech_col.controls.clear()
        q = query.lower()

        cats: dict[str, list] = {}
        for t in tt.get_all_techniques():
            if q and q not in t["nom"].lower() and q not in t.get("notes", "").lower():
                continue
            cats.setdefault(t.get("categorie", "Autre"), []).append(t)

        CAT_ORDER   = {"SARCOPLASMIQUE": 0, "MIXTE": 1, "MYOFIBRILLAIRE": 2}
        CAT_LABELS  = {"SARCOPLASMIQUE": "🔥 Sarcoplasmique", "MIXTE": "⚡ Mixte", "MYOFIBRILLAIRE": "💪 Myofibrillaire"}
        CAT_COLORS  = {"SARCOPLASMIQUE": ACCENT, "MIXTE": WARNING, "MYOFIBRILLAIRE": PURPLE}
        ordered = sorted(cats.items(), key=lambda x: CAT_ORDER.get(x[0], 99))

        for cat, techs in ordered:
            cat_color = CAT_COLORS.get(cat, TEXT_SUB)
            label     = CAT_LABELS.get(cat, cat)

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

            def _make_item(t):
                is_custom = t.get("_custom", False)
                item_ref  = ft.Ref[ft.Container]()
                def _click(e, tech=t, ref=item_ref):
                    prev = self._selected_tech_container
                    if prev and prev.current:
                        prev.current.bgcolor = "transparent"
                    if ref.current:
                        ref.current.bgcolor = ACCENT_DIM
                    self._selected_tech_container = ref
                    try: e.page.update()
                    except Exception: pass
                    self._on_tech_select(tech)
                return ft.Container(
                    content=ft.Row([
                        ft.Text(f"  {t['nom']}", size=12, color=TEXT, expand=True),
                        ft.Text("✦", size=9, color=ACCENT, tooltip="Personnalisée") if is_custom else ft.Container(width=0),
                        ft.Text(f"[{t.get('reps','—')}]", size=10, color=TEXT_MUTED),
                    ]),
                    padding=ft.padding.symmetric(horizontal=8, vertical=6),
                    border_radius=6, ink=True, bgcolor="transparent",
                    ref=item_ref, on_click=_click,
                )

            body_col = ft.Column([_make_item(t) for t in techs], spacing=0,
                                  ref=_body_ref, visible=False)
            header = ft.Container(
                content=ft.Row([
                    ft.Text("▶", size=11, color=cat_color,
                            weight=ft.FontWeight.BOLD, ref=_icon_ref),
                    ft.Text(f" {label}", size=11, color=cat_color,
                            weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text(str(len(techs)), size=10, color=TEXT_MUTED),
                ], spacing=4),
                bgcolor=BG_CARD2, border_radius=6,
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                ink=True,
                on_click=_make_toggle(_state, _icon_ref, _body_ref),
            )
            self._tech_col.controls.append(header)
            self._tech_col.controls.append(body_col)

        self._safe_update()

    def _on_tech_select(self, tech: dict):
        self.state["last_tech"] = tech
        if self._detail_text is None:
            return
        badge = " [✦ personnalisée]" if tech.get("_custom") else ""
        lines = [
            f"Technique : {tech['nom']}{badge}",
            f"Catégorie : {tech.get('categorie','—')}",
            f"Reps      : {tech.get('reps','—')}",
            f"Charge    : {tech.get('charge','—')}",
            f"Repos     : {tech.get('repos','—')}",
            f"Objectif  : {tech.get('objectif','—')}",
            f"Difficulté: {tech.get('difficulty_level','—')}/5",
        ]
        if tech.get("notes"):
            lines += ["", f"Notes : {tech['notes']}"]
        self._detail_text.value = "\n".join(lines)
        self._safe_update()

    # ── CRUD Techniques ───────────────────────────────────────────────────────

    def _custom_techs_path(self) -> str:
        from data.utils import USERS_DIR
        import os
        user = self.app_state.get("current_user", "default") or "default"
        folder = os.path.join(USERS_DIR, user)
        os.makedirs(folder, exist_ok=True)
        return os.path.join(folder, "custom_techniques.json")

    def _load_custom_techs(self) -> list:
        import json, os
        p = self._custom_techs_path()
        if not os.path.exists(p):
            return []
        try:
            return json.load(open(p, encoding="utf-8"))
        except Exception:
            return []

    def _save_custom_techs(self, techs: list):
        import json
        json.dump(techs, open(self._custom_techs_path(), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

    def _on_tech_add(self, e=None):
        self._open_tech_modal(None)

    def _on_tech_edit(self, e=None):
        tech = self.state.get("last_tech")
        if not tech:
            self._snack("Sélectionne d'abord une technique.", WARNING); return
        self._open_tech_modal(tech)

    def _on_tech_delete(self, e=None):
        tech = self.state.get("last_tech")
        if not tech:
            self._snack("Sélectionne d'abord une technique.", WARNING); return
        if not tech.get("_custom"):
            self._snack("Les techniques de base ne peuvent pas être supprimées.", WARNING); return
        customs = self._load_custom_techs()
        customs = [t for t in customs if t.get("id") != tech.get("id")]
        self._save_custom_techs(customs)
        self.state["last_tech"] = None
        self._selected_tech_container = None
        if self._detail_text:
            self._detail_text.value = ""
        # Patch training_techniques en mémoire
        tt.TECHNIQUES[:] = [t for t in tt.TECHNIQUES if t.get("id") != tech.get("id")]
        self._rebuild_tech_list("")
        self._snack("✔ Technique supprimée.", SUCCESS)

    def _open_tech_modal(self, tech):
        """Modal inline via _modal_layer (Stack) — 100% fiable, zéro page.overlay."""
        is_edit = tech is not None
        if is_edit and not tech.get("_custom"):
            import copy
            tech = copy.deepcopy(tech)
            tech["_custom"] = True
            tech["id"] = f"custom_{tech['id']}"

        CATS = ["SARCOPLASMIQUE", "MIXTE", "MYOFIBRILLAIRE"]
        _CAT_LABELS = {"SARCOPLASMIQUE": "🔥 Sarcoplasmique", "MIXTE": "⚡ Mixte", "MYOFIBRILLAIRE": "💪 Myofibrillaire"}

        def _mk_field(label, value="", **kw):
            return ft.TextField(
                label=label, value=value,
                bgcolor=BG_INPUT, border_color=BORDER,
                focused_border_color=ACCENT, color=TEXT,
                label_style=ft.TextStyle(color=TEXT_SUB, size=11),
                border_radius=8, text_size=13, **kw)

        f_nom    = _mk_field("Nom *",          tech.get("nom","")   if tech else "")
        f_reps   = _mk_field("Reps",           tech.get("reps","")  if tech else "", width=130)
        f_charge = _mk_field("Charge",         tech.get("charge","") if tech else "", width=130)
        f_repos  = _mk_field("Repos",          tech.get("repos","") if tech else "", width=130)
        f_obj    = _mk_field("Objectif",       tech.get("objectif","") if tech else "")
        f_diff   = _mk_field("Difficulté 1-5", str(tech.get("difficulty_level",3)) if tech else "3", width=130)
        f_notes  = _mk_field("Notes",          tech.get("notes","") if tech else "",
                              multiline=True, min_lines=2, max_lines=3)
        f_cat = ft.Dropdown(
            label="Catégorie *",
            value=tech.get("categorie", CATS[0]) if tech else CATS[0],
            options=[
                ft.dropdown.Option(key=c, text=_CAT_LABELS.get(c, c))
                for c in CATS
            ],
            bgcolor=BG_INPUT, border_color=BORDER,
            focused_border_color=ACCENT, color=TEXT,
            label_style=ft.TextStyle(color=TEXT_SUB, size=11),
            border_radius=8, text_size=13,
            on_select=lambda e: None,
        )

        def _close(ev=None):
            self._modal_layer.visible = False
            self._modal_layer.content = None
            self._safe_update()

        def _save(ev=None):
            nom = f_nom.value.strip()
            if not nom:
                self._snack("Le nom est obligatoire.", DANGER); return
            cat = f_cat.value or CATS[0]
            try: diff = int(f_diff.value)
            except Exception: diff = 3
            import re
            tid = (tech.get("id") if tech else None) or                   "custom_" + re.sub(r"[^a-z0-9]", "_", nom.lower())[:20]
            new_tech = {
                "id": tid, "nom": nom, "categorie": cat,
                "reps": f_reps.value.strip(), "charge": f_charge.value.strip(),
                "repos": f_repos.value.strip(), "objectif": f_obj.value.strip(),
                "difficulte": diff, "difficulty_level": diff,
                "programme_recommande": (
                    "Sarco" if cat == "SARCOPLASMIQUE" else
                    "Myofi" if cat == "MYOFIBRILLAIRE" else
                    "Standard"
                ),
                "notes": f_notes.value.strip(), "_custom": True,
            }
            customs = self._load_custom_techs()
            idx = next((i for i,t in enumerate(customs) if t.get("id")==tid), None)
            if idx is not None: customs[idx] = new_tech
            else: customs.append(new_tech)
            self._save_custom_techs(customs)
            idx2 = next((i for i,t in enumerate(tt.TECHNIQUES) if t.get("id")==tid), None)
            if idx2 is not None: tt.TECHNIQUES[idx2] = new_tech
            else: tt.TECHNIQUES.append(new_tech)
            self.state["last_tech"] = new_tech
            self._selected_tech_container = None
            _close()
            self._rebuild_tech_list("")
            self._snack(f"✔ Technique « {nom} » sauvegardée.", SUCCESS)

        panel = ft.Container(
            content=ft.Column([
                # Titre + fermer
                ft.Row([
                    ft.Text("✏ Modifier" if is_edit else "➕ Nouvelle technique",
                            color=ACCENT, weight=ft.FontWeight.BOLD, size=15, expand=True),
                    ft.ElevatedButton(
                        content=ft.Text("✕ Fermer", size=12, color=TEXT),
                        bgcolor=GRAY, on_click=_close, height=34,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(height=1, color=BORDER),
                # Champs
                ft.Column([
                    f_nom, f_cat,
                    ft.Row([f_reps, f_charge, f_repos], spacing=8, wrap=True),
                    f_obj,
                    ft.Row([f_diff], spacing=8),
                    f_notes,
                ], spacing=10, scroll=ft.ScrollMode.AUTO, expand=True),
                # Actions
                ft.Row([
                    ft.ElevatedButton(
                        content=ft.Text("✕ Annuler", size=13, color=TEXT,
                                        weight=ft.FontWeight.BOLD),
                        bgcolor=GRAY, on_click=_close,
                        width=130, height=42,
                    ),
                    ft.ElevatedButton(
                        content=ft.Text("💾 Sauvegarder", size=13, color=TEXT,
                                        weight=ft.FontWeight.BOLD),
                        bgcolor=SUCCESS, on_click=_save,
                        width=170, height=42,
                    ),
                ], spacing=10),
            ], spacing=12, expand=True),
            bgcolor=BG_CARD,
            border_radius=16,
            padding=ft.Padding.all(20),
            width=380,
            shadow=ft.BoxShadow(blur_radius=24, color="#60000000"),
        )

        self._modal_layer.content = panel
        self._modal_layer.visible = True
        self._safe_update()

    # ── Onglet Exercices : Catalogue docteur-fitness ──────────────────────────

    def _build_exercices_tab(self) -> ft.Container:
        """Accordéon des exercices par groupe musculaire (exercices_catalogue.py)."""
        from data import exercices_catalogue as ec

        self._exo_col    = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)
        self._exo_detail = ft.Text("", size=12, color=TEXT_SUB)
        self._exo_search = mk_entry(
            label="🔍 Rechercher", hint="nom, muscle...", width=280,
            on_change=lambda e: self._rebuild_exo_list(e.control.value),
        )

        self._rebuild_exo_list("")

        return ft.Container(
            content=ft.Column([
                ft.Container(content=self._exo_search,
                             padding=ft.padding.symmetric(horizontal=12, vertical=8)),
                ft.Container(
                    content=self._exo_col,
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=12),
                ),
                ft.Container(
                    content=ft.Column([
                        mk_title("  🔎  DÉTAIL EXERCICE"),
                        mk_sep(),
                        ft.Container(content=self._exo_detail,
                                     padding=ft.Padding.all(10)),
                    ]),
                    bgcolor=BG_CARD2, border_radius=10,
                    margin=ft.margin.symmetric(horizontal=12),
                    padding=ft.padding.symmetric(vertical=8),
                ),
            ], spacing=0, expand=True),
            expand=True,
        )

    def _rebuild_exo_list(self, query: str = ""):
        if not hasattr(self, "_exo_col") or self._exo_col is None:
            return
        self._exo_col.controls.clear()
        from data import exercices_catalogue as ec

        exos = ec.search_exercices(query) if query.strip() else ec.get_all_exercices()

        # Grouper par catégorie
        cats: dict[str, list] = {}
        for ex in exos:
            cats.setdefault(ex["cat"], []).append(ex)

        ordered = sorted(cats.items(), key=lambda x: ec.CAT_ORDER.get(x[0], 99))

        # Couleurs par groupe
        COL_HAUT = BLUE
        COL_BAS  = SUCCESS
        CAT_COLORS = {
            "PECS": COL_HAUT, "DOS": COL_HAUT, "EPAULES": COL_HAUT,
            "BICEPS": COL_HAUT, "TRICEPS": COL_HAUT,
            "ABDOS": COL_BAS, "QUADRICEPS": COL_BAS, "FESSIERS": COL_BAS,
            "ISCHIO": COL_BAS, "MOLLETS": COL_BAS, "FULL_BODY": ACCENT,
        }

        for cat, items in ordered:
            cat_color = CAT_COLORS.get(cat, TEXT_SUB)
            icon      = ec.CAT_ICONS.get(cat, "•")
            label     = ec.CAT_LABELS.get(cat, cat)

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

            def _make_exo_item(ex):
                item_ref = ft.Ref[ft.Container]()
                diff     = ex.get("difficulte", 1)
                stars    = "★" * diff + "☆" * (5 - diff)
                def _click(e, exo=ex, ref=item_ref):
                    # Désélection précédent
                    if hasattr(self, "_exo_selected") and self._exo_selected and self._exo_selected.current:
                        self._exo_selected.current.bgcolor = "transparent"
                    if ref.current:
                        ref.current.bgcolor = ACCENT_DIM
                    self._exo_selected = ref
                    # Afficher le détail
                    lines = [
                        f"Exercice   : {exo['nom']}",
                        f"Groupe     : {ec.CAT_LABELS.get(exo['cat'], exo['cat'])}",
                        f"Équipement : {exo.get('equipement', '—')}",
                        f"Reps       : {exo.get('reps', '—')}",
                        f"Difficulté : {stars}",
                    ]
                    if exo.get("muscles_secondaires"):
                        lines.append(f"Muscles 2° : {exo['muscles_secondaires']}")
                    if exo.get("notes"):
                        lines += ["", f"Notes : {exo['notes']}"]
                    if hasattr(self, "_exo_detail") and self._exo_detail:
                        self._exo_detail.value = "\n".join(lines)
                    try: e.page.update()
                    except Exception: pass
                return ft.Container(
                    content=ft.Row([
                        ft.Text(f"  {ex['nom']}", size=12, color=TEXT, expand=True),
                        ft.Text(ex.get("equipement", ""), size=9, color=TEXT_MUTED),
                    ]),
                    padding=ft.padding.symmetric(horizontal=8, vertical=6),
                    border_radius=6, ink=True, bgcolor="transparent",
                    ref=item_ref, on_click=_click,
                )

            body_col = ft.Column([_make_exo_item(ex) for ex in items],
                                  spacing=0, ref=_body_ref, visible=False)
            header = ft.Container(
                content=ft.Row([
                    ft.Text("▶", size=11, color=cat_color,
                            weight=ft.FontWeight.BOLD, ref=_icon_ref),
                    ft.Text(f" {icon} {label}", size=11, color=cat_color,
                            weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text(str(len(items)), size=10, color=TEXT_MUTED),
                ], spacing=4),
                bgcolor=BG_CARD2, border_radius=6,
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
                ink=True,
                on_click=_make_toggle(_state, _icon_ref, _body_ref),
            )
            self._exo_col.controls.append(header)
            self._exo_col.controls.append(body_col)

        self._safe_update()


    # ── Onglet 1 : Planning ──────────────────────────────────────────────────

    def _build_planning_tab(self) -> ft.Container:
        today = datetime.date.today()
        self._date_field = mk_entry(
            label="Date (JJ/MM/AAAA)", hint=today.strftime(DATE_FMT),
            value=today.strftime(DATE_FMT), width=150,
            on_change=lambda e: self._on_date_change(e.control.value),
        )

        def _open_cal_planning(e):
            from data.widgets import show_date_picker
            def _on_date(date_str):
                self._date_field.value = date_str
                self._on_date_change(date_str)
            show_date_picker(self.page, self._date_field.value, _on_date)

        cal_btn_planning = ft.ElevatedButton(
            content=ft.Text("📅", size=18),
            bgcolor=BG_CARD2, color=TEXT, tooltip="Choisir une date",
            on_click=_open_cal_planning,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8),
                                 padding=ft.Padding.all(0)),
            width=44, height=44,
        )

        view_dd = mk_dropdown(
            "Vue", ["Jour", "Semaine", "Mois"],
            value=self.state["view_mode"], width=140,
            on_change=lambda e: self._on_view_change(e.control.value),
        )

        self._plan_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)
        self._refresh_plan_display()

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        mk_title("  📅  PLANNING"),
                        mk_sep(),
                    ]),
                    padding=ft.padding.only(left=16, right=16, top=14, bottom=8),
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Row([self._date_field, cal_btn_planning], spacing=0),
                        view_dd,
                    ], spacing=12, wrap=True),
                    padding=ft.padding.symmetric(horizontal=16),
                ),
                ft.Container(
                    content=self._plan_col,
                    expand=True,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                ),
                ft.Container(
                    content=ft.Row([
                        mk_btn("➕ Ajouter", self._on_add_to_plan,
                               color=ACCENT, hover=ACCENT_HOVER, width=130, height=38),
                        mk_btn("🗑 Supprimer", self._on_del_plan_item,
                               color=DANGER, hover=DANGER_HVR, width=130, height=38),
                        mk_btn("↻ Rafraîchir", lambda e: self._refresh_plan_display(),
                               color=GRAY, hover=GRAY_HVR, width=130, height=38),
                    ], spacing=8, wrap=True),
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                ),
                ft.Container(height=10),
            ], spacing=0),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            margin=ft.margin.symmetric(horizontal=12, vertical=6),
        )

    def _refresh_plan_display(self):
        if self._plan_col is None:
            return
        self._plan_col.controls.clear()
        plan = self._read_plan()
        sd   = self.state["selected_date"]
        mode = self.state["view_mode"]

        entries = []
        if mode == "Jour":
            ds = sd.strftime(DATE_FMT)
            day_ents = [e for e in plan if e.get("date") == ds]
            if not day_ents:
                entries.append((f"Aucune séance pour {ds}", TEXT_MUTED, None))
            else:
                for e in day_ents:
                    entries.append((f"{ds} — {e['line'] or e['prog']}", TEXT, e))

        elif mode == "Semaine":
            start = sd - datetime.timedelta(days=sd.weekday())
            for i in range(7):
                d  = start + datetime.timedelta(i)
                ds = d.strftime(DATE_FMT)
                entries.append((f"─── {ds} ({d.strftime('%a')}) ───", ACCENT_GLOW, None))
                day_ents = [e for e in plan if e.get("date") == ds]
                for e in day_ents:
                    entries.append((f"  {e['line'] or e['prog']}", TEXT, e))
                if not day_ents:
                    entries.append(("  (repos)", TEXT_MUTED, None))

        else:  # Mois
            first = sd.replace(day=1)
            _, nd = calendar.monthrange(first.year, first.month)
            for d in range(1, nd + 1):
                day = first.replace(day=d)
                ds  = day.strftime(DATE_FMT)
                day_ents = [e for e in plan if e.get("date") == ds]
                if day_ents:
                    entries.append((f"─── {ds} ───", ACCENT_GLOW, None))
                    for e in day_ents:
                        entries.append((f"  {e['line'] or e['prog']}", TEXT, e))

        for text, color, entry in entries:
            self._plan_col.controls.append(
                ft.Container(
                    content=ft.Text(text, size=12, color=color),
                    bgcolor=BG_CARD2 if entry else "transparent",
                    border_radius=6,
                    padding=ft.padding.symmetric(horizontal=8, vertical=5),
                    ink=bool(entry),
                    data=entry,
                    on_click=(lambda e: self._on_plan_item_click(e.control.data)) if entry else None,
                )
            )
        self._safe_update()

    def _on_plan_item_click(self, entry):
        # Sélectionner l'entrée pour suppression éventuelle
        self.state["_selected_plan_entry"] = entry

    def _read_plan(self) -> list:
        try:
            rows = _db.planning_get_all(self._fake_app())
            return [{"date": r.get("date"), "line": r.get("line",""),
                     "prog": r.get("programme","")} for r in rows]
        except Exception:
            return []

    # ── Onglet 2 : Programme ─────────────────────────────────────────────────

    def _build_programme_tab(self) -> ft.Container:
        GROUPES = ["Pecs", "Dos", "Cuisses", "Épaules", "Bras",
                   "Fessiers", "Mollets", "Abdominaux", "Full body"]
        DUREES  = ["1 semaine", "1 mois", "2 mois", "6 mois", "1 an"]
        DAYS_LABELS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

        # ── Catégories ──
        cat_checks = []
        for cat, lbl, col in [
            ("SARCOPLASMIQUE", "Sarcoplasmique", ACCENT),
            ("MIXTE",          "Mixte",          WARNING),
            ("MYOFIBRILLAIRE", "Myofibrillaire", PURPLE),
        ]:
            cb = ft.Checkbox(
                label=lbl, value=cat in self.state["gen_cats"],
                fill_color={ft.ControlState.SELECTED: col},
                label_style=ft.TextStyle(color=TEXT, size=12),
                on_change=lambda e, c=cat: self._on_gen_cat_toggle(c, e.control.value),
            )
            cat_checks.append(cb)

        # ── Durée ──
        dur_dd = mk_dropdown("Durée", DUREES,
                             value=self.state.get("gen_duree", "1 mois"), width=160,
                             on_change=lambda e: self.state.update({"gen_duree": e.control.value}))

        # ── Date de début ──
        today_str = datetime.date.today().strftime(DATE_FMT)
        date_field = mk_entry(
            label="Date de début (JJ/MM/AAAA)", hint=today_str,
            value=self.state.get("gen_start_str", today_str), width=160,
            on_change=lambda e: self.state.update({"gen_start_str": e.control.value}),
        )

        def _open_cal_gen(e):
            from data.widgets import show_date_picker
            def _on_date(date_str):
                date_field.value = date_str
                self.state.update({"gen_start_str": date_str})
                self._safe_update()
            show_date_picker(self.page, date_field.value, _on_date)

        cal_btn_gen = ft.ElevatedButton(
            content=ft.Text("📅", size=18),
            bgcolor=BG_CARD2, color=TEXT, tooltip="Choisir une date",
            on_click=_open_cal_gen,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8),
                                 padding=ft.Padding.all(0)),
            width=44, height=44,
        )

        # ── Jours actifs + muscle par jour ──
        # state: gen_days = {0: {"active": True, "muscle": "Pecs"}, ...}
        if "gen_days" not in self.state:
            self.state["gen_days"] = {
                i: {"active": i < 5, "muscle": "Full body"}
                for i in range(7)
            }

        day_rows = []
        for i, day_lbl in enumerate(DAYS_LABELS):
            day_state = self.state["gen_days"][i]
            is_weekend = i >= 5

            muscle_dd = mk_dropdown(
                "", GROUPES,
                value=day_state.get("muscle", "Full body"),
                width=150,
                on_change=lambda e, idx=i: self.state["gen_days"][idx].update({"muscle": e.control.value}),
            )
            muscle_dd.visible = day_state["active"]
            muscle_ref = ft.Ref[type(muscle_dd)]()

            def _make_cb_change(idx, dd_ctrl):
                def _on_change(e):
                    self.state["gen_days"][idx]["active"] = e.control.value
                    dd_ctrl.visible = e.control.value
                    try: e.page.update()
                    except Exception: pass
                return _on_change

            cb = ft.Checkbox(
                label=day_lbl,
                value=day_state["active"],
                fill_color={ft.ControlState.SELECTED: ACCENT if not is_weekend else WARNING},
                label_style=ft.TextStyle(
                    color=WARNING if is_weekend else TEXT, size=12,
                    weight=ft.FontWeight.BOLD,
                ),
                on_change=_make_cb_change(i, muscle_dd),
            )

            day_rows.append(ft.Row([cb, muscle_dd], spacing=12,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER))

        # ── Programme courant ──
        self._prog_col = ft.Column(spacing=3, scroll=ft.ScrollMode.AUTO)
        self._refresh_prog_display()

        # ── Programmes sauvegardés ──
        self._saved_col = ft.Column(spacing=4)
        self._refresh_saved_programmes()

        # ── Notes ──
        self._note_field = ft.TextField(
            label="Notes de séance", multiline=True, min_lines=2, max_lines=4,
            bgcolor=BG_INPUT, border_color=BORDER, focused_border_color=ACCENT,
            color=TEXT, label_style=ft.TextStyle(color=TEXT_SUB, size=12),
            border_radius=R_INPUT, text_size=13,
            on_change=lambda e: self.state.update({"note": e.control.value}),
        )

        return ft.Container(
            content=ft.Column([

                # ── GÉNÉRATEUR ──────────────────────────────────────────────
                ft.Container(
                    content=ft.Column([
                        mk_title("  ⚡  GÉNÉRATEUR DE PLANNING"),
                        mk_sep(),
                        ft.Container(height=4),

                        # Durée + date début
                        ft.Row([dur_dd,
                                ft.Row([date_field, cal_btn_gen], spacing=0)],
                               spacing=12, wrap=True),
                        ft.Container(height=8),

                        # Catégories techniques
                        ft.Text("Catégories de techniques :", size=11, color=TEXT_SUB),
                        ft.Row(cat_checks, spacing=12, wrap=True),
                        ft.Container(height=8),

                        # Jours actifs
                        ft.Text("Jours actifs + muscle ciblé :", size=11, color=TEXT_SUB),
                        ft.Column(day_rows, spacing=6),
                        ft.Container(height=10),

                        # Boutons
                        ft.Row([
                            mk_btn("⚡ Générer", self._on_gen_month,
                                   color=ACCENT, hover=ACCENT_HOVER, width=140, height=42),
                            mk_btn("💾 Sauvegarder", self._on_save_programme,
                                   color=SUCCESS, hover=SUCCESS_HVR, width=150, height=42),
                            mk_btn("📋 Templates", self._show_templates_modal,
                                   color=ACCENT_DIM, hover=ACCENT_HOVER, width=130, height=42),
                            mk_btn("📄 Export PDF", self._on_export_pdf,
                                   color=GRAY, hover=GRAY_HVR, width=130, height=42),
                        ], spacing=8, wrap=True),
                    ], spacing=6),
                    bgcolor=BG_CARD2, border_radius=10,
                    padding=ft.Padding.all(14),
                    margin=ft.margin.symmetric(horizontal=12),
                ),
                ft.Container(height=8),

                # ── PROGRAMME COURANT ────────────────────────────────────────
                ft.Container(
                    content=ft.Column([
                        mk_title("  📋  PROGRAMME GÉNÉRÉ"),
                        mk_sep(),
                        ft.Container(
                            content=self._prog_col,
                            expand=True,
                            padding=ft.padding.symmetric(horizontal=8, vertical=6),
                        ),
                        ft.Row([
                            mk_btn("+ Technique", self._on_add_to_programme,
                                   color=ACCENT, hover=ACCENT_HOVER, width=130, height=36),
                            mk_btn("🗑 Effacer tout", self._on_clear_programme,
                                   color=DANGER, hover=DANGER_HVR, width=130, height=36),
                        ], spacing=8),
                        ft.Container(height=6),
                    ], spacing=6),
                    bgcolor=BG_CARD2, border_radius=10,
                    padding=ft.Padding.all(14),
                    margin=ft.margin.symmetric(horizontal=12),
                ),
                ft.Container(height=8),

                # ── PROGRAMMES SAUVEGARDÉS ───────────────────────────────────
                ft.Container(
                    content=ft.Column([
                        mk_title("  📂  PROGRAMMES SAUVEGARDÉS"),
                        mk_sep(),
                        ft.Container(content=self._saved_col,
                                     padding=ft.padding.symmetric(horizontal=4, vertical=6)),
                    ], spacing=6),
                    bgcolor=BG_CARD2, border_radius=10,
                    padding=ft.Padding.all(14),
                    margin=ft.margin.symmetric(horizontal=12),
                ),
                ft.Container(height=8),

                # ── NOTES ────────────────────────────────────────────────────
                ft.Container(
                    content=ft.Column([
                        mk_title("  📝  NOTES DE SÉANCE"),
                        mk_sep(),
                        ft.Container(content=self._note_field,
                                     padding=ft.padding.symmetric(horizontal=4, vertical=6)),
                        mk_btn("💾  SAUVEGARDER LA SÉANCE", self._on_save_session,
                               color=SUCCESS, hover=SUCCESS_HVR, width=260, height=44),
                        ft.Container(height=8),
                    ], spacing=6),
                    bgcolor=BG_CARD2, border_radius=10,
                    padding=ft.Padding.all(14),
                    margin=ft.margin.symmetric(horizontal=12),
                ),
                ft.Container(height=14),
            ], spacing=0),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            margin=ft.margin.symmetric(horizontal=12, vertical=6),
        )

    def _refresh_prog_display(self):
        if self._prog_col is None:
            return
        self._prog_col.controls.clear()
        lines = self.state["programme_lines"]
        if not lines:
            self._prog_col.controls.append(
                ft.Text("(programme vide — génère ou ajoute des techniques)",
                        size=12, color=TEXT_MUTED)
            )
            self._safe_update()
            return

        # Parser les lignes en groupes : titre global + semaines
        # Structure : [header_global, sem1_header, sem1_days..., sem2_header, sem2_days..., ...]
        groups = []   # [(week_header_line, week_idx, [day_lines])]
        global_header = None
        current_week  = None

        for line in lines:
            if line.startswith("───"):
                global_header = line
            elif line.startswith("──"):
                if current_week is not None:
                    groups.append(current_week)
                current_week = {"header": line, "days": [], "idx": len(groups)}
            else:
                if current_week is not None:
                    current_week["days"].append(line)
                # lignes orphelines avant la 1ère semaine → ignorées
        if current_week is not None:
            groups.append(current_week)

        # Titre global
        if global_header:
            self._prog_col.controls.append(
                ft.Container(
                    content=ft.Text(global_header, size=12, color=ACCENT,
                                    weight=ft.FontWeight.BOLD),
                    padding=ft.padding.symmetric(horizontal=6, vertical=6),
                )
            )

        # Semaines dépliables
        for grp in groups:
            self._prog_col.controls.append(
                self._build_week_block(grp)
            )

        self._safe_update()

    def _build_week_block(self, grp: dict) -> ft.Container:
        """Une semaine dépliable avec header cliquable pour changer la technique."""
        _state    = {"open": False}
        _icon_ref = ft.Ref[ft.Text]()
        _body_ref = ft.Ref[ft.Container]()

        # Extraire la technique du header : "── Sem.1 (dd/mm→dd/mm) │ Tech [CAT] ──"
        header_line = grp["header"]
        tech_part   = ""
        if "│" in header_line:
            tech_part = header_line.split("│", 1)[1].strip().rstrip("─").strip()

        # Compter repos vs entraînement
        n_entrains = sum(1 for d in grp["days"] if "—  Repos" not in d and d.strip())
        n_repos    = sum(1 for d in grp["days"] if "—  Repos" in d)

        # Header compact
        sem_label = header_line.split("│")[0].replace("──", "").strip()

        def _toggle(e=None):
            _state["open"] = not _state["open"]
            _icon_ref.current.value   = "▼" if _state["open"] else "▶"
            _body_ref.current.visible = _state["open"]
            try: e.page.update()
            except Exception: pass

        # Popup changement de technique
        def _change_tech(e=None, g=grp):
            cats = list(self.state.get("gen_cats", {"SARCOPLASMIQUE","MIXTE","MYOFIBRILLAIRE"}))
            pool = _pool(cats)
            if not pool:
                self._snack("Aucune technique disponible.", WARNING); return

            page = self.page

            def _apply_tech(tech, g=g):
                lines = self.state["programme_lines"]
                old_header = g["header"]
                date_part  = old_header.split("│")[0].rstrip() if "│" in old_header else old_header
                new_header = f"{date_part} │ {tech['nom']} [{tech.get('categorie','')}] ──"
                try:
                    hi = lines.index(old_header)
                    lines[hi] = new_header
                    g["header"] = new_header
                except ValueError:
                    pass

                for di, day_line in enumerate(g["days"]):
                    if "—  Repos" in day_line or not day_line.strip():
                        continue
                    if "  —  " in day_line:
                        prefix  = day_line.split("  —  ")[0]
                        reps    = tech.get("reps","—")
                        charge  = tech.get("charge","—")
                        new_day = f"{prefix}  —  {tech['nom']}  [{reps}] | {charge}"
                        try:
                            day_idx = lines.index(day_line)
                            lines[day_idx] = new_day
                        except ValueError:
                            pass
                        g["days"][di] = new_day

                try:
                    page.bottom_sheet.open = False
                    page.update()
                except Exception:
                    pass
                self._refresh_prog_display()

            tech_items = []
            for t in pool:
                col = {"SARCOPLASMIQUE": ACCENT, "MIXTE": WARNING, "MYOFIBRILLAIRE": PURPLE}.get(
                    t.get("categorie",""), TEXT_SUB)
                tech_items.append(
                    ft.ListTile(
                        title=ft.Text(t["nom"], size=13, color=TEXT),
                        subtitle=ft.Text(f"{t.get('categorie','')}  [{t.get('reps','—')}]",
                                         size=10, color=col),
                        on_click=lambda ev, tech=t: _apply_tech(tech),
                    )
                )

            bs = ft.BottomSheet(
                content=ft.Container(
                    content=ft.Column([
                        ft.Text("Choisir une technique", size=14, color=ACCENT,
                                weight=ft.FontWeight.BOLD),
                        ft.Divider(height=1, color=BORDER),
                        ft.Column(tech_items, scroll=ft.ScrollMode.AUTO, expand=True),
                    ], spacing=8),
                    padding=ft.Padding.all(16),
                    height=420,
                ),
                bgcolor=BG_CARD,
            )
            page.bottom_sheet = bs
            bs.open = True
            if bs not in page.overlay:
                page.overlay.append(bs)
            page.update()

        header = ft.Container(
            content=ft.Row([
                ft.Text("▶", size=10, color=ACCENT, ref=_icon_ref),
                ft.Column([
                    ft.Text(sem_label, size=12, color=ACCENT_GLOW,
                            weight=ft.FontWeight.BOLD),
                    ft.Text(tech_part, size=10, color=TEXT_SUB) if tech_part else ft.Container(),
                ], spacing=1, expand=True),
                ft.Text(f"💪{n_entrains}  😴{n_repos}", size=10, color=TEXT_MUTED),
                ft.Container(
                    content=ft.Text("✏", size=13, color=ACCENT),
                    on_click=_change_tech,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=6,
                    ink=True,
                    tooltip="Changer la technique",
                ),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            on_click=_toggle,
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            margin=ft.margin.only(bottom=2),
            ink=True,
        )

        # Corps — jours de la semaine
        day_items = []
        for day_line in grp["days"]:
            is_repos = "—  Repos" in day_line
            day_items.append(
                ft.Container(
                    content=ft.Text(day_line, size=11,
                                    color=TEXT_MUTED if is_repos else TEXT),
                    bgcolor="transparent" if is_repos else BG_CARD2,
                    border_radius=5,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    margin=ft.margin.only(bottom=1),
                )
            )

        body = ft.Container(
            content=ft.Column(day_items, spacing=0),
            visible=False,
            ref=_body_ref,
            padding=ft.padding.only(left=8, bottom=4),
        )

        return ft.Container(
            content=ft.Column([header, body], spacing=0),
            margin=ft.margin.only(bottom=4),
        )

    def _refresh_saved_programmes(self):
        if not hasattr(self, "_saved_col") or self._saved_col is None:
            return
        self._saved_col.controls.clear()
        try:
            progs = _db.programmes_get_all(self._fake_app())
        except Exception:
            progs = []

        if not progs:
            self._saved_col.controls.append(
                ft.Text("(aucun programme sauvegardé)", size=12, color=TEXT_MUTED)
            )
        else:
            for p in reversed(progs):
                try:
                    dt = datetime.datetime.fromisoformat(p.get("created","")).strftime("%d/%m/%Y %H:%M")
                except Exception:
                    dt = p.get("created","?")[:16]
                n_lines = len(p.get("lines", []))
                self._saved_col.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(p.get("title","?"), size=12, color=TEXT, weight=ft.FontWeight.BOLD),
                                ft.Text(f"{dt}  —  {n_lines} lignes", size=10, color=TEXT_MUTED),
                            ], spacing=2, expand=True),
                            ft.TextButton(content=ft.Text("📂 Charger", color=TEXT_MUTED), on_click=lambda e, prog=p: self._on_load_programme(prog),
                                style=ft.ButtonStyle(color=ACCENT),
                            ),
                            ft.TextButton(content=ft.Text("🗑", color=TEXT_MUTED), on_click=lambda e, prog=p: self._on_del_programme(prog),
                                style=ft.ButtonStyle(color=DANGER),
                            ),
                        ], spacing=4),
                        bgcolor=BG_CARD2, border_radius=8,
                        padding=ft.Padding.all(10),
                        margin=ft.margin.only(bottom=4),
                    )
                )
        self._safe_update()

    # ── Onglet 3 : Historique ────────────────────────────────────────────────

    def _build_historique_tab(self) -> ft.Container:
        self._hist_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO)
        self._refresh_history()

        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        mk_title("  🕐  HISTORIQUE DES SÉANCES"),
                        mk_sep(),
                        ft.Row([
                            mk_btn("📤 Exporter JSON", self._on_export_history,
                                   color=ACCENT_DIM, hover=ACCENT_HOVER, width=150, height=34),
                            mk_btn("📥 Importer JSON", self._on_import_history,
                                   color=ACCENT_DIM, hover=ACCENT_HOVER, width=150, height=34),
                        ], spacing=8, wrap=True),
                    ]),
                    padding=ft.padding.only(left=16, right=16, top=14, bottom=8),
                ),
                ft.Container(content=self._hist_col,
                             padding=ft.padding.symmetric(horizontal=12)),
                ft.Container(height=16),
            ], spacing=0),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            margin=ft.margin.symmetric(horizontal=12, vertical=6),
        )

    def _refresh_history(self):
        if self._hist_col is None:
            return
        self._hist_col.controls.clear()
        try:
            hist = _db.history_get_all(self._fake_app())
        except Exception:
            hist = []

        if not hist:
            self._hist_col.controls.append(
                ft.Text("(Aucun historique)", size=12, color=TEXT_MUTED)
            )
        else:
            for i, entry in enumerate(reversed(hist[-30:])):
                real_idx = len(hist) - 1 - i   # index réel dans la liste complète
                exs = entry.get("exercises", [])
                exs_preview = " | ".join(str(e) for e in exs[:3])
                if len(exs) > 3:
                    exs_preview += f" (+{len(exs)-3})"

                def _on_delete(e, idx=real_idx):
                    self._delete_history_entry(idx)

                self._hist_col.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(entry.get("date","?"), size=12, color=ACCENT,
                                        weight=ft.FontWeight.BOLD, expand=True),
                                ft.Text(entry.get("type","?"), size=11, color=TEXT_SUB),
                            ], spacing=8),
                            *([] if not exs_preview else [
                                ft.Text(exs_preview, size=10, color=TEXT_MUTED),
                            ]),
                            *([] if not entry.get("notes") else [
                                ft.Text(entry["notes"][:80], size=10, color=TEXT_MUTED),
                            ]),
                            ft.Row([
                                mk_btn("🗑 Supprimer", _on_delete,
                                       color="#6b2222", hover=DANGER_HVR, width=110, height=28),
                            ]),
                        ], spacing=3),
                        bgcolor=BG_CARD2, border_radius=8,
                        padding=ft.Padding.all(10),
                        margin=ft.margin.only(bottom=4),
                    )
                )
        self._safe_update()

    # ══════════════════════════════════════════════════════════════════════════
    #  HANDLERS
    # ══════════════════════════════════════════════════════════════════════════

    def _on_date_change(self, val: str):
        try:
            self.state["selected_date"] = datetime.datetime.strptime(val.strip(), DATE_FMT).date()
            self._refresh_plan_display()
        except ValueError:
            pass

    def _on_view_change(self, val: str):
        self.state["view_mode"] = val
        self._refresh_plan_display()

    def _on_gen_cat_toggle(self, cat: str, checked: bool):
        cats = self.state["gen_cats"]
        if checked:
            cats.add(cat)
        else:
            cats.discard(cat)

    def _on_gen_month(self, e):
        cats = list(self.state["gen_cats"])
        if not cats:
            self._snack("Sélectionne au moins une catégorie.", DANGER); return

        # Date de début
        start_str = self.state.get("gen_start_str", "")
        try:
            sd = _parse_date(start_str) if start_str else datetime.date.today()
        except Exception:
            sd = datetime.date.today()
        # Revenir au lundi de la semaine de départ
        sd = sd - datetime.timedelta(days=sd.weekday())

        # Durée → nb de jours
        duree = self.state.get("gen_duree", "1 mois")
        duree_map = {
            "1 semaine": 7, "1 mois": 30, "2 mois": 60,
            "6 mois": 183, "1 an": 365,
        }
        nb_days = duree_map.get(duree, 30)

        # Jours actifs + muscles
        gen_days = self.state.get("gen_days", {i: {"active": i < 5, "muscle": "Full body"} for i in range(7)})

        # Pool de techniques
        pool = _pool(cats)
        if not pool:
            self._snack("Aucune technique disponible.", DANGER); return

        # Générer les semaines sur la durée
        all_days = [sd + datetime.timedelta(days=i) for i in range(nb_days)]

        # Découper en semaines
        weeks, cur = [], []
        for d in all_days:
            if d.weekday() == 0 and cur:
                weeks.append(cur); cur = []
            cur.append(d)
        if cur:
            weeks.append(cur)

        # Assigner une technique par semaine (pas de répétition consécutive)
        ids_shuffled = [t["id"] for t in pool]
        random.shuffle(ids_shuffled)
        n_weeks = len(weeks)
        pool_cycle = list(ids_shuffled)
        if len(pool_cycle) < n_weeks:
            extended = []
            while len(extended) < n_weeks:
                src = list(ids_shuffled); random.shuffle(src)
                for tid in src:
                    if not extended or extended[-1] != tid:
                        extended.append(tid)
                    if len(extended) >= n_weeks: break
            pool_cycle = extended

        week_techs, last_id = [], None
        for w_idx in range(n_weeks):
            for attempt in range(len(pool_cycle)):
                tid = pool_cycle[(w_idx + attempt) % len(pool_cycle)]
                if tid != last_id:
                    week_techs.append(tid); last_id = tid; break
            else:
                week_techs.append(pool_cycle[w_idx % len(pool_cycle)])
                last_id = week_techs[-1]

        # Construire les lignes
        lines = [f"─── Planning {duree} — début {sd.strftime('%d/%m/%Y')} ───"]
        for w_idx, week_days in enumerate(weeks):
            tech = tt.find_technique_by_id(week_techs[w_idx]) if w_idx < len(week_techs) else None
            if not tech: continue
            monday, sunday = week_days[0], week_days[-1]
            lines.append(
                f"── Sem.{w_idx+1}  ({monday.strftime('%d/%m')}→{sunday.strftime('%d/%m')}) "
                f"│ {tech['nom']} [{tech.get('categorie','')}] ──"
            )
            for d in week_days:
                wd = d.weekday()
                ds = d.strftime(DATE_FMT)
                day_cfg = gen_days.get(wd, {"active": False, "muscle": ""})
                if not day_cfg.get("active", False):
                    lines.append(f"  {ds} ({DAY_FR[wd]})  —  Repos")
                    continue
                muscle = day_cfg.get("muscle", "Full body")
                reps   = tech.get("reps", "—")
                charge = tech.get("charge", "—")
                line   = f"  {ds} ({DAY_FR[wd]})  [{muscle}]  —  {tech['nom']}  [{reps}] | {charge}"
                lines.append(line)
                # Enregistrer dans le planning
                try:
                    _db.planning_insert(self._fake_app(), ds,
                                        muscle, self.state.get("prog_name", "Standard"),
                                        tech.get("categorie", ""), "", f"{tech['nom']} [{reps}] | {charge} ({tech['id']})")
                except Exception:
                    pass

        self.state["programme_lines"] = lines
        self._refresh_prog_display()
        self._snack(f"✔ Planning {duree} généré — {n_weeks} semaines, {len(pool)} techniques.", SUCCESS)

    def _on_export_pdf(self, e=None):
        """Export PDF du programme d'entraînement."""
        try:
            from data.pdf_utils import export_entrainement_pdf
            path = export_entrainement_pdf(self.app_state, page=self.page)
            if path:
                self._snack(f"✔ PDF généré : {path}", SUCCESS)
        except Exception as ex:
            self._snack(f"Erreur PDF : {ex}", DANGER)

    def _on_save_programme(self, e):
        lines = self.state["programme_lines"]
        if not lines:
            self._snack("Le programme est vide.", DANGER); return
        raw_title = lines[0].strip("─ ").strip()
        title = raw_title if raw_title else "Programme"
        now_iso = datetime.datetime.now().isoformat()
        try:
            progs = _db.programmes_get_all(self._fake_app())
            existing = next((p for p in progs if p.get("title") == title), None)
            if existing:
                # Mise à jour via delete + re-insert (DB simple)
                from data.db import get_user_db_from_app
                con = get_user_db_from_app(self._fake_app())
                con.execute("DELETE FROM programmes WHERE title=?", (title,))
                import json as _json
                con.execute("INSERT INTO programmes (title, created, lines) VALUES (?,?,?)",
                            (title, now_iso, _json.dumps(lines, ensure_ascii=False)))
                con.commit(); con.close()
            else:
                _db.programmes_insert(self._fake_app(), title, now_iso, lines)
            self._refresh_saved_programmes()
            self._snack(f"✔ Programme « {title} » sauvegardé.", SUCCESS)
        except Exception as ex:
            self._snack(f"Erreur : {ex}", DANGER)

    def _on_load_programme(self, prog: dict):
        self.state["programme_lines"] = prog.get("lines", [])
        self._refresh_prog_display()
        self._snack(f"✔ Programme « {prog.get('title','?')} » chargé.", SUCCESS)

    def _on_del_programme(self, prog: dict):
        try:
            from data.db import get_user_db_from_app
            con = get_user_db_from_app(self._fake_app())
            con.execute("DELETE FROM programmes WHERE title=?", (prog.get("title",""),))
            con.commit(); con.close()
            self._refresh_saved_programmes()
            self._snack("✔ Programme supprimé.", SUCCESS)
        except Exception as ex:
            self._snack(f"Erreur : {ex}", DANGER)

    def _on_add_to_plan(self, e=None):
        tech = self.state.get("last_tech")
        if not tech:
            self._snack("Sélectionne une technique dans le catalogue.", WARNING); return
        ds   = self.state["selected_date"].strftime(DATE_FMT)
        line = _fmt_tech(tech)
        grp  = ", ".join(self.state["groupes"])
        try:
            _db.planning_insert(self._fake_app(), ds, grp, self.state["prog_name"], "", "", line)
            _db.history_insert(self._fake_app(), {
                "date":       datetime.datetime.now().strftime(TS_FMT),
                "type":       self.state["prog_name"] or "séance",
                "duration":   "",
                "notes":      "",
                "exercises":  [line],
                "planned_for": ds,
            })
            self._refresh_plan_display()
            self._snack(f"✔ Ajouté pour le {ds}.", SUCCESS)
        except Exception as ex:
            self._snack(f"Erreur : {ex}", DANGER)

    def _on_del_plan_item(self, e=None):
        entry = self.state.get("_selected_plan_entry")
        if not entry:
            self._snack("Sélectionne d'abord une entrée dans le planning.", WARNING); return
        try:
            _db.planning_delete(self._fake_app(),
                                (entry.get("date","")).strip(),
                                entry.get("line","").strip())
            self.state["_selected_plan_entry"] = None
            self._refresh_plan_display()
            self._snack("✔ Entrée supprimée.", SUCCESS)
        except Exception as ex:
            self._snack(f"Erreur : {ex}", DANGER)

    def _on_add_to_programme(self, e=None):
        tech = self.state.get("last_tech")
        if not tech:
            self._snack("Sélectionne une technique dans le catalogue.", WARNING); return
        self.state["programme_lines"].append(_fmt_tech(tech))
        self._refresh_prog_display()

    def _on_clear_programme(self, e=None):
        self.state["programme_lines"] = []
        self._refresh_prog_display()

    def _on_save_session(self, e=None):
        if not self.app_state.get("current_user"):
            self._snack("Aucun profil sélectionné.", DANGER); return
        ds   = self.state["selected_date"].strftime(DATE_FMT)
        grp  = ", ".join(self.state["groupes"])
        prog = self.state["prog_name"]
        note = self.state.get("note", "")
        exs  = list(self.state["programme_lines"])
        try:
            _db.history_insert(self._fake_app(), {
                "date":       datetime.datetime.now().strftime(TS_FMT),
                "type":       prog or "général",
                "duration":   "",
                "notes":      note,
                "exercises":  exs,
                "planned_for": ds,
            })
            self._snack(f"✔ Séance du {ds} sauvegardée.", SUCCESS)
            if self._hist_col is not None:
                self._refresh_history()
        except Exception as ex:
            self._snack(f"Erreur : {ex}", DANGER)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _delete_history_entry(self, idx: int):
        """Supprime une entrée de l'historique par index — port de _hist_del."""
        try:
            hist = _db.history_get_all(self._fake_app())
            if 0 <= idx < len(hist):
                hist.pop(idx)
                _db.history_save_all(self._fake_app(), hist)
                self._refresh_history()
                self._snack("✔ Entrée supprimée.", SUCCESS)
        except Exception as ex:
            self._snack(f"Erreur : {ex}", DANGER)

    def _on_export_history(self, e=None):
        """Export historique JSON — affiche le chemin dans un snack (mobile-friendly)."""
        try:
            hist = _db.history_get_all(self._fake_app())
            if not hist:
                self._snack("Aucun historique à exporter.", WARNING); return
            import os
            user = self.app_state.get("current_user", "default")
            out_dir = utils.USERS_DIR
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, user, "historique_seances.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(hist, f, ensure_ascii=False, indent=2)
            self._snack(f"✔ Exporté : {path}", SUCCESS)
        except Exception as ex:
            self._snack(f"Erreur export : {ex}", DANGER)

    def _on_import_history(self, e=None):
        """Import historique JSON depuis le dossier utilisateur."""
        try:
            import os
            user = self.app_state.get("current_user", "default")
            path = os.path.join(utils.USERS_DIR, user, "historique_seances.json")
            if not os.path.exists(path):
                self._snack(f"Fichier introuvable : {path}", WARNING); return
            with open(path, "r", encoding="utf-8") as f:
                imp = json.load(f)
            hist = _db.history_get_all(self._fake_app())
            hist.extend(imp if isinstance(imp, list) else [imp])
            _db.history_save_all(self._fake_app(), hist)
            self._refresh_history()
            self._snack(f"✔ {len(imp)} entrées importées.", SUCCESS)
        except Exception as ex:
            self._snack(f"Erreur import : {ex}", DANGER)

    def _show_templates_modal(self, e=None):
        """Modal sélection template programme — port de _load_template."""
        def _apply(name):
            dlg.open = False
            self.page.update()
            lines = []
            if name in ("Sarco", "Myofi"):
                try:
                    tmpl = tt.build_program_template(name, weeks=4)
                    for w in tmpl["weeks"]:
                        lines.append(f"─── Semaine {w['week']} ───")
                        for s in w["sessions"]:
                            lines.append(f"  Séance {s['session']}")
                            for ex in s["exercises"]:
                                tech = tt.find_technique_by_id(ex["id"])
                                if tech:
                                    lines.append(
                                        f"    {tech['nom']} [{tech['reps']}] | {tech['charge']} ({tech['id']})"
                                    )
                except Exception:
                    lines = [f"Template {name}"]
            else:
                lines = [
                    "Standard — Jour A : Pecs/Dos 4×8",
                    "Standard — Jour B : Jambes 4×8",
                    "Standard — Jour C : Épaules/Bras 4×8",
                ]
            self.state["programme_lines"] = lines
            self._refresh_prog_display()
            self._snack(f"✔ Template « {name} » chargé.", SUCCESS)

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("📋  Choisir un template", color=ACCENT, size=14,
                          weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    mk_btn("🔵 Sarcoplasmique (4 semaines)", lambda e: _apply("Sarco"),
                           color=ACCENT, hover=ACCENT_HOVER, width=280, height=44),
                    mk_btn("🟢 Myofibrillaire (4 semaines)", lambda e: _apply("Myofi"),
                           color=SUCCESS, hover=SUCCESS_HVR, width=280, height=44),
                    mk_btn("⚪ Standard 3 jours A/B/C",      lambda e: _apply("Standard"),
                           color=GRAY,    hover=GRAY_HVR,    width=280, height=44),
                ], spacing=10),
                padding=ft.Padding.all(16),
                bgcolor=BG_CARD,
            ),
            actions=[
                ft.TextButton(content=ft.Text("Annuler", color=TEXT_MUTED), on_click=lambda e: self._close_dlg(dlg)),
            ],
            bgcolor=BG_CARD,
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def _close_dlg(self, dlg):
        dlg.open = False
        try:
            self.page.overlay.remove(dlg)
        except Exception:
            pass
        self.page.update()

    def _fake_app(self):
        class _F:
            def __init__(self, cu): self.current_user = cu
        return _F(self.app_state.get("current_user", ""))

    def _snack(self, msg: str, color: str = SUCCESS):
        from ui.snackbar import snack, _LEVEL_COLORS
        _col_to_level = {v: k for k, v in _LEVEL_COLORS.items()}
        level = _col_to_level.get(color, "success")
        snack(self.page, msg, level)

    def _safe_update(self):
        from ui.page_utils import safe_update
        safe_update(self.page)

    def _load_custom_techs_at_startup(self):
        """Charge les techniques custom en mémoire au démarrage."""
        try:
            customs = self._load_custom_techs()
            for c in customs:
                existing = next((i for i, t in enumerate(tt.TECHNIQUES) if t.get("id") == c.get("id")), None)
                if existing is not None:
                    tt.TECHNIQUES[existing] = c
                else:
                    tt.TECHNIQUES.append(c)
        except Exception:
            pass

    def _load_last_programme(self):
        """Charge le dernier programme sauvegardé au démarrage."""
        self._load_custom_techs_at_startup()
        try:
            progs = _db.programmes_get_all(self._fake_app())
            if progs:
                last = progs[-1]
                self.state["programme_lines"] = last.get("lines", [])
                self._refresh_prog_display()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE PUBLIC
# ══════════════════════════════════════════════════════════════════════════════

def build_entrainement_screen(page: ft.Page, app_state: dict) -> ft.Column:
    """Point d'entrée principal — appelé depuis main.py."""
    view = EntrainementView(page, app_state)
    return view.get_view()
