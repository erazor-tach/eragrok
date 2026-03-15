# data/profil.py — THRESHOLD · Module Profil (Flet)
# ─────────────────────────────────────────────────────────────────────────────
# Port de show_user_selection_screen() / _create_or_modify() / on_delete_profile()
# depuis eragrok/eragrok.py vers Flet.
# Gère : sélection profil, création, édition, suppression, fiche profil actif.
# ─────────────────────────────────────────────────────────────────────────────
from __future__ import annotations
import flet as ft

from ui.theme import (
    ACCENT, ACCENT_DIM, ACCENT_HOVER,
    BG_CARD, BG_CARD2, BG_INPUT, BG_ROOT,
    BORDER, DANGER, DANGER_HVR,
    GRAY, GRAY_HVR, SUCCESS, SUCCESS_HVR,
    TEXT, TEXT_MUTED, TEXT_SUB, WARNING,
    R_CARD, R_INPUT,
    mk_btn, mk_card, mk_dropdown, mk_entry,
    mk_sep, mk_title,
)
from data import utils


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTES
# ══════════════════════════════════════════════════════════════════════════════

_JOURS  = [str(j).zfill(2) for j in range(1, 32)]
_MOIS   = [
    "01","02","03","04","05","06",
    "07","08","09","10","11","12",
]
_MOIS_LABELS = [
    "01 Janvier","02 Février","03 Mars","04 Avril","05 Mai","06 Juin",
    "07 Juillet","08 Août","09 Septembre","10 Octobre","11 Novembre","12 Décembre",
]
_ANNEES = [str(y) for y in range(2025, 1899, -1)]

_OBJECTIFS = ["Gain de masse", "Maintien", "Perte de poids"]


# ══════════════════════════════════════════════════════════════════════════════
#  CLASSE PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════

