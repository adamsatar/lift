# 🏋️ Tidy Workout Tracker

A simple Streamlit app to log, track, and visualize workout exercises. Supports reps-based and duration-based logging, including unilateral movements.

## Features
- Log sets with weight, reps or duration
- Track unilateral exercises with left/right handling
- Visualize volume progression over time
- Edit historical entries
- Maintain an exercise catalog with metadata

## Getting Started

### Prerequisites
- Python 3.9+
- [Streamlit](https://streamlit.io)

### Setup
```bash
pip install -r requirements.txt
streamlit run app.py
```

## File Structure
```
.
├── app.py               # Streamlit front-end logic
├── db.py                # Database and schema functions
├── workout_tracker.db   # Local SQLite database (auto-created)
├── requirements.txt     # Dependencies
└── README.md            # App documentation
```

## License
MIT
