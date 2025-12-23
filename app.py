import streamlit as st

st.set_page_config(page_title="Perfusor-Rechner 13H3", layout="centered")

# =============================================================================
# Perfusorstandard 13H3 (Stand 09/2019) – Rechner
# - Dropdown Medikament
# - Rate ↔ Dosis (in der Einheit des Medikaments laut Tabelle)
# - 2 Dezimalstellen
# - unterstützt: µg/kg/min, µg/kg/h, mg/kg/h, ng/kg/min, mg/h, µg/h, g/h, mmol/h, IE/h
# - Einträge ohne echte Perfusor-Rate/Dosis-Logik werden als INFO/BOLUS markiert
# =============================================================================

SUPPORTED_DOSE_UNITS = {
    "µg/kg/min", "µg/kg/h", "mg/kg/h", "ng/kg/min",
    "mg/h", "µg/h", "g/h", "mmol/h", "IE/h",
    "INFO/BOLUS"
}

# ---- Drug definitions (Hausstandard 13H3 / Stand 09/2019; Werte wie im PDF) ----
# amount_unit supports: "g", "mg", "µg", "ng", "mmol", "IE"
# dose_unit supports: see SUPPORTED_DOSE_UNITS
DRUGS = {
    # --- Katecholamine / Inotrope ---
    "Arterenol (Noradrenalin) 10 mg/50 ml": {
        "amount": 10, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.10, "max": None,
        "note": "Tabelle: meist 10 mg/50 ml NaCl 0,9%; Richtwerte im Kommentar."
    },
    "Suprarenin (Adrenalin) 10 mg/50 ml": {
        "amount": 10, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.10, "max": None,
        "note": "Tabelle: meist 10 mg/50 ml NaCl 0,9%; Richtwerte im Kommentar."
    },
    "Dobutrex (Dobutamin) 250 mg/50 ml": {
        "amount": 250, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 3.0, "max": None,
        "note": "Im Blatt stehen 250 mg/50 ml und 500 mg/50 ml."
    },
    "Dobutrex (Dobutamin) 500 mg/50 ml": {
        "amount": 500, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 3.0, "max": None,
        "note": "Im Blatt stehen 250 mg/50 ml und 500 mg/50 ml."
    },
    "Dopamin 250 mg/50 ml": {
        "amount": 250, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 3.0, "max": None,
        "note": "Kommentar im Blatt: 'Nierendosis' individuell; Vasokonstriktion ab >5."
    },
    "Corotrop (Milrinon) 20 mg/50 ml": {
        "amount": 20, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.25, "max": 0.75,
        "note": "Im Blatt: ohne Bolus."
    },
    "Simdax (Levosimendan) 12.5 mg/50 ml": {
        "amount": 12.5, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.10, "max": 0.20,
        "note": "Im Blatt: auf Intensiv OHNE Bolus; Dauerinfusion 0,05–0,2 µg/kg/min."
    },
    "Isuprel (Isoprenalin) 1 mg/50 ml": {
        "amount": 1, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.01, "max": 0.03,
        "note": "Im Blatt: reiner ß-Stimulator."
    },
    "Rapibloc (Landiolol) 300 mg/50 ml": {
        "amount": 300, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 2.50, "max": 20.0,
        "note": "Im Blatt: schrittweise Erhöhung alle 10 min."
    },
    "Brevibloc (Esmolol) 2500 mg/50 ml": {
        "amount": 2500, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 200.0, "max": None,
        "note": "Im Blatt: Steigerung 200 mg/h alle 10 min; hohe Dosen 800–1200 mg/h."
    },

    # --- Analgosedierung / Narkose ---
    "Ultiva (Remifentanil) 5 mg/50 ml": {
        "amount": 5, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.05, "max": 0.20,
        "note": "Im Blatt: im Unterschied zu anderen Opiaten in µg/kg/min."
    },
    "Ultiva (Remifentanil) 10 mg/50 ml": {
        "amount": 10, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.05, "max": 0.20,
        "note": "Im Blatt: alternative Konzentration."
    },
    "Propofol 1000 mg/50 ml": {
        "amount": 1000, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/kg/h", "start": 1.0, "max": 4.0,
        "note": "Im Blatt: mg/kg/h."
    },
    "Ketanest S (Esketamin) 1250 mg/50 ml": {
        "amount": 1250, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/kg/h", "start": 1.0, "max": 3.0,
        "note": "Im Blatt: mg/kg/h."
    },
    "Dormicum (Midazolam) 250 mg/50 ml": {
        "amount": 250, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/h", "start": 100.0, "max": None,
        "note": "Im Blatt: geringe D 25–50; hohe D >300 µg/kg/h."
    },
    "Dexdor (Dexmedetomidin) 1000 µg/50 ml": {
        "amount": 1000, "amount_unit": "µg", "volume_ml": 50,
        "dose_unit": "µg/kg/h", "start": 0.70, "max": 1.40,
        "note": "Im Blatt: Cave HF-/RR-Abfall."
    },
    "Fentanyl 2.5 mg/50 ml": {
        "amount": 2.5, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/h", "start": 1.0, "max": 4.0,
        "note": "Im Blatt: µg/kg/h."
    },
    "Thiopental 1000 mg/50 ml": {
        "amount": 1000, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/kg/h", "start": 2.0, "max": 5.0,
        "note": "Im Blatt: ~2 bis 5 mg/kg/h."
    },
    "Esmeron (Rocuronium) 500 mg/50 ml": {
        "amount": 500, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 40.0, "max": None,
        "note": "Im Blatt: 30–50 mg/h; keine Steigerung."
    },
    "Brietal (Methohexital) 500 mg/50 ml": {
        "amount": 500, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 50.0, "max": 200.0,
        "note": "Im Blatt: möglichst vermeiden."
    },
    "Haldol Perfusor (Haloperidol) 25 mg/50 ml": {
        "amount": 25, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 0.5, "max": 10.0,
        "note": "Im Blatt: 0,5–1 mg/h bis 10 mg/h."
    },

    # --- Blutdruck / Vasodilatation / Rhythmus ---
    "Catapresan (Clonidin) 1.5 mg/50 ml": {
        "amount": 1.5, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/h", "start": 30.0, "max": 120.0,
        "note": "Nicht gewichtsadaptiert (µg/h)."
    },
    "Ebrantil (Urapidil) 250 mg/50 ml": {
        "amount": 250, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 10.0, "max": 50.0,
        "note": "Nicht gewichtsadaptiert (mg/h)."
    },
    "Dilzem (Diltiazem) 100 mg/50 ml": {
        "amount": 100, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 10.0, "max": 40.0,
        "note": "Im Blatt: 10 mg/h; max 40 mg/h."
    },
    "Isoptin (Verapamil) 50 mg/50 ml": {
        "amount": 50, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 0.10, "max": None,
        "note": "Im Blatt: mg/h; Kommentar enthält zusätzliche Hinweise (Hypertensive Krise)."
    },
    "Perlinganit (Nitroglycerin) 50 mg/50 ml": {
        "amount": 50, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 1.0, "max": 4.0,
        "note": "Im Blatt: mg/h 1 bis 4."
    },
    "Nipruss (Nitroprussid) 60 mg/50 ml": {
        "amount": 60, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.5, "max": 8.0,
        "note": "Im Blatt: Lichtschutz; Kurzzeitanwendung."
    },

    # --- Antikoagulation / Thrombolyse / Sonstiges ---
    "Heparin 10.000 IE/50 ml": {
        "amount": 10000, "amount_unit": "IE", "volume_ml": 50,
        "dose_unit": "IE/h", "start": 350.0, "max": None,
        "note": "Nicht gewichtsadaptiert (IE/h). Start hier als Prophylaxe-Mittelwert 350 IE/h; titrieren nach APTT."
    },
    "Argatra (Argatroban) 50 mg/50 ml": {
        "amount": 50, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "µg/kg/min", "start": 0.20, "max": None,
        "note": "Im Blatt: nach APTT; Dosis oft geringer als Beipack."
    },
    "Actilyse (Alteplase, rtPA) – INFO": {
        "amount": 0, "amount_unit": "mg", "volume_ml": 1,
        "dose_unit": "INFO/BOLUS", "start": None, "max": None,
        "note": "Kein Standard-Perfusor (Thrombolyse-Schema). Rechenhilfe hier deaktiviert."
    },

    # --- Diurese / GI / TX / etc ---
    "Lasix (Furosemid) 500 mg/50 ml": {
        "amount": 500, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 10.0, "max": 40.0,
        "note": "Im Blatt: mg/h 10 bis 40."
    },
    "Pantoloc (Pantoprazol) 200 mg/50 ml": {
        "amount": 200, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 2.0, "max": None,
        "note": "Im Blatt: 2 mg/h."
    },
    "Somatostatin 6 mg/50 ml": {
        "amount": 6, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 0.36, "max": None,
        "note": "Im Blatt: 0,36 mg/h (= 3 ml/h)."
    },
    "Hydrocortone (Hydrocortison) 100 mg/50 ml": {
        "amount": 100, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 8.4, "max": None,
        "note": "Im Blatt: Stufenschema (8,4 → 4,2 → 2,1 mg/h)."
    },
    "Insulin (Actrapid) 50 IE/50 ml": {
        "amount": 50, "amount_unit": "IE", "volume_ml": 50,
        "dose_unit": "IE/h", "start": 1.0, "max": None,
        "note": "Im Blatt: 0,5–1 IE/h als Start; nach BZ titrieren."
    },
    "Prograf (Tacrolimus) 1 mg/50 ml": {
        "amount": 1, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 0.025, "max": None,
        "note": "Im Blatt: nach TX-Team / Spiegel."
    },
    "Sandimmun (Ciclosporin) 50 mg/50 ml": {
        "amount": 50, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 2.0, "max": None,
        "note": "Im Blatt: nach Spiegel; Beginn 50 mg/d ≈ 2 mg/h."
    },
    "Sedacoron (Amiodaron) 750 mg/50 ml": {
        "amount": 750, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 45.0, "max": None,
        "note": "Im Blatt: Aufsättigungs-/Gesamtdosis siehe Kommentar."
    },
    "Theospirex (Theophyllin) 1000 mg/50 ml": {
        "amount": 1000, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 20.0, "max": 50.0,
        "note": "Im Blatt: 20 bis 50 mg/h."
    },
    "Vasopressin 40 IE/40 ml": {
        "amount": 40, "amount_unit": "IE", "volume_ml": 40,
        "dose_unit": "IE/h", "start": 1.0, "max": 4.0,
        "note": "Im Blatt: nicht als titrierbarer Vasopressor verwenden; kurz wie möglich."
    },
    "Vendal (Morphin) 50 mg/50 ml": {
        "amount": 50, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "mg/h", "start": 1.0, "max": 10.0,
        "note": "Im Blatt: 1–10 mg/h (oder mehr)."
    },
    "Minirin (Desmopressin) 20 µg/50 ml": {
        "amount": 20, "amount_unit": "µg", "volume_ml": 50,
        "dose_unit": "µg/h", "start": 4.0, "max": None,
        "note": "Im Blatt: 4 µg/h über 5 h."
    },
    "Minprog (Alprostadil) 1 mg/50 ml": {
        "amount": 1, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "ng/kg/min", "start": 2.5, "max": 10.0,
        "note": "Im Blatt: ng/kg/min."
    },
    "Flolan (Epoprostenol) 0.25 mg/50 ml": {
        "amount": 0.25, "amount_unit": "mg", "volume_ml": 50,
        "dose_unit": "ng/kg/min", "start": 3.0, "max": 15.0,
        "note": "Im Blatt: ng/kg/min; individuelle Zielwerte."
    },

    # --- Elektrolyte / Spezial (mmol/h, g/h) ---
    "Glucose-1-Phosphat (5 Amp zu 10 mmol) /50 ml": {
        "amount": 50, "amount_unit": "mmol", "volume_ml": 50,
        "dose_unit": "mmol/h", "start": 15.0, "max": None,
        "note": "Im Blatt: 15 mmol/h (=15 ml/h) – Beispiel im Kommentar."
    },
    "Kalium Chlorid (pur, nur ZVK) – INFO": {
        "amount": 0, "amount_unit": "mmol", "volume_ml": 1,
        "dose_unit": "INFO/BOLUS", "start": None, "max": None,
        "note": "Im Blatt: als mmol über Stunden, aber Mischung/Volumen variabel – bitte als Custom rechnen."
    },
    "Kalium Malat (pur, nur ZVK) – INFO": {
        "amount": 0, "amount_unit": "mmol", "volume_ml": 1,
        "dose_unit": "INFO/BOLUS", "start": None, "max": None,
        "note": "Im Blatt: als mmol über Stunden, aber Mischung/Volumen variabel – bitte als Custom rechnen."
    },
    "Hepamerz (5 Amp zu 5 g) /50 ml": {
        "amount": 5, "amount_unit": "g", "volume_ml": 50,
        "dose_unit": "g/h", "start": 1.0, "max": None,
        "note": "Im Blatt: g/h."
    },

    # --- Weitere Einträge ohne klare Perfusor-Standard-Rate ---
    "Beriplex – INFO": {
        "amount": 0, "amount_unit": "IE", "volume_ml": 1,
        "dose_unit": "INFO/BOLUS", "start": None, "max": None,
        "note": "Im Blatt: 'pur im Perfusor ~1500–2000 IE über ca. 20 min' (kein Standard mg/h)."
    },
    "Prothromplex – INFO": {
        "amount": 0, "amount_unit": "IE", "volume_ml": 1,
        "dose_unit": "INFO/BOLUS", "start": None, "max": None,
        "note": "Im Blatt: 'pur im Perfusor ~1200–2400 IE' (kein Standard IE/h)."
    },
    "Novoseven – INFO": {
        "amount": 0, "amount_unit": "mg", "volume_ml": 1,
        "dose_unit": "INFO/BOLUS", "start": None, "max": None,
        "note": "Im Blatt: Bolusgaben, kein Perfusor-Standard."
    },
    "Haldol Bolus – INFO": {
        "amount": 0, "amount_unit": "mg", "volume_ml": 1,
        "dose_unit": "INFO/BOLUS", "start": None, "max": None,
        "note": "Bolus 5–10 mg, kein Perfusor-Standard."
    },
    "Bricanyl (Terbutalin) – INFO": {
        "amount": 0, "amount_unit": "mg", "volume_ml": 1,
        "dose_unit": "INFO/BOLUS", "start": None, "max": None,
        "note": "Im Blatt: '6 Amp/50 ml' aber Dosisführung als ml/h bzw. s.c. Alternativen – bitte als Custom rechnen."
    },
    "Cormagnesin – INFO": {
        "amount": 0, "amount_unit": "mg", "volume_ml": 1,
        "dose_unit": "INFO/BOLUS", "start": None, "max": None,
        "note": "Im Blatt: große therapeutische Breite, aber keine eindeutige Standardmischung im Tabellenfeld."
    },
}

