# 🥑 Keto Aldi Meal Planner (Streamlit)

A tiny Streamlit app that turns your prompt into a working planner:
- Collects your goals & preferences
- Optionally takes a CSV of Aldi UK prices
- Calls OpenAI to generate a **strict keto**, **high‑protein** 7‑day plan
- Validates budget/macros and renders a clean report you can download as JSON

## Quick start

1) **Install dependencies**
```bash
python -m venv .venv && source .venv/bin/activate   # (on Windows: .venv\Scripts\activate)
pip install -r requirements.txt
```

2) **Set your API key**
```bash
# macOS/Linux
export OPENAI_API_KEY=sk-...

# Windows PowerShell
setx OPENAI_API_KEY "sk-..."
$env:OPENAI_API_KEY="sk-..."
```

3) **Run the app**
```bash
streamlit run app.py
```

4) **(Optional) Price CSV**
Upload a CSV with headers: `name,pack_size,price_gbp`. Example is included as `sample_prices.csv`.

## Notes

- The app asks the model to **return JSON only**, then validates:
  - Budget ≤ your limit
  - Protein & calories within ±5% of your targets
  - 20–30 g net carbs/day if strict keto is on
- You can change the model in the sidebar. Defaults to `gpt-4o-mini`.
- For best pricing, refresh your CSV weekly from Aldi online listings.