class ProfilView:
    """
    Écran Profil complet :
    - Sélection / Ouvrir / Modifier / Supprimer profil existant
    - Formulaire Créer / Modifier
    - Fiche profil actif (si déjà connecté)
    """

    def __init__(self, page: ft.Page, app_state: dict, on_open_profile):
        self.page            = page
        self.app_state       = app_state
        self.on_open_profile = on_open_profile   # callback(info: dict) appelé à l'ouverture

        # État formulaire
        self._editing_user: str | None = None

        # Widgets gardés en référence pour mutation
        self._user_dd: ft.Dropdown | None  = None
        self._form_title_text: ft.Text | None = None
        self._save_btn: ft.ElevatedButton | None = None
        self._save_btn_text: ft.Text | None = None
        self._sel_card_col: ft.Column | None = None
        self._active_card_col: ft.Column | None = None

        # Champs formulaire
        self._name_f   = mk_entry(label="Nom / Prénom", hint="Ex : Rudy Martin", width=300)
        self._taille_f = mk_entry(label="Taille (cm)",  hint="176",  width=140,
                                  on_change=lambda e: self._validate_field_num(
                                      e.control, 100, 250, "cm"))
        self._poids_f  = mk_entry(label="Poids (kg)",   hint="87",   width=140,
                                  on_change=lambda e: self._validate_field_num(
                                      e.control, 30, 400, "kg"))
        self._dob_j    = mk_dropdown("Jour",  _JOURS,        value="01", width=110)
        self._dob_m    = mk_dropdown("Mois",  _MOIS_LABELS,  value="01 Janvier", width=190)
        self._dob_a    = mk_dropdown("Année", _ANNEES,       value="1990", width=110)
        self._sexe_dd  = mk_dropdown("Sexe",       ["Homme", "Femme"],        value="Homme",        width=140)
        self._adj_dd   = mk_dropdown("Approche calorique", list(utils.ADJUSTMENTS.keys()),
                                     value="Maintien (0%)", width=300)


    # ── Vue principale ────────────────────────────────────────────────────────

    def get_view(self) -> ft.Column:
        utils.ensure_users_dir()
        return ft.Column([
            self._build_hero(),
            self._build_active_card(),
            self._build_selection_card(),
            self._build_form_card(),
            ft.Container(height=24),
        ], spacing=12, scroll=ft.ScrollMode.AUTO)

    # ── Hero ──────────────────────────────────────────────────────────────────

    def _build_hero(self) -> ft.Container:
        from ui.logo import logo_image
        return ft.Container(
            content=ft.Column([
                logo_image(80),
                ft.Text("THRESHOLD", size=28, color=ACCENT,
                        weight=ft.FontWeight.BOLD),
                ft.Text("COACH BODYBUILDING", size=11, color=TEXT_MUTED),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
            alignment=ft.Alignment(0, 0),
            padding=ft.padding.only(top=32, bottom=8),
        )

    # ── Fiche profil actif ────────────────────────────────────────────────────

    def _build_active_card(self) -> ft.Container:
        self._active_card_col = ft.Column(spacing=4)
        self._refresh_active_card()
        return ft.Container(
            content=self._active_card_col,
            padding=ft.padding.symmetric(horizontal=16),
        )

    def _refresh_active_card(self):
        if self._active_card_col is None:
            return
        self._active_card_col.controls.clear()
        info = self.app_state.get("user_info")
        if not info:
            return

        # Calculs IMC
        poids   = info.get("poids")
        taille  = info.get("taille")
        imc_val = None
        imc_cat = "—"
        imc_col = TEXT_MUTED
        if poids and taille:
            try:
                imc_raw, cat_tuple = utils.calculer_imc(poids, taille)
                if imc_raw:
                    imc_val = round(imc_raw, 1)
                    if cat_tuple:
                        imc_cat = cat_tuple[0]
                        imc_col = _imc_color(imc_raw)
            except Exception:
                pass

        age = info.get("age", "?")
        dob = info.get("date_naissance", "")

        rows = [
            ("👤 Nom",         info.get("name", "—")),
            ("⚧ Sexe",         info.get("sexe", "—")),
            ("🎂 Âge",         f"{age} ans" + (f"  ({dob})" if dob else "")),
            ("📏 Taille",       f"{taille} cm" if taille else "—"),
            ("⚖️ Poids",        f"{poids} kg" if poids else "—"),
            ("📊 IMC",          f"{imc_val}  —  {imc_cat}" if imc_val else "—"),
            ("🎯 Objectif",     info.get("objectif", "—")),
            ("🔧 Ajustement",   info.get("ajustement", "—")),
        ]

        name_val   = info.get("name", "—")
        taille_val = f"{taille} cm" if taille else "—"
        poids_val  = f"{poids} kg" if poids else "—"
        imc_str    = f"{imc_val} — {imc_cat}" if imc_val else "—"
        obj_val    = info.get("objectif", "—")

        def _col(label, value, color=TEXT):
            return ft.Column([
                ft.Text(label, size=12, color=TEXT_MUTED),
                ft.Text(value, size=15, color=color, weight=ft.FontWeight.BOLD),
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        self._active_card_col.controls.append(
            ft.Container(
                content=ft.Column([
                    mk_title("  👤  PROFIL ACTIF"),
                    mk_sep(),
                    ft.Container(height=6),
                    ft.Row([
                        _col("👤 Nom",      name_val),
                        ft.VerticalDivider(width=1, color=BORDER),
                        _col("📏 Taille",   taille_val),
                        ft.VerticalDivider(width=1, color=BORDER),
                        _col("⚖️ Poids",    poids_val),
                        ft.VerticalDivider(width=1, color=BORDER),
                        _col("📊 IMC",      imc_str, imc_col),
                        ft.VerticalDivider(width=1, color=BORDER),
                        _col("🎯 Objectif", obj_val),
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Container(height=4),
                ], spacing=4),
                bgcolor=BG_CARD, border_radius=R_CARD,
                border=ft.border.all(1, BORDER),
                padding=ft.Padding.all(16),
            )
        )

    # ── Sélection profil existant ─────────────────────────────────────────────

    def _build_selection_card(self) -> ft.Container:
        self._sel_card_col = ft.Column(spacing=8)
        self._refresh_selection_card()
        return ft.Container(
            content=self._sel_card_col,
            padding=ft.padding.symmetric(horizontal=16),
        )

    def _refresh_selection_card(self):
        if self._sel_card_col is None:
            return
        self._sel_card_col.controls.clear()
        users = utils.list_users()

        inner_controls = [
            mk_title("  SÉLECTIONNER UN PROFIL"),
            mk_sep(),
            ft.Container(height=8),
        ]

        if not users:
            inner_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("👋  Bienvenue sur THRESHOLD !",
                                size=16, color=ACCENT, weight=ft.FontWeight.BOLD),
                        ft.Container(height=6),
                        ft.Text("Aucun profil trouvé. Crée ton premier profil"
                                " en remplissant le formulaire ci-dessous.",
                                size=13, color=TEXT),
                        ft.Container(height=8),
                        ft.Row([
                            ft.Text("↓", size=22, color=ACCENT, weight=ft.FontWeight.BOLD),
                            ft.Text("Remplis le formulaire juste en dessous",
                                    size=12, color=TEXT_MUTED),
                        ], spacing=8),
                    ], spacing=4),
                    bgcolor=ACCENT_DIM,
                    border_radius=10,
                    padding=ft.Padding.all(16),
                    border=ft.border.all(1, ACCENT),
                )
            )
        else:
            self._user_dd = mk_dropdown(
                "Choisir un profil", users,
                value=users[0] if users else "",
                width=300,
            )
            inner_controls.append(self._user_dd)
            inner_controls.append(ft.Container(height=8))
            inner_controls.append(
                ft.Row([
                    mk_btn("▶  OUVRIR",    self._on_open,   color=ACCENT,  hover=ACCENT_HOVER, width=130, height=44),
                    mk_btn("✎  Modifier",  self._on_edit,   color=GRAY,    hover=GRAY_HVR,     width=120, height=44),
                    mk_btn("✕  Supprimer", self._on_delete, color="#6b2222", hover=DANGER_HVR,  width=120, height=44),
                ], spacing=8, wrap=True)
            )

        self._sel_card_col.controls.append(
            ft.Container(
                content=ft.Column(inner_controls, spacing=6),
                bgcolor=BG_CARD, border_radius=R_CARD,
                border=ft.border.all(1, BORDER),
                padding=ft.Padding.all(16),
            )
        )

    # ── Formulaire créer / modifier ───────────────────────────────────────────

    def _build_form_card(self) -> ft.Container:
        self._form_title_text = ft.Text(
            "CRÉER UN NOUVEAU PROFIL",
            size=14, color=ACCENT, weight=ft.FontWeight.BOLD,
        )
        self._save_btn_text = ft.Text("＋  CRÉER CE PROFIL", size=13,
                                        weight=ft.FontWeight.BOLD, color=TEXT)
        self._save_btn = ft.ElevatedButton(
            content=self._save_btn_text,
            on_click=self._on_save,
            bgcolor=SUCCESS,
            width=220, height=44,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=8),
                overlay_color=SUCCESS_HVR,
            ),
        )

        # Branché ici car self._save_btn doit exister avant l'appel
        def _on_field_change(e=None):
            self._update_form_mode(dirty=True)
            try: self.page.update()
            except Exception: pass

        for _w in [self._name_f, self._taille_f, self._poids_f]:
            _w.on_change = _on_field_change
        for _w in [self._dob_j, self._dob_m, self._dob_a,
                   self._sexe_dd, self._adj_dd]:
            _w.on_select = _on_field_change

        return ft.Container(
            content=ft.Column([
                self._form_title_text,
                mk_sep(),
                ft.Container(height=8),
                # Nom
                self._name_f,
                # DOB
                ft.Column([
                    ft.Text("Date de naissance", size=11, color=TEXT_SUB),
                    ft.Row([self._dob_j, self._dob_m, self._dob_a], spacing=6, wrap=True),
                ], spacing=4),
                # Taille / Poids / Sexe
                ft.Row([self._taille_f, self._poids_f], spacing=10, wrap=True),
                self._sexe_dd,
                # Ajustement
                self._adj_dd,
                ft.Container(height=8),
                ft.Row([
                    self._save_btn,
                    mk_btn("↺  Réinitialiser", self._on_reset,
                           color=GRAY, hover=GRAY_HVR, width=160, height=44),
                ], spacing=10, wrap=True),
            ], spacing=8),
            bgcolor=BG_CARD, border_radius=R_CARD,
            border=ft.border.all(1, BORDER),
            padding=ft.Padding.all(16),
            margin=ft.margin.symmetric(horizontal=16),
        )

    # ── Handlers ─────────────────────────────────────────────────────────────

    def _on_open(self, e=None):
        """Ouvre le profil sélectionné dans le dropdown."""
        if not self._user_dd or not self._user_dd.value:
            self._snack("Sélectionne un profil.", WARNING); return
        info = utils.get_user_info(self._user_dd.value)
        if not info:
            self._snack("Profil introuvable.", DANGER); return
        self.app_state["current_user"] = info.get("folder",
            self._user_dd.value.lower().replace(" ", "_"))
        self.app_state["user_info"] = info
        # Init prices en arrière-plan
        try:
            from data.prices_module import ensure_prices_loaded
            class _F:
                def __init__(s, cu): s.current_user = cu
            ensure_prices_loaded(_F(self.app_state["current_user"]))
        except Exception:
            pass
        self.on_open_profile(info)

    def _on_edit(self, e=None):
        """Charge le profil sélectionné dans le formulaire pour modification."""
        if not self._user_dd or not self._user_dd.value:
            self._snack("Sélectionne un profil.", WARNING); return
        info = utils.get_user_info(self._user_dd.value)
        if not info:
            self._snack("Profil introuvable.", DANGER); return
        self._load_info_into_form(info, editing_name=self._user_dd.value)

    def _load_active_for_edit(self, e=None):
        """Charge le profil actuellement connecté dans le formulaire."""
        info = self.app_state.get("user_info")
        if not info:
            self._snack("Aucun profil actif.", WARNING); return
        self._load_info_into_form(info, editing_name=info.get("name", ""))

    def _load_info_into_form(self, info: dict, editing_name: str):
        """Remplit les champs du formulaire depuis un dict info."""
        self._name_f.value   = info.get("name", "") or ""
        self._taille_f.value = str(info.get("taille", "") or "")
        self._poids_f.value  = str(info.get("poids", "") or "")
        self._sexe_dd.value  = info.get("sexe", "Homme") or "Homme"
        adj = info.get("ajustement", "Maintien (0%)")
        self._adj_dd.value   = adj if adj in utils.ADJUSTMENTS else "Maintien (0%)"

        # Date de naissance
        dob = info.get("date_naissance", "") or ""
        if dob and "/" in dob:
            parts = dob.split("/")
            if len(parts) == 3:
                j, m_num, a = parts
                mois_label = next(
                    (ml for ml in _MOIS_LABELS if ml.startswith(m_num.zfill(2))),
                    "01 Janvier",
                )
                self._dob_j.value = j.zfill(2)
                self._dob_m.value = mois_label
                self._dob_a.value = a

        self._editing_user = editing_name
        self._update_form_mode(dirty=False)
        self._safe_update()

    def _on_delete(self, e=None):
        """Supprime le profil sélectionné avec confirmation."""
        if not self._user_dd or not self._user_dd.value:
            self._snack("Sélectionne un profil.", WARNING); return
        name = self._user_dd.value

        def _confirm(ev):
            dlg.open = False
            self.page.update()
            if utils.delete_user(name):
                # Si c'était le profil actif, le déconnecter
                if self.app_state.get("user_info", {}).get("name") == name:
                    self.app_state["current_user"] = None
                    self.app_state["user_info"]    = None
                self._refresh_selection_card()
                self._refresh_active_card()
                self._safe_update()
                self._snack(f"✔ '{name}' supprimé.", SUCCESS)
            else:
                self._snack("Suppression échouée.", DANGER)

        def _cancel(ev):
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmer la suppression", color=DANGER, size=14),
            content=ft.Text(f"Supprimer '{name}' ?\nIrréversible — toutes les données seront perdues.",
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

    def _on_save(self, e=None):
        """Crée ou modifie un profil selon le mode formulaire."""
        name   = (self._name_f.value or "").strip()
        taille_raw = (self._taille_f.value or "").strip()
        poids_raw  = (self._poids_f.value or "").strip()
        sexe   = self._sexe_dd.value or "Homme"
        adj    = self._adj_dd.value or "Maintien (0%)"
        dob    = self._get_dob_str()
        objectif = utils.ajustement_to_objectif(adj)

        if not name:
            self._snack("Le nom est obligatoire.", DANGER); return
        if not dob or len(dob) != 10:
            self._snack("Sélectionne une date de naissance valide.", DANGER); return

        taille, err = utils.validate_taille(taille_raw)
        if err:
            self._snack(err, DANGER)
            self._taille_f.border_color = DANGER
            self._safe_update(); return
        self._taille_f.border_color = None

        poids, err = utils.validate_poids(poids_raw)
        if err:
            self._snack(err, DANGER)
            self._poids_f.border_color = DANGER
            self._safe_update(); return
        self._poids_f.border_color = None

        taille = str(int(taille)) if taille == int(taille) else str(taille)
        poids  = str(poids)

        if self._editing_user:
            ok = utils.update_user(
                self._editing_user, name, dob, sexe,
                taille, poids, objectif, adj, date_naissance=dob,
            )
            if ok:
                # Mettre à jour app_state si c'était le profil actif
                if self.app_state.get("user_info", {}).get("name") == self._editing_user:
                    new_info = utils.get_user_info(name)
                    if new_info:
                        self.app_state["user_info"]    = new_info
                        self.app_state["current_user"] = new_info.get("folder",
                            name.lower().replace(" ", "_"))
                self._snack(f"✔ Profil '{name}' mis à jour.", SUCCESS)
                self._on_reset()
                self._refresh_selection_card()
                self._refresh_active_card()
                self._safe_update()
            else:
                self._snack("Mise à jour échouée.", DANGER)
        else:
            ok, msg = utils.add_user(name, dob, sexe, taille, poids,
                                     objectif, adj, date_naissance=dob)
            if ok:
                info = utils.get_user_info(name)
                if info:
                    self.app_state["current_user"] = info.get("folder",
                        name.lower().replace(" ", "_"))
                    self.app_state["user_info"] = info
                self._snack(f"✔ Profil '{name}' créé !", SUCCESS)
                # Naviguer vers le dashboard immédiatement — avant tout refresh UI
                if info and self.on_open_profile:
                    self.on_open_profile(info)
                else:
                    self._on_reset()
                    self._refresh_selection_card()
                    self._refresh_active_card()
                    self._safe_update()
            else:
                self._snack(msg, DANGER)

    def _on_reset(self, e=None):
        """Réinitialise le formulaire en mode création."""
        self._name_f.value   = ""
        self._taille_f.value = ""
        self._poids_f.value  = ""
        self._sexe_dd.value  = "Homme"
        self._adj_dd.value   = "Maintien (0%)"
        self._dob_j.value    = "01"
        self._dob_m.value    = "01 Janvier"
        self._dob_a.value    = "2000"
        self._editing_user   = None
        self._update_form_mode(dirty=False)
        self._safe_update()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_dob_str(self) -> str:
        """Retourne la date de naissance au format JJ/MM/AAAA depuis les 3 dropdowns."""
        j = (self._dob_j.value or "01").zfill(2)
        m = (self._dob_m.value or "01 Janvier")[:2].zfill(2)
        a = self._dob_a.value or "2000"
        return f"{j}/{m}/{a}"

    def _update_form_mode(self, dirty: bool = True):
        """Met à jour titre + bouton selon mode création vs édition."""
        if not self._form_title_text or not self._save_btn or not self._save_btn_text:
            return
        if self._editing_user:
            self._form_title_text.value  = f"MODIFIER — {self._editing_user.upper()}"
            self._save_btn_text.value    = "✔  VALIDER LES MODIFICATIONS"
            self._save_btn.bgcolor       = ACCENT
        elif dirty:
            self._form_title_text.value  = "CRÉER UN NOUVEAU PROFIL"
            self._save_btn_text.value    = "✔  VALIDER ET CRÉER"
            self._save_btn.bgcolor       = SUCCESS
        else:
            self._form_title_text.value  = "CRÉER UN NOUVEAU PROFIL"
            self._save_btn_text.value    = "＋  CRÉER CE PROFIL"
            self._save_btn.bgcolor       = SUCCESS

    def _validate_field_num(self, field, min_val: float, max_val: float, unit: str):
        """Colorie la bordure du champ en rouge si valeur invalide, vert si ok."""
        v = utils.parse_num(field.value, float, None, min_val=min_val, max_val=max_val)
        field.border_color = SUCCESS if v is not None else (DANGER if field.value.strip() else None)
        self._safe_update()

    def _snack(self, msg: str, color: str = SUCCESS):
        from ui.snackbar import snack, _LEVEL_COLORS
        # Mappe la couleur hex vers un niveau sémantique
        _col_to_level = {v: k for k, v in _LEVEL_COLORS.items()}
        level = _col_to_level.get(color, "success")
        snack(self.page, msg, level)

    def _safe_update(self):
        from ui.page_utils import safe_update
        safe_update(self.page)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER COULEUR IMC
# ══════════════════════════════════════════════════════════════════════════════

def _imc_color(imc: float) -> str:
    if imc < 16.0:   return "#ff4444"
    if imc < 17.0:   return "#ff8844"
    if imc < 18.5:   return "#ffcc44"
    if imc < 25.0:   return "#44cc44"
    if imc < 30.0:   return "#ffcc44"
    if imc < 35.0:   return "#ff8844"
    if imc < 40.0:   return "#ff6644"
    return "#ff2222"


# ══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE PUBLIC
# ══════════════════════════════════════════════════════════════════════════════

def build_profil_screen(page: ft.Page, app_state: dict,
                        on_open_profile) -> ft.Column:
    """
    Construit et retourne l'écran Profil complet.
    on_open_profile(info: dict) — callback déclenché à l'ouverture d'un profil.
    """
    view = ProfilView(page, app_state, on_open_profile)
    return view.get_view()
