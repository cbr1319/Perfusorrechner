import streamlit as st

st.set_page_config(page_title="Perfusor-Rechner 13H3", layout="centered")

# ---- Daten (aus Perfusorstandard 13H3 Stand 09/2019; Konzentrationen nach Hausstandard) ----
# amount_unit: "mg", "µg", "IE"
# dose_unit: one of: "µg/kg/min", "µg/kg/h", "mg/kg/h", "µg/h", "mg/h", "IE/h"
DRUGS = {
    "Noradrenalin (Arterenol)": {
        "amount": 10, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.10, "max": 0.50,
        "note": "Standard meist 10 mg/50 ml NaCl; Ausgabe in γ (=µg/kg/min)."
    },
    "Adrenalin (Suprarenin)": {
        "amount": 10, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.10, "max": 0.50,
        "note": "Standard meist 10 mg/50 ml NaCl; Ausgabe in γ (=µg/kg/min)."
    },
    "Dobutamin (Dobutrex)": {
        "amount": 500, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 3.0, "max": None,
        "note": "250 mg/50 ml ist in manchen Häusern üblich; hier 500 mg/50 ml laut Blatt."
    },
    "Remifentanil (Ultiva) 5 mg/50 ml": {
        "amount": 5, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.05, "max": 0.20,
        "note": "Nie als Bolus; HWZ sehr kurz."
    },
    "Remifentanil (Ultiva) 10 mg/50 ml": {
        "amount": 10, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.05, "max": 0.20,
        "note": "Alternative Konzentration."
    },
    "Propofol": {
        "amount": 1000, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/kg/h", "start": 1.0, "max": 4.0,
        "note": "Wake-up-call beachten."
    },
    "Esketamin (Ketanest S)": {
        "amount": 1250, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/kg/h", "start": 1.0, "max": 3.0,
        "note": "CAVE nicht als Monotherapie (laut Blatt)."
    },
    "Clonidin (Catapresan)": {
        "amount": 1.5, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/h", "start": 30.0, "max": 120.0,
        "note": "Ausgabe in µg/h (gewichtsunabhängig)."
    },
    "Dexmedetomidin (Dexdor)": {
        "amount": 1000, "amount_unit": "µg", "volume_ml": 50,
        "dose_unit": "µg/kg/h", "start": 0.7, "max": 1.4,
        "note": "CAVE AV-Block (laut Blatt)."
    },
    "Midazolam (Dormicum)": {
        "amount": 250, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/h", "start": 100.0, "max": None,
        "note": "Hohe Dosis >300 µg/kg/h (laut Blatt)."
    },
    "Urapidil (Ebrantil)": {
        "amount": 250, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 10.0, "max": 50.0,
        "note": "Ausgabe in mg/h (gewichtsunabhängig)."
    },
    "Heparin": {
        "amount": 10000, "amount_unit": "IE", "volume_ml": 50,
        "dose_unit": "IE/h", "start": 350.0, "max": None,
        "note": "Prophylaxe ca. 300–400 IE/h; therapeutisch nach aPTT (laut Blatt)."
    },
    "Isoprenalin (Isuprel)": {
        "amount": 1, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.01, "max": 0.03,
        "note": "IND z.B. AV-Block/SSS (laut Blatt)."
    },
    "Landiolol (Rapibloc)": {
        "amount": 300, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 2.5, "max": 20.0,
        "note": "Schrittweise Erhöhung alle 10 min (laut Blatt)."
    },
}

# ---- Helper ----
def to_float(x):
    try:
        return float(x)
    except Exception:
        return None

def conc_per_ml(drug: dict):
    """Return concentration per ml in base units: ug/ml for mass drugs, IU/ml for heparin."""
    amt = drug["amount"]
    u = drug["amount_unit"]
    vol = drug["volume_ml"]
    if u == "IE":
        return amt / vol, "IE/ml"
    # mass-based
    if u == "mg":
        ug = amt * 1000.0
    elif u == "µg":
        ug = amt * 1.0
    else:
        raise ValueError("Unsupported unit")
    return ug / vol, "µg/ml"

def dose_from_rate(rate_ml_h: float, weight_kg: float | None, drug: dict):
    conc, conc_unit = conc_per_ml(drug)
    du = drug["dose_unit"]

    if du == "IE/h":
        return conc * rate_ml_h, du

    # mass drugs: conc is in µg/ml
    ug_per_h = conc * rate_ml_h
    ug_per_min = ug_per_h / 60.0

    if du == "µg/h":
        return ug_per_h, du
    if du == "mg/h":
        return ug_per_h / 1000.0, du
    if weight_kg is None or weight_kg <= 0:
        return None, du

    if du == "µg/kg/min":
        return ug_per_min / weight_kg, du
    if du == "µg/kg/h":
        return ug_per_h / weight_kg, du
    if du == "mg/kg/h":
        return (ug_per_h / 1000.0) / weight_kg, du

    return None, du

