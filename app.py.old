import streamlit as st
import pandas as pd
import datetime
import altair as alt
import db
import plotly.express as px

db.create_tables()
st.title("🏋️ Tidy Workout Tracker")

tabs = st.tabs(["Track", "Edit", "View", "Catalog"])

# ---------------- Track ----------------
with tabs[0]:
    st.subheader("New Exercise Entry")
    catalog_df = db.get_catalog_with_muscle_groups()
    exercise_names = catalog_df["exercise"].tolist()

    with st.form("new_exercise_entry_form"):
        entry_date = st.date_input("Date", value=datetime.date.today())
        selected_exercise = st.selectbox("Exercise", exercise_names)
        num_sets = st.number_input("Number of Sets", min_value=1, step=1, value=1)
        rest_period = st.number_input("Rest Period (seconds)", min_value=0, step=1, value=60)
        submitted_entry = st.form_submit_button("Add Exercise")

    if submitted_entry:
        meta = db.get_catalog_entry(selected_exercise)
        measured_by = meta["measured_by"]
        columns = {
            "Set": list(range(1, num_sets + 1)),
            "Weight": [None] * num_sets,
        }
        if measured_by == "Reps":
            columns["Reps"] = [None] * num_sets
        elif measured_by == "Duration":
            columns["Duration"] = [None] * num_sets

        columns["Note"] = ["" for _ in range(num_sets)]

        column_order = ["Set", "Weight"]
        if "Reps" in columns: column_order.append("Reps")
        if "Duration" in columns: column_order.append("Duration")
        column_order.append("Note")

        st.session_state.exercise_meta = {
            "date": entry_date.strftime("%m/%d/%Y"),
            "exercise": selected_exercise,
            "total_sets": num_sets,
            "rest": rest_period,
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
                        row["Note"]
                    )
                st.success("Exercise entry saved!")
                del st.session_state.exercise_meta
                del st.session_state.exercise_df

    today_str = datetime.date.today().strftime("%m/%d/%Y")
    current_entries = pd.read_sql_query(
        "SELECT exercise, set_number, weight, reps, rest, note, duration FROM exercises WHERE date = ?",
        db.user_conn, params=(today_str,)
    )

    # Always insert and rename, even if DataFrame is empty
    current_entries.insert(0, "Date", today_str)
    current_entries.rename(columns={
        "exercise": "Exercise",
        "set_number": "Set",
        "weight": "Weight",
        "reps": "Reps",
        "rest": "Rest",
        "note": "Note",
        "duration": "Duration"
    }, inplace=True)

    current_entries = current_entries[["Date", "Exercise", "Set", "Weight", "Reps", "Duration", "Rest", "Note"]]

    st.subheader("Today's Exercise Entries")
    st.dataframe(current_entries, hide_index=True, use_container_width=True)

# ---------------- Edit ----------------
with tabs[1]:
    st.subheader("Edit Exercise Log")

    log_df = db.get_exercise_log()
    if log_df.empty:
        st.info("No exercise entries available.")
    else:
        available_dates = sorted(log_df["Date"].unique())
        selected_dates = st.multiselect("Filter by Date", options=available_dates, default=[])

        # Show all if none selected
        if not selected_dates:
            selected_dates = available_dates

        # Filter log by selected dates first
        date_filtered_df = log_df[log_df["Date"].isin(selected_dates)]
        available_exercises = sorted(date_filtered_df["Exercise"].unique())
        selected_exercises = st.multiselect("Filter by Exercise", options=available_exercises, default=[])
        if not selected_exercises:
            selected_exercises = available_exercises

        filtered_df = date_filtered_df[date_filtered_df["Exercise"].isin(selected_exercises)]

        display_df = filtered_df[["id", "Date", "Exercise", "Set", "Weight", "Reps", "Duration", "Rest", "Note"]].copy()
        edited_log = st.data_editor(display_df.drop(columns=["id"]), use_container_width=True, num_rows="dynamic")

        if st.button("Save Log Changes"):
            original_ids = set(display_df["id"])
            edited_ids = set(edited_log.index)

            # Update modified rows
            for idx in edited_ids:
                row_with_id = display_df.iloc[idx].copy()
                row_with_id.update(edited_log.loc[idx])
                db.update_exercise_row(row_with_id)

            # Remove deleted rows
            deleted_ids = original_ids - edited_ids
            for del_id in deleted_ids:
                db.delete_exercise_row(int(del_id))

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

        st.subheader("Exercise Entries")
        entry_table = filtered_df[["Date", "Set", "Weight", "Reps", "Duration", "Rest", "Note"]].copy()
        st.dataframe(entry_table, hide_index=True, use_container_width=True)

        volume_chart = alt.Chart(agg_df).mark_line(point=True).encode(
            x=alt.X("Date:T", title="Workout Date", axis=alt.Axis(format="%m/%d/%Y")),
            y=alt.Y("Volume:Q", title="Total Volume (Weight x Reps)"),
            tooltip=["Date", "Volume"]
        ).properties(width=700, height=400, title=f"Volume Progression for {selected_ex}")
        st.altair_chart(volume_chart, use_container_width=True)

        st.subheader("Experimental: Combined Volume Chart")

        # Prepare full volume data
        all_df = log_df.copy()
        all_df["Date"] = pd.to_datetime(all_df["Date"], format="%m/%d/%Y")
        all_df["Volume"] = all_df["Weight"] * all_df["Reps"]
        volume_df = all_df.groupby(["Date", "Exercise"], as_index=False)["Volume"].sum()

        # Create interactive Plotly chart
        fig = px.line(volume_df, x="Date", y="Volume", color="Exercise",
                      title="Volume Over Time (All Exercises)",
                      markers=True)
        fig.update_layout(legend_title_text="Exercise")

        st.plotly_chart(fig, use_container_width=True)

# ---------------- Catalog ----------------
muscle_groups_df = db.get_muscle_groups()
muscle_groups_df.rename(columns={k: db.COLUMN_LABELS[k] for k in muscle_groups_df.columns if k in db.COLUMN_LABELS}, inplace=True)

tag_map_df = db.get_tag_map()

with tabs[3]:
    st.subheader("Exercise Catalog")
    catalog_df = db.get_catalog_with_muscle_groups()

    display_df = catalog_df.drop(columns=["id"]).rename(columns={k: db.COLUMN_LABELS[k] for k in catalog_df.columns if k in db.COLUMN_LABELS})

    st.dataframe(display_df, hide_index=True, use_container_width=True)