# ---- Helpers ----
def to_float(x):
    try:
        return float(x)
    except Exception:
        return None

def amount_to_base(amount: float, unit: str):
    """
    Convert amount to base units for concentration:
    - mass drugs -> micrograms (µg)
    - mmol drugs -> mmol (kept)
    - IE drugs -> IE (kept)
    """
    if unit == "IE":
        return amount, "IE"
    if unit == "mmol":
        return amount, "mmol"

    # mass -> µg
    if unit == "g":
        return amount * 1_000_000.0, "µg"
    if unit == "mg":
        return amount * 1_000.0, "µg"
    if unit == "µg":
        return amount * 1.0, "µg"
    if unit == "ng":
        return amount / 1_000.0, "µg"

    raise ValueError(f"Unsupported amount_unit: {unit}")

def conc_per_ml(drug: dict):
    """Return concentration per ml in the matching base unit."""
    amt = to_float(drug.get("amount"))
    vol = to_float(drug.get("volume_ml"))
    u = drug.get("amount_unit")

    if amt is None or vol is None or vol == 0:
        return 0.0, "—"

    base_amt, base_unit = amount_to_base(amt, u)

    if base_unit == "IE":
        return base_amt / vol, "IE/ml"
    if base_unit == "mmol":
        return base_amt / vol, "mmol/ml"
    # base_unit == "µg"
    return base_amt / vol, "µg/ml"

