# 🏧 PayGuard — Impact-Based Automated Troubleshooting System

**Hackathon Project | Team: 3 Developers | Timeline: 4 Days**

A structured, intelligent decision-support system for digital payment failure incidents.

---

## 🗂 Project Structure

```
payment_troubleshooter/
├── app.py               ← Streamlit dashboard (entry point)
├── pipeline.py          ← Orchestrates all layers end-to-end
├── data_generator.py    ← Synthetic dataset generation
├── classifier.py        ← Layer 1: ML classification (RandomForest)
├── impact_scorer.py     ← Layer 2: Business impact scoring
├── action_engine.py     ← Layers 3 & 4: Action rules + escalation
├── feedback_store.py    ← Layer 5: Technician feedback loop
├── requirements.txt
├── data/                ← Auto-created (training CSV, feedback CSV)
└── model/               ← Auto-created (trained model pickle)
```

---

## 🚀 Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. (Optional) Pre-train the model
```bash
python classifier.py
```
The app will auto-train on first launch if no model exists.

### 3. Launch the dashboard
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 🧠 System Architecture

```
Raw Incident Data
       │
       ▼
┌─────────────────────┐
│  Layer 1            │  RandomForest classifier
│  Classification     │  → predicted_issue
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Layer 2            │  Formula: vol × amt × (downtime/60) × complaint_mult
│  Impact Scoring     │  → impact_score (₹)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Layer 3            │  Rule map: issue_type → action + team + SLA
│  Action Recommender │  → recommended_action
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Layer 4            │  if impact > ₹1L OR downtime > 120min → ESCALATE
│  Escalation Engine  │  → escalation_status
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Layer 5            │  Technician submits corrections + ratings
│  Feedback Loop      │  → feedback.csv (audit + future retraining)
└─────────────────────┘
```

---

## 📊 Output Schema

| Column | Description |
|--------|-------------|
| `atm_id` | ATM identifier |
| `location` | Branch/location name |
| `predicted_issue` | ML-classified failure type |
| `impact_score` | Financial exposure estimate (₹) |
| `recommended_action` | Rule-based remediation steps |
| `escalation_status` | Escalated or Normal |
| `sla_minutes` | Target resolution time |
| `responsible_team` | Assigned team |

---

## 🔧 Issue Types & Actions

| Issue | Recommended Action | Team |
|-------|--------------------|------|
| `network_failure` | Restart interface, check ISP | Network Ops |
| `card_declined` | Check processor gateway | Payments Team |
| `hardware_fault` | Dispatch field technician | Field Maintenance |
| `cash_out` | Emergency cash replenishment | Cash Management |
| `auth_timeout` | Check auth server latency | Backend Engineering |

---

## 💡 Demo Tips

1. Use **"Generate Demo Data"** mode for instant results
2. Set slider to 50–100 incidents for a rich dashboard
3. Check the **Escalated Incidents** section for detail cards
4. Submit a feedback entry to show the feedback loop
5. Download results CSV to show the output schema

---

## ⚠️ Constraints Met

- ✅ No deep learning
- ✅ No cloud dependencies — fully offline
- ✅ Minimal dependencies (4 packages)
- ✅ Beginner-friendly modular code
- ✅ Demo-stable Streamlit UI
