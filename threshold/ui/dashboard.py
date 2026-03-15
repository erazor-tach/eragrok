# ui/dashboard.py — THRESHOLD · Dashboard principal
# ─────────────────────────────────────────────────────────────────────────────
import flet as ft
from ui.theme import *
from data import db as _db, utils
from data import injection_schedule as _inj




import datetime as _dt

def _parse_date_flex(s):
    if not s: return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try: return _dt.datetime.strptime(str(s).strip(), fmt).date()
        except: pass
    return None


# ── Rappels d'injections du jour ──────────────────────────────────────────────

def _build_injections_today_card(app_state: dict) -> ft.Container:
    """Widget dashboard — injections/prises du jour + 2 jours suivants."""
    from ui.theme import (
        BG_CARD, BG_CARD2, BG_INPUT, ACCENT, ACCENT_DIM, SUCCESS,
        TEXT, TEXT_MUTED, TEXT_SUB, WARNING, BORDER, R_CARD,
        mk_sep, mk_title,
    )
    import datetime as _dt

    cycle = None
    try:
        cycle = _db.cycle_get_active(app_state)
    except Exception:
        pass

    if not cycle or not cycle.get("debut"):
        return ft.Container(
            content=ft.Text("Aucun cycle actif.", size=12, color=TEXT_MUTED),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )

    # Récupérer les données du cycle
    debut_str   = cycle.get("debut", "")
    n_weeks     = int(cycle.get("longueur_sem", 12) or 12)
    produits_s  = cycle.get("produits_doses", "") or ""

    try:
        start = _dt.datetime.strptime(debut_str.strip(), "%d/%m/%Y").date()
    except Exception:
        return ft.Container(
            content=ft.Text("Date de début invalide.", size=12, color=TEXT_MUTED),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )

    # Parser produits_doses : "Prod: dose | Prod2: dose2"
    products_doses: dict[str, str] = {}
    for part in produits_s.split("|"):
        part = part.strip()
        if ":" in part:
            k, v = part.split(":", 1)
            products_doses[k.strip()] = v.strip()

    if not products_doses:
        return ft.Container(
            content=ft.Text("Aucun produit enregistré dans ce cycle.", size=12, color=TEXT_MUTED),
            padding=ft.padding.symmetric(horizontal=16, vertical=12),
        )

    # days_2x_config stocké en JSON dans la DB
    days_2x: dict[str, tuple[int, int]] = {}
    try:
        import json as _json
        raw = cycle.get("days_2x_config", "{}")
        parsed = _json.loads(raw if isinstance(raw, str) else "{}")
        for k, v in parsed.items():
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                days_2x[k] = (int(v[0]), int(v[1]))
    except Exception:
        pass

    # Si pas de config 2x/sem sauvegardée, appliquer lundi/jeudi par défaut
    # pour tous les produits 2x/sem présents dans le cycle
    for prod in products_doses:
        if _inj.get_freq(prod) == _inj.FREQ_2X_SEM and prod not in days_2x:
            days_2x[prod] = (0, 3)  # lundi / jeudi par défaut

    planning = _inj.get_next_injections(
        products_doses, start, n_weeks, days_2x, days_ahead=3
    )

    today = _dt.date.today()
    JOURS_FR_LONG = ["Lundi","Mardi","Mercredi","Jeudi","Vendredi","Samedi","Dimanche"]
    controls = []

    if not planning:
        controls.append(ft.Container(
            content=ft.Text("Aucune injection aujourd'hui ni dans les 2 prochains jours.",
                            size=12, color=TEXT_MUTED),
            padding=ft.Padding.all(10),
        ))
    else:
        for date, items in sorted(planning.items()):
            is_today  = (date == today)
            day_label = ("Aujourd'hui" if is_today
                         else f"{JOURS_FR_LONG[date.weekday()]} {date.strftime('%d/%m')}")
            day_color = SUCCESS if is_today else ACCENT

            item_rows = [
                ft.Row([
                    ft.Text(f"  💉 {it['product']}", size=11, color=TEXT, expand=True),
                    ft.Text(it['dose'], size=11, color=TEXT_MUTED),
                    ft.Text(f"[{it['freq']}]{it.get('timing_note','')}", size=10,
                            color=WARNING if it.get('timing_note') else TEXT_SUB),
                ], spacing=6)
                for it in items
            ]
            controls.append(ft.Container(
                content=ft.Column([
                    ft.Text(day_label, size=12, color=day_color,
                            weight=ft.FontWeight.BOLD),
                    *item_rows,
                ], spacing=3),
                bgcolor=ACCENT_DIM if is_today else BG_CARD2,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                margin=ft.margin.only(bottom=4),
                border=ft.border.all(1, SUCCESS) if is_today else None,
            ))

    return ft.Container(
        content=ft.Column(controls, spacing=6),
        bgcolor=BG_CARD,
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
    )


