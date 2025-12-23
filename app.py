import streamlit as st

st.set_page_config(page_title="Perfusor-Rechner 13H3", layout="centered")

# ---- Drug definitions (Hausstandard 13H3 / Stand 09/2019; Konzentrationen nach Hausstandard) ----
# amount_unit supports: "mg", "µg", "IE"
# dose_unit supports: "µg/kg/min" (gamma), "µg/kg/h", "mg/kg/h", "ng/kg/min", "µg/h", "IE/h"
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
        "note": "Alternative Konzentration 10 mg/50 ml existiert ebenfalls (separater Eintrag möglich)."
    },
    "Remifentanil (Ultiva) 10 mg/50 ml": {
        "amount": 10, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.05, "max": 0.20,
        "note": "Alternative Konzentration 5 mg/50 ml existiert ebenfalls."
    },
    "Propofol": {
        "amount": 1000, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/kg/h", "start": 1.0, "max": 4.0,
        "note": "Ausgabe in mg/kg/h."
    },
    "Ketanest S (Esketamin)": {
        "amount": 1250, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/kg/h", "start": 1.0, "max": 3.0,
        "note": "Ausgabe in mg/kg/h."
    },
    "Catapresan (Clonidin)": {
        "amount": 1500, "amount_unit": "µg", "volume_ml": 50,
        "dose_unit": "µg/h", "start": None, "max": None,
        "note": "Ausgabe in µg/h (nicht kg-basiert)."
    },
    "Dexdor (Dexmedetomidin)": {
        "amount": 1000, "amount_unit": "µg", "volume_ml": 50,
        "dose_unit": "µg/kg/h", "start": 0.70, "max": 1.40,
        "note": "Ausgabe in µg/kg/h."
    },
    "Dormicum (Midazolam)": {
        "amount": 250, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/h", "start": 100.0, "max": None,
        "note": "Ausgabe in µg/kg/h (mg → µg Umrechnung intern)."
    },
    "Ebrantil (Urapidil)": {
        "amount": 250, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": None, "max": None,
        "note": "Ausgabe in mg/h (nicht kg-basiert)."
    },
    "Heparin": {
        "amount": 10000, "amount_unit": "IE", "volume_ml": 50,
        "dose_unit": "IE/h", "start": None, "max": None,
        "note": "Ausgabe in IE/h."
    },
    "Isuprel (Isoprenalin)": {
        "amount": 1, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.01, "max": 0.03,
        "note": "Ausgabe in γ (=µg/kg/min)."
    },
    "Landiolol (Rapibloc)": {
        "amount": 300, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 2.5, "max": 20.0,
        "note": "Ausgabe in µg/kg/min."
    },
}

# ---- Helpers ----
def to_float(x):
    try:
        return float(x)
    except Exception:
        return None

def conc_per_ml(drug: dict):
    """Return concentration per ml.
    - For mass drugs: returns (µg/ml, 'µg/ml')
    - For IE drugs: returns (IE/ml, 'IE/ml')
    """
    amt = to_float(drug.get("amount"))
    vol = to_float(drug.get("volume_ml"))
    u = drug.get("amount_unit")

    if amt is None or vol is None or vol == 0:
        return 0.0, "—"

    if u == "IE":
        return amt / vol, "IE/ml"

    # mass-based: convert everything to µg
    if u == "mg":
        ug = amt * 1000.0
    elif u == "µg":
        ug = amt * 1.0
    else:
        raise ValueError("Unsupported unit for amount_unit")

    return ug / vol, "µg/ml"

def dose_from_rate(rate_ml_h: float, weight_kg: float | None, drug: dict):
    """Convert pump rate (ml/h) to dose in the drug's configured dose_unit.
    Returns a numeric value (or None).
    """
    conc, _ = conc_per_ml(drug)
    du = drug["dose_unit"]

    # conc is µg/ml for mass drugs, IE/ml for heparin-like
    if du == "IE/h":
        return conc * rate_ml_h

    # Compute µg/h, µg/min
    ug_per_h = conc * rate_ml_h
    ug_per_min = ug_per_h / 60.0

    if du == "µg/h":
        return ug_per_h

    # Units that require weight
    if du == "µg/kg/min":
        return None if not weight_kg else (ug_per_min / weight_kg)
    if du == "µg/kg/h":
        return None if not weight_kg else (ug_per_h / weight_kg)
    if du == "mg/kg/h":
        return None if not weight_kg else ((ug_per_h / 1000.0) / weight_kg)
    if du == "ng/kg/min":
        return None if not weight_kg else ((ug_per_min * 1000.0) / weight_kg)

    # Non-standard (e.g. mg/h) – handle by converting ug/h → mg/h
    if du == "mg/h":
        return ug_per_h / 1000.0

    return None