def dose_from_rate(rate_ml_h: float, weight_kg: float | None, drug: dict):
    """Convert pump rate (ml/h) to dose in the drug's configured dose_unit."""
    du = drug["dose_unit"]
    if du == "INFO/BOLUS":
        return None

    conc, conc_unit = conc_per_ml(drug)  # µg/ml OR IE/ml OR mmol/ml
    if conc == 0:
        return None

    # Non-weight-based direct units
    if du == "IE/h":
        # conc in IE/ml
        return conc * rate_ml_h
    if du == "mmol/h":
        # conc in mmol/ml
        return conc * rate_ml_h
    if du == "µg/h":
        # conc in µg/ml
        return conc * rate_ml_h
    if du == "mg/h":
        # conc in µg/ml -> mg/h
        return (conc * rate_ml_h) / 1000.0
    if du == "g/h":
        # conc in µg/ml -> g/h
        return (conc * rate_ml_h) / 1_000_000.0

    # Weight-based units (mass)
    ug_per_h = conc * rate_ml_h
    ug_per_min = ug_per_h / 60.0

    if du == "µg/kg/min":
        return None if not weight_kg else (ug_per_min / weight_kg)
    if du == "µg/kg/h":
        return None if not weight_kg else (ug_per_h / weight_kg)
    if du == "mg/kg/h":
        return None if not weight_kg else ((ug_per_h / 1000.0) / weight_kg)
    if du == "ng/kg/min":
        return None if not weight_kg else ((ug_per_min * 1000.0) / weight_kg)

    return None