def _build_timeline_card(app_state: dict) -> ft.Container:
    """Timeline Cycle → Washout → PCT en Flet (port de render_cycle_timeline ERAGROK)."""
    cycle = None
    try:
        from data import db as _db
        cycle = _db.cycle_get_active(app_state)
    except Exception:
        pass

    controls = [ft.Container(height=6)]

    if not cycle or not cycle.get("debut"):
        controls.append(ft.Container(
            content=ft.Text("Aucun cycle enregistré.", size=12, color=TEXT_MUTED),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        ))
        return mk_card([ft.Container(content=ft.Column(controls, spacing=0),
                                     padding=ft.padding.only(top=16, bottom=12))])

    debut = _parse_date_flex(cycle.get("debut", ""))
    if not debut:
        return mk_card([ft.Container(content=ft.Column(controls, spacing=0),
                                     padding=ft.padding.only(top=16, bottom=12))])

    try:    n_weeks = int(cycle.get("longueur_sem", 12))
    except: n_weeks = 12
    washout_w = 2
    pct_w     = 4
    total_w   = n_weeks + washout_w + pct_w

    today   = _dt.date.today()
    days_in = (today - debut).days
    cur_week = days_in / 7

    # Phases : (label, nb_semaines, bg_color, text_color)
    phases = [
        ("CYCLE",   n_weeks,    "#1a4a1a", "#22c55e"),
        ("WASHOUT", washout_w,  "#2a1a00", "#f59e0b"),
        ("PCT",     pct_w,      "#0a0d2b", "#3b82f6"),
    ]

    bar_segments = []
    week_cursor = 0
    for label, n_w, bg_col, txt_col in phases:
        pct = n_w / total_w
        # Marqueur "aujourd'hui" dans cette phase ?
        is_active = (week_cursor <= cur_week < week_cursor + n_w)
        bar_segments.append(ft.Container(
            content=ft.Text(label, size=9, color=txt_col,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER),
            bgcolor=bg_col,
            expand=round(n_w * 10),  # proportionnel
            height=28,
            alignment=ft.Alignment(0, 0),
            border=ft.border.all(2, txt_col) if is_active else None,
            border_radius=0,
        ))
        week_cursor += n_w

    # Curseur "Aujourd'hui" — label positionné au-dessus
    cur_pct = max(0, min(1, cur_week / total_w))
    today_row = ft.Stack([
        ft.Container(
            content=ft.Row(bar_segments, spacing=0),
            height=28,
        ),
        ft.Container(
            content=ft.Text("▼ Auj.", size=8, color=ACCENT,
                            weight=ft.FontWeight.BOLD),
            left=cur_pct * 100,  # position % simulée
            top=0,
        ) if 0 <= cur_week <= total_w else ft.Container(),
    ])

    # Ligne semaines
    week_labels = ft.Row([
        ft.Text(f"S0", size=8, color=TEXT_MUTED),
        ft.Container(expand=True),
        ft.Text(f"S{n_weeks}", size=8, color=TEXT_MUTED),
        ft.Container(expand=True),
        ft.Text(f"S{n_weeks+washout_w}", size=8, color=TEXT_MUTED),
        ft.Container(expand=True),
        ft.Text(f"S{total_w}", size=8, color=TEXT_MUTED),
    ])

    # Phase actuelle en texte
    if days_in < 0:
        phase_txt, phase_col = "Cycle pas encore démarré", TEXT_MUTED
    elif days_in < n_weeks * 7:
        wk = days_in // 7 + 1
        left = n_weeks * 7 - days_in
        phase_txt, phase_col = f"CYCLE — Semaine {wk}/{n_weeks}  ·  {left}j restants", "#22c55e"
    elif days_in < (n_weeks + washout_w) * 7:
        phase_txt, phase_col = "WASHOUT — Arrêt des produits", "#f59e0b"
    else:
        pct_day = days_in - (n_weeks + washout_w) * 7
        phase_txt, phase_col = f"PCT — Jour {pct_day + 1}", "#3b82f6"

    fin_cycle = debut + _dt.timedelta(weeks=n_weeks)
    pct_start = debut + _dt.timedelta(weeks=n_weeks + washout_w)
    end_date  = debut + _dt.timedelta(weeks=total_w)

    controls += [
        ft.Container(
            content=ft.Column([
                ft.Row(bar_segments, spacing=0),
                ft.Container(height=4),
                week_labels,
            ], spacing=0),
            padding=ft.padding.symmetric(horizontal=16),
            margin=ft.margin.only(bottom=8),
        ),
        ft.Container(
            content=ft.Column([
                ft.Text(f"📍  {phase_txt}", size=11, color=phase_col,
                        weight=ft.FontWeight.BOLD),
                ft.Text(
                    f"Début : {debut:%d/%m/%Y}  ·  Fin cycle : {fin_cycle:%d/%m/%Y}"
                    f"  ·  PCT : {pct_start:%d/%m/%Y}  ·  Fin PCT : {end_date:%d/%m/%Y}",
                    size=10, color=TEXT_MUTED,
                ),
            ], spacing=4),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        ),
    ]

    return mk_card([ft.Container(content=ft.Column(controls, spacing=0),
                                  padding=ft.padding.only(top=16, bottom=8))])


