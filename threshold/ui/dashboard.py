# ui/dashboard.py — THRESHOLD · Dashboard principal
# ─────────────────────────────────────────────────────────────────────────────
import flet as ft
from ui.theme import *
from data import db as _db, utils


def build_dashboard(page: ft.Page, app_state: dict) -> ft.Column:
    """Construit la vue dashboard complète."""

    user_info = app_state.get("user_info") or {}
    user_name = user_info.get("name", "—")
    poids     = user_info.get("poids") or 0
    taille    = user_info.get("taille") or 0
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
    hero = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("⚡ THRESHOLD", size=26, color=ACCENT,
                        weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                mk_badge(user_name.upper()),
            ]),
        ], spacing=4),
        bgcolor=BG_CARD,
        padding=ft.padding.symmetric(horizontal=20, vertical=16),
    )
    accent_line = ft.Container(height=3, bgcolor=ACCENT)

    # ── Card Profil & Macros ──────────────────────────────────────────────────
    profil_card = mk_card([
        ft.Container(
            content=ft.Column([
                mk_title("  👤  PROFIL & MACROS DU JOUR"),
                mk_sep(),
                ft.Container(height=8),
                # Métriques
                ft.Row([
                    ft.Column([
                        ft.Text("⚖️  Poids", size=11, color=TEXT_SUB),
                        ft.Text(f"{poids:.0f} kg" if poids else "—",
                                size=14, color=TEXT),
                    ], spacing=2),
                    ft.Column([
                        ft.Text("📏  IMC", size=11, color=TEXT_SUB),
                        ft.Text(imc_str, size=14, color=ACCENT_GLOW),
                    ], spacing=2),
                    ft.Column([
                        ft.Text("🎯  Objectif", size=11, color=TEXT_SUB),
                        ft.Text(adj_label, size=12, color=TEXT),
                    ], spacing=2, expand=True),
                ], spacing=20),
                ft.Container(height=12),
                # Macros
                macro_row(cal, cal, prot, prot, gluc, gluc, lip, lip, fiber=0),
            ], spacing=0),
            padding=ft.padding.all(16),
        ),
    ])

    # ── Card Plan alimentaire ─────────────────────────────────────────────────
    last_plan = app_state.get("last_meal_plan")
    if last_plan and last_plan.get("plan"):
        plan_items = _build_plan_view(last_plan["plan"], cal, prot, gluc, lip)
    else:
        plan_items = [
            ft.Container(
                content=ft.Column([
                    mk_title("  🍽  PLAN ALIMENTAIRE"),
                    mk_sep(),
                    ft.Container(
                        content=ft.Text("Aucun plan généré.\nVa dans Nutrition → Générer.",
                                        size=13, color=TEXT_MUTED,
                                        text_align=ft.TextAlign.CENTER),
                        padding=ft.padding.all(30),
                        alignment=ft.Alignment(0, 0),
                    ),
                ]),
                padding=ft.padding.all(16),
            ),
        ]
    plan_card = mk_card(plan_items)

    # ── Assemblage ────────────────────────────────────────────────────────────
    return ft.Column([
        hero,
        accent_line,
        ft.Container(
            content=ft.Column([
                profil_card,
                plan_card,
            ], spacing=0),
            padding=ft.padding.symmetric(horizontal=12, vertical=16),
        ),
    ], spacing=0, scroll=ft.ScrollMode.AUTO)


def _build_plan_view(plan: list, cal_t: float, prot_t: float,
                     gluc_t: float, lip_t: float) -> list:
    """Construit les widgets pour afficher un plan alimentaire."""
    from data.meal_engine import _fiber_for

    tc = sum(m["tot_cal"] for m in plan)
    tp = sum(m["tot_p"]   for m in plan)
    tg = sum(m["tot_g"]   for m in plan)
    tl = sum(m["tot_l"]   for m in plan)
    tf = sum(_fiber_for(i["food"], i["g"]) for m in plan for i in m["items"])

    controls = [
        ft.Container(
            content=ft.Column([
                mk_title("  🍽  PLAN ALIMENTAIRE"),
                mk_sep(),
                ft.Container(height=8),
                macro_row(tc, cal_t, tp, prot_t, tg, gluc_t, tl, lip_t, tf),
                ft.Container(height=12),
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
                        ft.Text(item["food"], size=13, color=TEXT, expand=True),
                        ft.Text(f"{item['g']:.0f}g", size=12, color=ACCENT),
                        ft.Text(f"{item['p']:.1f}P {item['g_']:.1f}G {item['l']:.1f}L{fib_s}",
                                size=10, color=TEXT_MUTED),
                    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=12, vertical=4),
                )
            )

        icon = SLOT_ICONS.get(meal.get("type", ""), "🍽")
        meal_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"{icon} {meal['name']}", size=13, color=ACCENT_GLOW,
                            weight=ft.FontWeight.BOLD, expand=True),
                    ft.Text(f"{meal['tot_cal']:.0f} kcal", size=12, color=TEXT_SUB),
                ]),
                ft.Divider(height=1, color=BORDER),
                *items_col,
            ], spacing=4),
            bgcolor=BG_CARD2,
            border_radius=10,
            padding=ft.padding.all(12),
            margin=ft.margin.only(left=12, right=12, bottom=8),
        )
        controls.append(meal_card)

    return controls