def rate_from_dose(target: float, weight_kg: float | None, drug: dict):
    """Convert target dose (in drug's dose_unit) to pump rate (ml/h)."""
    du = drug["dose_unit"]
    if du == "INFO/BOLUS":
        return None

    conc, conc_unit = conc_per_ml(drug)
    if target is None or conc == 0:
        return None

    # Non-weight-based direct units
    if du == "IE/h":
        return target / conc
    if du == "mmol/h":
        return target / conc
    if du == "µg/h":
        ug_per_h = target
        return ug_per_h / conc
    if du == "mg/h":
        ug_per_h = target * 1000.0
        return ug_per_h / conc
    if du == "g/h":
        ug_per_h = target * 1_000_000.0
        return ug_per_h / conc

    # Weight-based (mass)
    if du == "µg/kg/min":
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
    else:
        return None

    return ug_per_h / conc

def fmt(x):
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

# Medikament auswählen
options = list(DRUGS.keys()) + ["Custom"]
choice = st.selectbox("Medikament auswählen", options, index=0)

# Custom
if choice == "Custom":
    st.subheader("Custom-Perfusor")
    st.write("Für Mischungen, die nicht in der Standardliste sind.")

    c1, c2, c3 = st.columns(3)
    with c1:
        amt = st.number_input("Menge", min_value=0.0, value=10.0, step=0.1, format="%.2f")
    with c2:
        amt_unit = st.selectbox("Einheit Menge", ["g", "mg", "µg", "ng", "mmol", "IE"])
    with c3:
        vol = st.number_input("Volumen (ml)", min_value=1.0, value=50.0, step=1.0, format="%.0f")

    dose_unit = st.selectbox(
        "Ziel-/Ausgabe-Einheit",
        ["µg/kg/min", "µg/kg/h", "mg/kg/h", "ng/kg/min", "mg/h", "µg/h", "g/h", "mmol/h", "IE/h"],
    )

    drug = {
        "amount": amt, "amount_unit": amt_unit, "volume_ml": vol,
        "dose_unit": dose_unit, "start": None, "max": None,
        "note": "Custom-Mischung (keine Speicherung von Daten)."
    }
