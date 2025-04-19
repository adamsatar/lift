import streamlit as st

from logic import UserService, SystemService, build_exercise_dataframe

st.title("🏋️ Tidy Workout Tracker")

# --- Workout History Viewer ---
st.header("Workout History")

with UserService() as usr_svc, SystemService() as sys_svc:
    workouts = usr_svc.get_all_workouts()

    if not workouts:
        st.info("No workouts found.")
    else:
        dropdown_options = usr_svc.get_workout_display_strings()
        selected_uuid = st.selectbox("Select a workout", dropdown_options)

        lookup_uuid = usr_svc.get_workout_uuid_map()[selected_uuid]
        exercises = usr_svc.get_exercises_for_workout(lookup_uuid)

        if exercises:
            # Map ID to exercise name
            name_map = sys_svc.get_exercise_name_map()
            df = build_exercise_dataframe(exercises, name_map)
            st.dataframe(df)
        else:
            st.warning("No exercises logged for this workout.")

# You can later add:
# - Workout logging form
# - Catalog editor
# - Dashboard / visualization