def _build_week_card(app_state: dict, monday: _dt.date, label: str) -> ft.Container:
    """Card semaine (entraînements + nutrition) — port de _render_week_view ERAGROK."""
    from data import db as _db
    sunday = monday + _dt.timedelta(days=6)
    date_range = f"{monday:%d/%m} → {sunday:%d/%m/%Y}"
    DAY_FR = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

    # ── Entraînements ──
    week_dates_set = set()
    d = monday
    while d <= sunday:
        week_dates_set.add(d)
        d += _dt.timedelta(days=1)

    sessions = {}  # date → {groupes, progs, lines}
    try:
        from collections import defaultdict
        import re as _re
        days_map = defaultdict(lambda: {"groupes": set(), "progs": set(), "lines": []})
        for r in _db.planning_get_all(app_state):
            pd = _parse_date_flex(r.get("date", ""))
            if pd and pd in week_dates_set:
                if r.get("groupes"): days_map[pd]["groupes"].add(r["groupes"].strip())
                if r.get("programme"): days_map[pd]["progs"].add(r["programme"].strip())
                line = r.get("line", "").strip()
                if line:
                    clean = _re.sub(r"\s*\([A-Z0-9_]+\)\s*$", "", line).strip()
                    if clean and clean not in days_map[pd]["lines"]:
                        days_map[pd]["lines"].append(clean)
        sessions = dict(days_map)
    except Exception:
        pass

    training_rows = []
    for wd in range(7):
        day_d = monday + _dt.timedelta(days=wd)
        day_str = f"{DAY_FR[wd]} {day_d:%d/%m}"
        is_today = (day_d == _dt.date.today())

        if day_d in sessions:
            info_d = sessions[day_d]
            muscles = " · ".join(sorted(info_d["groupes"]))
            progs   = " · ".join(sorted(info_d["progs"]))
            techs   = info_d["lines"][:2]
            row_content = ft.Column([
                ft.Row([
                    ft.Text(day_str, size=11,
                            color=ACCENT if is_today else ACCENT_GLOW,
                            weight=ft.FontWeight.BOLD, width=55),
                    ft.Text(f"💪 {muscles}" if muscles else progs,
                            size=11, color=TEXT_SUB, expand=True),
                ], spacing=6),
                *([ft.Text(f"  🔧 {t[:55]}{'…' if len(t)>55 else ''}",
                           size=10, color=TEXT_MUTED) for t in techs]),
            ], spacing=2)
        else:
            row_content = ft.Row([
                ft.Text(day_str, size=11,
                        color=ACCENT if is_today else TEXT_MUTED,
                        width=55),
                ft.Text("Repos", size=10, color=TEXT_MUTED),
            ], spacing=6)

        training_rows.append(ft.Container(
            content=row_content,
            bgcolor=BG_CARD2 if day_d in sessions else "transparent",
            border_radius=6,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            margin=ft.margin.only(bottom=2),
            border=ft.border.all(1, ACCENT) if is_today else None,
        ))

    # ── Nutrition moyenne ──
    nut_rows = []
    try:
        for r in _db.nutrition_get_all(app_state):
            pd = _parse_date_flex(r.get("date", ""))
            if pd and pd in week_dates_set:
                nut_rows.append(r)
    except Exception:
        pass

    nut_section = []
    if nut_rows:
        def _avg(key):
            vals = [float(r[key]) for r in nut_rows
                    if r.get(key) and str(r[key]).strip()]
            return sum(vals) / len(vals) if vals else None
        c = _avg("calories"); p = _avg("proteines")
        g = _avg("glucides"); l = _avg("lipides")
        n = len(nut_rows)
        nut_section = [
            ft.Divider(height=1, color=BORDER),
            ft.Container(
                content=ft.Row([
                    ft.Text(f"🍎 Nutrition — {n}j enregistré{'s' if n>1 else ''}",
                            size=11, color=ACCENT, expand=True),
                ]),
                padding=ft.padding.only(top=6, bottom=4),
            ),
            ft.Container(
                content=ft.Row([
                    ft.Text(f"🔥 {c:.0f}" if c else "🔥 —", size=11, color=ACCENT_GLOW),
                    ft.Text(f"🥩 {p:.0f}g" if p else "🥩 —", size=11, color="#4aaa4a"),
                    ft.Text(f"🍚 {g:.0f}g" if g else "🍚 —", size=11, color="#3b82f6"),
                    ft.Text(f"🥑 {l:.0f}g" if l else "🥑 —", size=11, color="#a855f7"),
                ], spacing=12),
                bgcolor=BG_CARD2, border_radius=6,
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
            ),
        ]

    return mk_card([ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Container(expand=True),
                ft.Text(date_range, size=10, color=TEXT_MUTED),
            ]),
            ft.Container(height=4),
            ft.Text("🏋  Entraînement", size=11, color=ACCENT),
            ft.Container(height=4),
            *training_rows,
            *nut_section,
            ft.Container(height=8),
        ], spacing=0),
        padding=ft.padding.symmetric(horizontal=16, vertical=14),
    )])


