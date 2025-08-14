import os
import json
import streamlit as st
from openai import OpenAI
from utils import render_plan_markdown, validate_plan_json, price_hint_table

st.set_page_config(page_title="Keto Aldi Meal Planner", page_icon="🥑", layout="wide")

st.title("🥑 Keto Aldi Meal Planner")
st.caption("Creates a 7‑day strict-keto, high‑protein, batch-cooking plan and Aldi UK shopping list within your budget.")

# Sidebar: API & optional price CSV
with st.sidebar:
    st.header("API & Model")
    api_key = st.text_input("OpenAI API key", type="password", value=os.getenv("OPENAI_API_KEY", ""))
    model = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    st.write("Tip: set OPENAI_API_KEY in your environment for convenience.")
    st.divider()
    st.header("Price data (optional)")
    price_csv = st.file_uploader("Upload Aldi prices CSV (name, pack_size, price_gbp)", type=["csv"])
    st.caption("For highest accuracy, upload a price CSV you refresh weekly.")

st.subheader("Your details")
col1, col2 = st.columns(2)
with col1:
    weight = st.number_input("Weight (kg)", min_value=35.0, max_value=200.0, value=83.0, step=0.5)
    goal = st.selectbox("Goal", ["Fat loss", "Muscle gain", "Recomp"], index=2)
    training = st.text_input("Training routine", value="5 gym sessions + 2 runs/week")
    protein_target = st.number_input("Daily protein target (g)", min_value=60, max_value=300, value=165, step=5)
with col2:
    calorie_target = st.number_input("Daily calorie target (kcal)", min_value=1200, max_value=4000, value=2200, step=50)
    keto_strict = st.checkbox("Strict keto (20–30 g net carbs/day)", value=True)
    budget = st.number_input("Weekly grocery budget (£)", min_value=20, max_value=200, value=60, step=5)
    snacks = st.checkbox("Include optional snacks", value=True)

restrictions = st.text_area("Dietary restrictions/dislikes", value="No sugar or grains. Avoid ultra-processed foods.")
repeat_tol = st.selectbox("Repeat tolerance", ["Low (varied daily)", "Medium (repeat some meals)", "High (happy to repeat often)"], index=1)
cook_pref = st.selectbox("Cooking preference", ["One weekly batch-cook", "One batch + midweek top-up", "Cook fresh most days"], index=0)

if st.button("Generate 7‑day plan", use_container_width=True, disabled=(not api_key)):
    with st.spinner("Generating your plan..."):
        client = OpenAI(api_key=api_key)

        system_prompt = """
You are a specialist nutrition and meal-planning assistant who creates keto-friendly, high-protein, batch-cooking meal plans and shopping lists for UK Aldi customers.

Task
When asked, generate a complete 7-day shopping list and cooking plan based on the user’s provided personal details, dietary goals, and preferences.

Constraints & Requirements
- Keep total weekly grocery cost under the user’s stated budget (default: £60).
- Exactly match the user’s macro targets and calorie goals where provided.
- Strict keto: 20–30 g net carbs/day (unless user specifies otherwise).
- Focus on best £ per gram of protein using Aldi UK products with real pack sizes and current prices (cross-check from latest Aldi UK online listings or an uploaded CSV).
- Plan 2 main meals/day, plus optional snacks if requested.
- All meals must be bulk-prep friendly and easy to store for 7 days with minimal mid-week cooking.
- Use high ingredient reuse to minimise waste but avoid flavour fatigue.
- Minimise ultra-processed foods unless user explicitly requests.
- Use metric weights and UK spelling.

Output Format (JSON only)
Return a single JSON object with these keys:
- shopping_list: [{{name, pack_size, unit_price_gbp, quantity, line_total_gbp}}]
- total_weekly_cost_gbp: number
- meal_plan: [{{day, meal_1, meal_2}}]  # Include exact ingredient weights in the meal text
- macros_table: [{{day, protein_g, net_carbs_g, fat_g, kcal}}]
- batch_cooking_guide: string
- flavour_rotation: [string]
- optional_snacks: [{{name, serving_desc, protein_g, net_carbs_g, fat_g, kcal, price_gbp}}]

Validation rules:
- Keep total_weekly_cost_gbp <= budget.
- Ensure each day's net_carbs_g is within 20–30 g if keto_strict is True.
- Hit protein_target ± 5% and calories ± 5% daily.
- Use realistic Aldi UK pack sizes.
- Prefer best £/g protein options.
- Reuse ingredients sensibly to minimise waste.
"""

        user_context = {
            "weight_kg": weight,
            "goal": goal,
            "training_routine": training,
            "daily_protein_target_g": int(protein_target),
            "daily_calorie_target_kcal": int(calorie_target),
            "keto_strict": keto_strict,
            "dietary_restrictions": restrictions,
            "repeat_tolerance": repeat_tol,
            "cooking_preference": cook_pref,
            "include_snacks": snacks,
            "budget_gbp": float(budget),
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Here are my preferences and goals:\n" + json.dumps(user_context, indent=2)},
        ]

        if price_csv is not None:
            import pandas as pd
            price_df = pd.read_csv(price_csv)
            messages.append({"role": "user", "content": "Here is a CSV-derived list of Aldi price hints (name, pack_size, price_gbp):\n" + price_df.to_json(orient="records")})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        try:
            plan = json.loads(raw)
        except Exception:
            st.error("The model did not return valid JSON. See raw output below:")
            st.code(raw, language="json")
            st.stop()

        ok, problems = validate_plan_json(plan, budget=float(budget), protein_target=float(protein_target), kcal_target=float(calorie_target), keto_strict=bool(keto_strict))
        if not ok:
            with st.expander("Validation issues", expanded=True):
                for p in problems:
                    st.error(p)

        st.success("Plan generated.")
        st.download_button("Download JSON", data=json.dumps(plan, indent=2), file_name="keto_plan.json", mime="application/json", use_container_width=True)

        # Render nice markdown
        md = render_plan_markdown(plan)
        st.markdown(md)

        # Show price table if present
        if "shopping_list" in plan:
            st.subheader("Shopping list (table view)")
            try:
                import pandas as pd
                df = pd.DataFrame(plan["shopping_list"])
                st.dataframe(df, use_container_width=True)
            except Exception:
                pass

        if price_csv is not None:
            st.subheader("Uploaded price hints")
            st.dataframe(price_hint_table(price_df), use_container_width=True)