def rate_from_dose(target: float, weight_kg: float | None, drug: dict):
    """Convert target dose (in drug's dose_unit) to pump rate (ml/h).
    Returns numeric rate in ml/h (or None).
    """
    conc, _ = conc_per_ml(drug)
    du = drug["dose_unit"]

    if target is None:
        return None
    if conc == 0:
        return None

    if du == "IE/h":
        return target / conc

    # Determine required µg/h
    if du == "µg/h":
        ug_per_h = target
    elif du == "µg/kg/min":
        if not weight_kg:
            return None
        ug_per_h = target * weight_kg * 60.0
    elif du == "µg/kg/h":
        if not weight_kg:
            return None
        ug_per_h = target * weight_kg
    elif du == "mg/kg/h":
        if not weight_kg:
            return None
        ug_per_h = target * weight_kg * 1000.0
    elif du == "ng/kg/min":
        if not weight_kg:
            return None
        ug_per_h = (target / 1000.0) * weight_kg * 60.0
    elif du == "mg/h":
        ug_per_h = target * 1000.0
    else:
        return None

    return ug_per_h / conc

def fmt(x):
    # robust formatter for metrics
    if x is None:
        return "—"
    if isinstance(x, (tuple, list)):
        x = x[0] if len(x) else None
        if x is None:
            return "—"
    try:
        return f"{float(x):.2f}"
    except Exception:
        return "—"

# ---- UI ----
st.title("Perfusor-Rechner 13H3")
st.caption("Interne Rechenhilfe. Therapie/Verordnung immer nach Hausstandard & klinischer Situation.")

st.markdown("### Patient")
weight_kg = st.number_input("Gewicht (kg)", min_value=0.0, value=70.0, step=0.5, format="%.1f")
st.markdown("---")

# --- Medikament auswählen (Dropdown) ---
options = list(DRUGS.keys()) + ["Custom"]
choice = st.selectbox("Medikament auswählen", options, index=0)

if choice == "Custom":
    st.subheader("Custom-Perfusor")
    st.write("Für Mischungen, die nicht in der Standardliste sind.")

    c1, c2, c3 = st.columns(3)
    with c1:
        amt = st.number_input("Menge", min_value=0.0, value=10.0, step=0.1, format="%.2f")
    with c2:
        amt_unit = st.selectbox("Einheit Menge", ["mg", "µg", "IE"])
    with c3:
        vol = st.number_input("Volumen (ml)", min_value=1.0, value=50.0, step=1.0, format="%.0f")

    dose_unit = st.selectbox(
        "Ziel-/Ausgabe-Einheit",
        ["µg/kg/min", "µg/kg/h", "mg/kg/h", "ng/kg/min", "µg/h", "mg/h", "IE/h"],
    )

    drug = {
        "amount": amt, "amount_unit": amt_unit, "volume_ml": vol,
        "dose_unit": dose_unit, "start": None, "max": None,
        "note": "Custom-Mischung (keine Speicherung von Daten)."
    }
else:
    drug = DRUGS[choice]
    st.subheader(choice)

conc, conc_unit = conc_per_ml(drug)
st.caption(f"**Konzentration:** {fmt(conc)} {conc_unit}")

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
    default_target = float(drug["start"]) if drug.get("start") is not None else 0.0
    target = st.number_input(
        f"Zieldosis ({drug['dose_unit']})",
        min_value=0.0,
        value=default_target,
        step=0.1,
        format="%.2f",
        key="target",
    )

    rate_ml_h2 = rate_from_dose(target, weight_kg, drug)
    st.metric(label="Benötigte Rate (ml/h)", value=fmt(rate_ml_h2))
    if rate_ml_h2 is not None:
        st.write(f"= **{rate_ml_h2/60.0:.2f} ml/min**")

st.markdown("---")
st.caption("Hinweis: Keine Speicherung von Daten. Dieser Rechner dient nur der Umrechnung (Rate ↔ Dosis).")