def _collapsible_card(title: str, content: ft.Control,
                       collapsed: bool = False,
                       builder_fn=None,
                       subtitle_fn=None) -> ft.Container:
    """Card avec header cliquable pour déplier/replier le contenu."""
    icon_ref    = ft.Ref[ft.Text]()
    body_ref    = ft.Ref[ft.Container]()
    sub_ref     = ft.Ref[ft.Text]()
    state       = {"open": not collapsed}

    def _toggle(e=None):
        state["open"] = not state["open"]
        icon_ref.current.value = "▲" if state["open"] else "▼"
        if state["open"] and builder_fn is not None:
            try:
                body_ref.current.content = builder_fn()
            except Exception:
                pass
        body_ref.current.visible = state["open"]
        try: e.page.update()
        except Exception: pass

    # Sous-titre dynamique (ex: résumé cycle)
    sub_row = []
    if subtitle_fn is not None:
        try:
            sub_txt = subtitle_fn()
        except Exception:
            sub_txt = ""
        if sub_txt:
            sub_row = [ft.Text(sub_txt, size=10, color=TEXT_MUTED)]

    header = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text(title, size=13, color=TEXT_ACCENT,
                        weight=ft.FontWeight.BOLD, expand=True),
                ft.Text("▼" if collapsed else "▲",
                        size=12, color=ACCENT, ref=icon_ref),
            ], spacing=8),
            *sub_row,
        ], spacing=2),
        on_click=_toggle,
        bgcolor=BG_CARD,
        padding=ft.padding.symmetric(horizontal=16, vertical=12),
    )

    body = ft.Container(
        content=content,
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

def _cycle_summary(app_state: dict) -> str:
    """Retourne une ligne de résumé du cycle actif pour le header collapsible."""
    try:
        cycle = _db.cycle_get_active(app_state)
        if not cycle:
            return ""
        debut = cycle.get("debut", "")
        fin   = cycle.get("fin_estimee", "—")
        prods = (cycle.get("produits_doses", "") or "")[:35]
        if len(cycle.get("produits_doses", "") or "") > 35:
            prods += "…"
        sem_txt = ""
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                d = _dt.datetime.strptime(debut, fmt).date()
                sem_txt = f"S{((_dt.date.today() - d).days // 7) + 1} · "
                break
            except Exception:
                pass
        return f"{sem_txt}{prods}  ({debut} → {fin})"
    except Exception:
        return ""


def _build_cycle_card(app_state: dict) -> ft.Container:
    """Card Cycle hormonal pour le dashboard — port de _render_cycle_card_inline ERAGROK."""
    try:
        from data import db as _db
        from data.cycle import PRODUCT_INFO
    except Exception:
        PRODUCT_INFO = {}

    cycle = None
    try:
        cycle = _db.cycle_get_active(app_state)
    except Exception:
        pass

    controls = [
        ft.Container(height=6),
    ]

    if not cycle:
        controls.append(ft.Container(
            content=ft.Text("Aucun cycle enregistré.", size=12, color=TEXT_MUTED),
            padding=ft.padding.symmetric(horizontal=16, vertical=8),
        ))
    else:
        # Ligne dates
        controls.append(ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("📅 Début",    size=10, color=TEXT_MUTED),
                    ft.Text(cycle.get("debut", "—"), size=12, color=TEXT),
                ], spacing=2),
                ft.Column([
                    ft.Text("🏁 Fin est.", size=10, color=TEXT_MUTED),
                    ft.Text(cycle.get("fin_estimee", "—"), size=12, color=ACCENT_GLOW),
                ], spacing=2),
                ft.Column([
                    ft.Text("⏱ Durée",    size=10, color=TEXT_MUTED),
                    ft.Text(f"{cycle.get('longueur_sem', '?')} sem.", size=12, color=TEXT_SUB),
                ], spacing=2),
            ], spacing=20),
            bgcolor=BG_CARD2, border_radius=8,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            margin=ft.margin.symmetric(horizontal=16),
        ))

        # Produits
        produits_raw = cycle.get("produits_doses", "") or ""
        entries = [p.strip() for p in produits_raw.split("|") if p.strip()]
        if entries:
            controls.append(ft.Container(
                content=ft.Text("  Produits du stack :", size=11, color=ACCENT),
                padding=ft.padding.only(left=16, top=8, bottom=4),
            ))
            dang_scores = []
            for entry in entries:
                parts     = entry.split(":", 1)
                prod_name = parts[0].strip()
                prod_dose = parts[1].strip() if len(parts) > 1 else ""
                info      = PRODUCT_INFO.get(prod_name, {})
                dang      = info.get("dangerosite", "")
                stars     = dang.count("★")
                dang_scores.append(stars)
                dang_col  = {0:"#555555",1:"#22c55e",2:"#84cc16",
                             3:"#f59e0b",4:"#ef4444",5:"#7f1d1d"}.get(stars, TEXT_SUB)

                row_items = [
                    ft.Text(f"• {prod_name}", size=12, color=TEXT, expand=True),
                ]
                if prod_dose:
                    row_items.append(ft.Container(
                        content=ft.Text(prod_dose, size=10, color=ACCENT_GLOW),
                        bgcolor=BG_ROOT, border_radius=4,
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                    ))

                sub_items = []
                utilite  = info.get("utilite", "")
                demi_vie = info.get("demi_vie", "")
                if utilite:
                    sub_items.append(ft.Text(f"🎯 {utilite}", size=10, color=TEXT_SUB))
                if demi_vie:
                    sub_items.append(ft.Text(f"⏲ {demi_vie}", size=10, color=TEXT_MUTED))
                if dang:
                    sub_items.append(ft.Text(f"⚠ {dang}", size=10, color=dang_col))

                controls.append(ft.Container(
                    content=ft.Column([
                        ft.Row(row_items, spacing=8),
                        *([ft.Row(sub_items, spacing=12, wrap=True)] if sub_items else []),
                    ], spacing=2),
                    bgcolor=BG_CARD2, border_radius=6,
                    padding=ft.padding.symmetric(horizontal=10, vertical=6),
                    margin=ft.margin.only(left=16, right=16, bottom=4),
                ))

            if dang_scores:
                max_d = max(dang_scores)
                risk_txt = {0:"—",1:"✅ Faible",2:"✅ Modéré",
                            3:"⚠️ Élevé",4:"🔴 Très élevé",5:"🔴 Extrême"}.get(max_d,"—")
                risk_col = {0:"#555",1:"#22c55e",2:"#84cc16",
                            3:"#f59e0b",4:"#ef4444",5:"#7f1d1d"}.get(max_d, TEXT_SUB)
                controls.append(ft.Container(
                    content=ft.Row([
                        ft.Text("Risque stack :", size=11, color=TEXT_MUTED),
                        ft.Text(risk_txt, size=12, color=risk_col,
                                weight=ft.FontWeight.BOLD),
                    ], spacing=8),
                    padding=ft.padding.only(left=16, top=6, bottom=8),
                ))

        # Note
        note = cycle.get("note", "")
        if note:
            controls.append(ft.Container(
                content=ft.Text(f"📝 {note[:120]}{'…' if len(note)>120 else ''}",
                                size=11, color=TEXT_SUB),
                bgcolor=BG_CARD2, border_radius=6,
                padding=ft.padding.symmetric(horizontal=12, vertical=6),
                margin=ft.margin.only(left=16, right=16, bottom=4),
            ))

    return mk_card([ft.Container(
        content=ft.Column(controls, spacing=0),
        padding=ft.padding.only(left=0, right=0, top=16, bottom=12),
    )])