def rate_from_dose(target: float, weight_kg: float | None, drug: dict):
    conc, _ = conc_per_ml(drug)
    du = drug["dose_unit"]
    if conc <= 0:
        return None

    if du == "IE/h":
        return target / conc

    # mass drugs (conc in µg/ml)
    if du == "µg/h":
        ug_per_h = target
    elif du == "mg/h":
        ug_per_h = target * 1000.0
    else:
        if weight_kg is None or weight_kg <= 0:
            return None
        if du == "µg/kg/min":
            ug_per_h = target * weight_kg * 60.0
        elif du == "µg/kg/h":
            ug_per_h = target * weight_kg
        elif du == "mg/kg/h":
            ug_per_h = target * 1000.0 * weight_kg
        else:
            return None

    return ug_per_h / conc

def fmt(x):
    if x is None:
        return "—"
    return f"{x:.2f}"

# ---- UI ----
st.title("Perfusor‑Rechner 13H3")
st.caption("Interne Rechenhilfe. Therapie/Verordnung immer nach Hausstandard und ärztlicher Anordnung.")
st.markdown("### Patient")
weight_kg = st.number_input("Gewicht (kg)", min_value=0.0, value=70.0, step=0.5, format="%.1f")
st.markdown("---")


weight = st.number_input("Patientengewicht (kg)", min_value=0.0, value=70.0, step=1.0, format="%.1f")


# --- Medikament auswählen (Dropdown statt Tabs) ---
options = list(DRUGS.keys()) + ["Custom"]
choice = st.selectbox("Medikament auswählen", options, index=0)

if choice == "Custom":
    st.subheader("Custom‑Perfusor")
    st.write("Für Mischungen, die nicht in der Standardliste sind.")

    c1, c2, c3 = st.columns(3)
    with c1:
        amt = st.number_input("Menge", min_value=0.0, value=10.0, step=0.1, format="%.2f")
    with c2:
        amt_unit = st.selectbox("Einheit Menge", ["mg", "µg", "IE"])
    with c3:
        vol = st.number_input("Volumen (ml)", min_value=1.0, value=50.0, step=1.0, format="%.0f")

    dose_unit = st.selectbox("Ziel-/Ausgabe-Einheit", ["µg/kg/min", "µg/kg/h", "mg/kg/h", "ng/kg/min", "IE/h"])
    drug = {
        "amount": amt, "amount_unit": amt_unit, "volume_ml": vol,
        "dose_unit": dose_unit, "start": None, "max": None,
        "note": "Custom‑Mischung (keine Speicherung von Daten)."
    }
else:
    drug = DRUGS[choice]
    st.subheader(choice)

conc, conc_unit = conc_per_ml(drug)
st.caption(f"**Konzentration:** {conc_unit} (automatisch aus Menge/Volumen)")

# Hinweis/Start/Max
if drug.get("note"):
    st.info(drug["note"])
if drug.get("start") is not None:
    st.markdown(f"**Start (laut Blatt):** {drug['start']} {drug['dose_unit']}")
if drug.get("max") is not None:
    st.markdown(f"**Max (laut Blatt):** {drug['max']} {drug['dose_unit']}")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Rate → Dosis")
    rate_ml_h = st.number_input("Rate (ml/h)", min_value=0.0, value=2.0, step=0.1, format="%.2f", key="rate_ml_h")
    dose = dose_from_rate(rate_ml_h, weight_kg, drug)
    du = drug["dose_unit"]
    st.metric(label=f"Dosis ({du})", value=fmt(dose))
    st.write(f"= **{rate_ml_h/60.0:.2f} ml/min**")

with col2:
    st.markdown("### Dosis → Rate")
    target = st.number_input(f"Zieldosis ({drug['dose_unit']})", min_value=0.0,
                             value=float(drug["start"]) if drug.get("start") is not None else 0.0,
                             step=0.1, format="%.2f", key="target")
    rate_ml_h2 = rate_from_dose(target, weight_kg, drug)
    st.metric(label="Benötigte Rate (ml/h)", value=fmt(rate_ml_h2))
    if rate_ml_h2 is not None:
        st.write(f"= **{rate_ml_h2/60.0:.2f} ml/min**")