else:
    drug = DRUGS[choice]
    st.subheader(choice)

# Anzeige Konzentration
conc, conc_unit = conc_per_ml(drug)
st.caption(f"**Konzentration:** {fmt(conc)} {conc_unit}")

# Hinweis/Start/Max
if drug.get("note"):
    st.info(drug["note"])
if drug.get("start") is not None:
    st.markdown(f"**Start (laut Blatt):** {drug['start']} {drug['dose_unit']}")
if drug.get("max") is not None:
    st.markdown(f"**Max (laut Blatt):** {drug['max']} {drug['dose_unit']}")

st.markdown("---")

# Rechner
du = drug["dose_unit"]

if du == "INFO/BOLUS":
    st.warning("Für dieses Medikament ist im Standardblatt keine eindeutige kontinuierliche Perfusor-Umrechnung (Rate ↔ Dosis) definiert. Bitte nutze ggf. 'Custom' oder halte dich an das Protokoll im Kommentar.")
else:
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Rate → Dosis")
        rate_ml_h = st.number_input("Rate (ml/h)", min_value=0.0, value=2.0, step=0.1, format="%.2f", key="rate_ml_h")
        dose = dose_from_rate(rate_ml_h, weight_kg, drug)
        st.metric(label=f"Dosis ({du})", value=fmt(dose))
        st.write(f"= **{rate_ml_h/60.0:.2f} ml/min**")

    with col2:
        st.markdown("### Dosis → Rate")
        default_target = float(drug["start"]) if drug.get("start") is not None else 0.0
        target = st.number_input(
            f"Zieldosis ({du})",
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