def build_dashboard(page: ft.Page, app_state: dict) -> ft.Column:
    """Construit la vue dashboard complète."""

    user_info = app_state.get("user_info") or {}
    user_name = user_info.get("name", "—")
    try:    poids  = float(user_info.get("poids")  or 0)
    except: poids  = 0.0
    try:    taille = float(user_info.get("taille") or 0)
    except: taille = 0.0
    age       = user_info.get("age") or "—"
    sexe      = user_info.get("sexe", "Homme")
    adj_label = user_info.get("ajustement", "Maintien (0%)")
    objectif  = user_info.get("objectif", "Maintien")

    # ── Calculs nutrition ─────────────────────────────────────────────────────
    nut = utils.calculs_nutrition(poids, age, sexe, objectif, taille)
    adj_val = utils.ADJUSTMENTS.get(adj_label, 0.0)

    if nut:
        cal  = nut["tdee"] * (1 + adj_val)
        prot = nut["proteines"]
        obj_l = objectif.lower()
        if "masse" in obj_l:    cp, fp = 0.47, 0.23
        elif "perte" in obj_l:  cp, fp = 0.37, 0.23
        else:                    cp, fp = 0.45, 0.25
        gluc = (cal * cp) / 4
        lip  = (cal * fp) / 9
    else:
        cal, prot, gluc, lip = 2500, 180, 280, 70

    # ── IMC ────────────────────────────────────────────────────────────────────
    imc_val, imc_cat = utils.calculer_imc(poids, taille)
    imc_str = f"{imc_val:.1f} — {imc_cat[0]}" if imc_val else "—"

    # ── Hero header ───────────────────────────────────────────────────────────
    from ui.logo import logo_image
    hero = ft.Container(
        content=ft.Column([
            ft.Row([
                logo_image(36),
                ft.Text("THRESHOLD", size=22, color=ACCENT,
                        weight=ft.FontWeight.BOLD),
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ], spacing=4),
        bgcolor=BG_CARD,
        padding=ft.padding.symmetric(horizontal=20, vertical=14),
    )
    accent_line = ft.Container(height=3, bgcolor=ACCENT)

    # ── Card Profil & Macros ──────────────────────────────────────────────────
    profil_card = mk_card([
        ft.Container(
            content=ft.Column([
                ft.Container(height=8),
                # Ligne : Nom | Taille | Poids | IMC | Objectif
                ft.Row([
                    ft.Column([
                        ft.Text("👤 Nom",    size=12, color=TEXT_MUTED),
                        ft.Text(user_name,   size=15, color=TEXT,
                                weight=ft.FontWeight.BOLD),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(width=1, color=BORDER),
                    ft.Column([
                        ft.Text("📏 Taille", size=12, color=TEXT_MUTED),
                        ft.Text(f"{taille:.0f} cm" if taille else "—",
                                size=15, color=TEXT, weight=ft.FontWeight.BOLD),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(width=1, color=BORDER),
                    ft.Column([
                        ft.Text("⚖️ Poids",  size=12, color=TEXT_MUTED),
                        ft.Text(f"{poids:.0f} kg" if poids else "—",
                                size=15, color=TEXT, weight=ft.FontWeight.BOLD),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(width=1, color=BORDER),
                    ft.Column([
                        ft.Text("📊 IMC",    size=12, color=TEXT_MUTED),
                        ft.Text(imc_str,     size=15, color=ACCENT_GLOW,
                                weight=ft.FontWeight.BOLD),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.VerticalDivider(width=1, color=BORDER),
                    ft.Column([
                        ft.Text("🎯 Objectif", size=12, color=TEXT_MUTED),
                        ft.Text(adj_label,      size=14, color=TEXT,
                                weight=ft.FontWeight.BOLD),
                    ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Container(height=12),
                # Macros
                macro_row(cal, cal, prot, prot, gluc, gluc, lip, lip, fiber=0),
            ], spacing=0),
            padding=ft.Padding.all(16),
        ),
    ])

    # ── Card Plan alimentaire ─────────────────────────────────────────────────
    last_plan = app_state.get("last_meal_plan")
    if not last_plan:
        # Fallback : lecture directe depuis la DB avec normalisation
        try:
            from data import db as _db
            db_plan = _db.meal_plan_get_last(app_state, accepted_only=True)
            if db_plan:
                last_plan = _db.meal_plan_to_dashboard(db_plan)
                if last_plan:
                    app_state["last_meal_plan"] = last_plan
        except Exception as _e:
            import sys
            print(f"[dashboard] fallback meal_plan échoué : {_e}", file=sys.stderr)
    if last_plan and last_plan.get("plan"):
        plan_items = _build_plan_view(last_plan["plan"], cal, prot, gluc, lip)
    else:
        plan_items = [
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Text("Aucun plan généré.\nVa dans Nutrition → Générer.",
                                        size=13, color=TEXT_MUTED,
                                        text_align=ft.TextAlign.CENTER),
                        padding=ft.Padding.all(30),
                        alignment=ft.Alignment(0, 0),
                    ),
                ]),
                padding=ft.Padding.all(16),
            ),
        ]
    plan_card = mk_card(plan_items)

    # ── Card Graphique poids ──────────────────────────────────────────────────
    def _try_weight_chart():
        try:
            from data.weight_chart import build_weight_chart
            return mk_card([ft.Container(
                content=build_weight_chart(page, app_state),
                padding=ft.Padding.all(4),
            )])
        except Exception:
            return None

    weight_card = _try_weight_chart()

    # ── Semaines ──────────────────────────────────────────────────────────────
    today_d    = _dt.date.today()
    monday_cur = today_d - _dt.timedelta(days=today_d.weekday())
    week_cur_card  = _build_week_card(app_state, monday_cur, "SEMAINE EN COURS")
    week_next_card = _build_week_card(app_state, monday_cur + _dt.timedelta(weeks=1), "SEMAINE SUIVANTE")

    # ── Cycle + Timeline — reconstruits à chaque ouverture ───────────────────

    # ── Assemblage — colonne unique fixe (app mobile) ─────────────────────────
    def _strip(card):
        try:    return card.content
        except: return card

    sections = [
        _collapsible_card("  👤  PROFIL & MACROS DU JOUR",
                          _strip(profil_card),              collapsed=False),
        _collapsible_card("  📅  SEMAINE EN COURS",
                          _strip(week_cur_card),            collapsed=True),
        _collapsible_card("  📅  SEMAINE SUIVANTE",
                          _strip(week_next_card),           collapsed=True),
        _collapsible_card("  🍽  PLAN ALIMENTAIRE",
                          _strip(plan_card),                collapsed=True),
        _collapsible_card("  📈  ÉVOLUTION DU POIDS",
                          _strip(weight_card) if weight_card else ft.Container(),
                          collapsed=True),
        _collapsible_card("  💉  CYCLE HORMONAL",
                          ft.Container(), collapsed=True,
                          builder_fn=lambda: _strip(_build_cycle_card(app_state)),
                          subtitle_fn=lambda: _cycle_summary(app_state)),
        _collapsible_card("  🧬  TIMELINE DU CYCLE",
                          ft.Container(), collapsed=True,
                          builder_fn=lambda: _strip(_build_timeline_card(app_state))),
        _collapsible_card("  💊  RAPPELS D'INJECTIONS",
                          ft.Container(), collapsed=False,
                          builder_fn=lambda: _strip(_build_injections_today_card(app_state))),
    ]

    return ft.Column([
        hero,
        accent_line,
        ft.Container(
            content=ft.Column(sections, spacing=0),
            padding=ft.padding.symmetric(horizontal=12, vertical=16),
        ),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)


def _try_macro_pie(cal, prot, gluc, lip):
    """Retourne le widget macro_pie ou None si erreur."""
    try:
        from data.widgets import build_macro_pie
        return build_macro_pie(cal, prot, gluc, lip)
    except Exception:
        return None


def _build_plan_view(plan: list, cal_t: float, prot_t: float,
                     gluc_t: float, lip_t: float) -> list:
    """Construit les widgets pour afficher un plan alimentaire."""
    from data.meal_engine import _fiber_for

    # Clés THRESHOLD: tot_cal/tot_p/tot_g/tot_l
    tc = sum(m.get("tot_cal", m.get("cal", 0)) for m in plan)
    tp = sum(m.get("tot_p",   m.get("prot", 0)) for m in plan)
    tg = sum(m.get("tot_g",   m.get("gluc", 0)) for m in plan)
    tl = sum(m.get("tot_l",   m.get("lip", 0)) for m in plan)
    try:
        tf = sum(_fiber_for(i["food"], i["g"]) for m in plan for i in m.get("items", []))
    except Exception:
        tf = 0

    controls = [
        ft.Container(
            content=ft.Column([
                ft.Container(height=8),
                macro_row(tc, cal_t, tp, prot_t, tg, gluc_t, tl, lip_t, tf),
                ft.Container(height=8),
                *([] if not (pie := _try_macro_pie(tc, tp, tg, tl)) else [pie]),
                ft.Container(height=4),
            ]),
            padding=ft.padding.only(left=16, right=16, top=16),
        ),
    ]

    SLOT_ICONS = {"matin": "🌅", "midi": "☀️", "collation": "🍎",
                  "soir": "🌙", "coucher": "🌛"}

    for meal in plan:
        items_col = []
        for item in meal.get("items", []):
            fib = _fiber_for(item["food"], item["g"])
            fib_s = f"  🌾{fib:.1f}" if fib > 0.1 else ""
            items_col.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=6, height=6, bgcolor=ACCENT_GLOW,
                                     border_radius=3),
                        ft.Text(item.get("food", "?"), size=13, color=TEXT, expand=True),
                        ft.Text(f"{item.get('g',0):.0f}g", size=12, color=ACCENT),
                        ft.Text(f"{item.get('p',0):.1f}P {item.get('g_',0):.1f}G {item.get('l',0):.1f}L{fib_s}",
                                size=10, color=TEXT_MUTED),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                )
            )

        icon = SLOT_ICONS.get(meal.get("type", ""), "🍽")
        meal_name = meal.get("name", meal.get("nom", f"Repas"))
        meal_cal  = meal.get("tot_cal", meal.get("cal", 0))
        meal_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"{icon} {meal_name}", size=13, color=ACCENT_GLOW,
                            weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text(f"{meal_cal:.0f} kcal", size=12, color=TEXT_SUB),
                ]),
                ft.Divider(height=1, color=BORDER),
                *items_col,
            ], spacing=4),
            bgcolor=BG_CARD2,
            border_radius=10,
            padding=ft.Padding.all(12),
            margin=ft.margin.only(left=12, right=12, bottom=8),
        )
        controls.append(meal_card)

    return controls
