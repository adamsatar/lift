import streamlit as st
import pandas as pd
import datetime
import altair as alt
import db

db.create_tables()
st.title("🏋️ Tidy Workout Tracker")

tabs = st.tabs(["Track", "Edit", "View", "Catalog"])

# ---------------- Track ----------------
with tabs[0]:
    st.subheader("New Exercise Entry")
    catalog_df = db.get_exercise_catalog()
    exercise_names = catalog_df["exercise"].tolist()

    with st.form("new_exercise_entry_form"):
        entry_date = st.date_input("Date", value=datetime.date.today())
        selected_exercise = st.selectbox("Exercise", exercise_names)
        num_sets = st.number_input("Number of Sets", min_value=1, step=1, value=1)
        rest_period = st.number_input("Rest Period (seconds)", min_value=0, step=1, value=60)
        submitted_entry = st.form_submit_button("Add Exercise")

    if submitted_entry:
        meta = db.get_catalog_entry(selected_exercise)
        is_unilateral = meta["sides"] == "Unilateral"
        set_count = num_sets * 2 if is_unilateral else num_sets
        sides = ["Left", "Right"] * (set_count // 2) if is_unilateral else [None] * set_count

        measured_by = meta["measured_by"]
        columns = {
            "Set": list(range(1, set_count + 1)),
            "Weight": [None] * set_count,
        }
        if measured_by == "Reps":
            columns["Reps"] = [None] * set_count
        elif measured_by == "Duration":
            columns["Duration"] = [None] * set_count

        if is_unilateral:
            columns["Side"] = sides

        columns["Note"] = ["" for _ in range(set_count)]

        column_order = ["Set", "Weight"]
        if "Reps" in columns: column_order.append("Reps")
        if "Duration" in columns: column_order.append("Duration")
        if "Side" in columns: column_order.append("Side")
        column_order.append("Note")

        st.session_state.exercise_meta = {
            "date": entry_date.strftime("%m/%d/%Y"),
            "exercise": selected_exercise,
            "total_sets": set_count,
            "rest": rest_period,
            "sides": sides,
            "equipment": meta["equipment"],
            "weight": meta["weight"]
        }
        st.session_state.exercise_df = pd.DataFrame({col: columns[col] for col in column_order})

    if "exercise_df" in st.session_state and "exercise_meta" in st.session_state:
        meta_ex = st.session_state.exercise_meta
        with st.form("exercise_details_form"):
            st.subheader(f"Enter details for {meta_ex['exercise']}")
            st.caption(f"Rest Period: {meta_ex['rest']} seconds")
            if meta_ex["equipment"] == "Barbell":
                st.caption(f"{meta_ex['weight']} lbs will be added for barbell when exercise is saved")
            edited_df = st.data_editor(st.session_state.exercise_df, use_container_width=True, hide_index=True)
            st.session_state.exercise_df = edited_df
            if st.form_submit_button("Save Exercise"):
                for _, row in st.session_state.exercise_df.iterrows():
                    total_weight = float(row.get("Weight") or 0) + float(meta_ex["weight"] if meta_ex["equipment"] == "Barbell" else 0)
                    db.insert_exercise(
                        meta_ex["date"],
                        meta_ex["exercise"],
                        int(row["Set"]),
                        total_weight,
                        row.get("Reps"),
                        row.get("Duration"),
                        meta_ex["rest"],
                        row["Note"],
                        row.get("Side")
                    )
                st.success("Exercise entry saved!")
                del st.session_state.exercise_meta
                del st.session_state.exercise_df

    today_str = datetime.date.today().strftime("%m/%d/%Y")
    current_entries = pd.read_sql_query(
        "SELECT exercise, set_number, side, weight, reps, rest, note, duration FROM exercises WHERE date = ?",
        db.conn, params=(today_str,)
    )

    # Always insert and rename, even if DataFrame is empty
    current_entries.insert(0, "Date", today_str)
    current_entries.rename(columns={
        "exercise": "Exercise",
        "set_number": "Set",
        "side": "Side",
        "weight": "Weight",
        "reps": "Reps",
        "rest": "Rest",
        "note": "Note",
        "duration": "Duration"
    }, inplace=True)

    current_entries = current_entries[["Date", "Exercise", "Set", "Weight", "Reps", "Duration", "Side", "Rest", "Note"]]

    st.subheader("Today's Exercise Entries")
    st.dataframe(current_entries, hide_index=True, use_container_width=True)

# ---------------- Edit ----------------
with tabs[1]:
    st.subheader("Edit Exercise Log")
    log_df = db.get_exercise_log()
    if log_df.empty:
        st.info("No exercise entries available.")
    else:
        display_df = log_df[["Date", "Exercise", "Set", "Weight", "Reps", "Duration", "Side", "Rest", "Note"]].copy()
        edited_log = st.data_editor(display_df, use_container_width=True, num_rows="dynamic")
        if st.button("Save Log Changes"):
            for _, row in edited_log.iterrows():
                db.update_exercise_row(row)
            st.success("Exercise log updated!")
            st.rerun()

# ---------------- View ----------------
with tabs[2]:
    st.subheader("Graphical View of Exercise Data")
    log_df = db.get_exercise_log()
    if log_df.empty:
        st.info("No data available for analysis.")
    else:
        exercise_options = sorted(log_df["Exercise"].unique())
        selected_ex = st.selectbox("Select Exercise", exercise_options)
        filtered_df = log_df[log_df["Exercise"] == selected_ex].copy()
        filtered_df["Datetime"] = pd.to_datetime(filtered_df["Date"], format="%m/%d/%Y")
        filtered_df["Volume"] = filtered_df["Weight"] * filtered_df["Reps"]
        agg_df = filtered_df.groupby("Date", as_index=False)["Volume"].sum()
        agg_df["Date"] = pd.to_datetime(agg_df["Date"], format="%m/%d/%Y")
        volume_chart = alt.Chart(agg_df).mark_line(point=True).encode(
            x=alt.X("Date:T", title="Workout Date", axis=alt.Axis(format="%m/%d/%Y")),
            y=alt.Y("Volume:Q", title="Total Volume (Weight x Reps)"),
            tooltip=["Date", "Volume"]
        ).properties(width=700, height=400, title=f"Volume Progression for {selected_ex}")
        st.altair_chart(volume_chart, use_container_width=True)

# ---------------- Catalog ----------------
with tabs[3]:
    st.subheader("Exercise Catalog")
    catalog_df = db.get_exercise_catalog()
    display_df = catalog_df.drop(columns=["id"]).rename(columns={
        "exercise": "Exercise",
        "equipment": "Equipment",
        "weight": "Weight",
        "sides": "Sides",
        "measured_by": "Measured By"
    })

    edited_df = st.data_editor(display_df, use_container_width=True, num_rows="dynamic")

    if st.button("Save Catalog Changes"):
        edited_df.columns = ["exercise", "equipment", "weight", "sides", "measured_by"]
        edited_df["id"] = catalog_df["id"]
        for _, row in edited_df.iterrows():
            db.update_catalog_entry(row)
        st.success("Catalog updated!")
        st.rerun()

    st.divider()
    st.subheader("Add New Catalog Entry")
    with st.form("add_catalog_form"):
        new_name = st.text_input("Exercise Name")
        new_equipment = st.selectbox("Equipment Type", ["Barbell", "Dumbbell", "Machine", "Bodyweight", "Cable"])
        new_weight = st.number_input("Default Equipment Weight (lbs)", value=45.0)
        new_sides = st.selectbox("Exercise Type", ["Bilateral", "Unilateral"])
        new_measured_by = st.selectbox("Measured By", ["Reps", "Duration"])
        submit_new = st.form_submit_button("Add Exercise")
    if submit_new:
        db.insert_catalog_entry(new_name, new_equipment, new_weight, new_sides, new_measured_by)
        st.success(f"Added '{new_name}' to catalog!")
        st.rerun()