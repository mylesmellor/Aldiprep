from typing import Tuple, List, Dict, Any
import math

def _approx_equal(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol * b

def validate_plan_json(plan: Dict[str, Any], budget: float, protein_target: float, kcal_target: float, keto_strict: bool) -> Tuple[bool, List[str]]:
    problems = []
    ok = True

    # Required keys
    required = ["shopping_list", "total_weekly_cost_gbp", "meal_plan", "macros_table", "batch_cooking_guide", "flavour_rotation", "optional_snacks"]
    for k in required:
        if k not in plan:
            ok = False
            problems.append(f"Missing key: {k}")

    # Budget check
    try:
        total = float(plan.get("total_weekly_cost_gbp", 1e9))
        if total > budget:
            ok = False
            problems.append(f"Budget exceeded: £{total:.2f} > £{budget:.2f}")
    except Exception:
        ok = False
        problems.append("total_weekly_cost_gbp is not a number")

    # Macros checks
    macros = plan.get("macros_table", [])
    if isinstance(macros, list) and macros:
        for row in macros:
            try:
                p = float(row.get("protein_g", -1))
                c = float(row.get("net_carbs_g", -1))
                k = float(row.get("kcal", -1))
                if not _approx_equal(p, protein_target, 0.05):
                    problems.append(f"Protein off target on {row.get('day','?')}: {p} g vs target {protein_target} g (±5%)")
                    ok = False
                if not _approx_equal(k, kcal_target, 0.05):
                    problems.append(f"Calories off target on {row.get('day','?')}: {k} kcal vs target {kcal_target} kcal (±5%)")
                    ok = False
                if keto_strict and not (20 <= c <= 30):
                    problems.append(f"Net carbs outside 20–30 g on {row.get('day','?')}: {c} g")
                    ok = False
            except Exception:
                ok = False
                problems.append("Invalid macros row encountered.")
    else:
        ok = False
        problems.append("macros_table missing or empty.")

    return ok, problems

def render_plan_markdown(plan: Dict[str, Any]) -> str:
    def fmt_money(x):
        try:
            return f"£{float(x):.2f}"
        except Exception:
            return str(x)

    lines = []
    lines.append("# 7‑Day Keto Meal Plan (Aldi UK)")
    lines.append("")
    lines.append(f"**Total weekly cost:** {fmt_money(plan.get('total_weekly_cost_gbp', ''))}")
    lines.append("")

    # Shopping list
    lines.append("## Shopping List")
    sl = plan.get("shopping_list", [])
    if sl:
        lines.append("| Product | Pack size | Unit price | Qty | Line total |")
        lines.append("|---|---:|---:|---:|---:|")
        for item in sl:
            lines.append(f"| {item.get('name','')} | {item.get('pack_size','')} | {fmt_money(item.get('unit_price_gbp',''))} | {item.get('quantity','')} | {fmt_money(item.get('line_total_gbp',''))} |")
    lines.append("")

    # Meal plan
    lines.append("## Meal Plan")
    for row in plan.get("meal_plan", []):
        lines.append(f"**{row.get('day','')}**  ")
        lines.append(f"- Meal 1: {row.get('meal_1','')}")
        lines.append(f"- Meal 2: {row.get('meal_2','')}")
        lines.append("")

    # Macros
    lines.append("## Macros")
    lines.append("| Day | Protein (g) | Net Carbs (g) | Fat (g) | kcal |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in plan.get("macros_table", []):
        lines.append(f"| {row.get('day','')} | {row.get('protein_g','')} | {row.get('net_carbs_g','')} | {row.get('fat_g','')} | {row.get('kcal','')} |")
    lines.append("")

    # Batch cooking guide
    lines.append("## Batch Cooking Guide")
    lines.append(plan.get("batch_cooking_guide", ""))
    lines.append("")

    # Flavour rotation
    lines.append("## Flavour Rotation")
    for s in plan.get("flavour_rotation", []):
        lines.append(f"- {s}")
    lines.append("")

    # Optional snacks
    if plan.get("optional_snacks"):
        lines.append("## Optional Snacks")
        lines.append("| Item | Serving | Protein (g) | Net Carbs (g) | Fat (g) | kcal | Price |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for s in plan["optional_snacks"]:
            lines.append(f"| {s.get('name','')} | {s.get('serving_desc','')} | {s.get('protein_g','')} | {s.get('net_carbs_g','')} | {s.get('fat_g','')} | {s.get('kcal','')} | £{s.get('price_gbp','')} |")
        lines.append("")
    return "\n".join(lines)

def price_hint_table(df):
    # Rename for nicer display if expected columns exist
    cols = {c.lower(): c for c in df.columns}
    return df
