import streamlit as st

from logic import UserService, SystemService, get_exercise_df, get_plotly_volume_chart, get_all_exercises_df

st.title("🏋️ Tidy Workout Tracker")

tab1, tab2, tab3 = st.tabs(["Edit", "View", "Analyze"])

with tab1:
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
                name_map = sys_svc.get_exercise_name_map()
                df = get_exercise_df(exercises, name_map)
                st.dataframe(df)
            else:
                st.warning("No exercises logged for this workout.")

with tab2:
    all_exercises_df = get_all_exercises_df()

    selected_dates = st.multiselect("Filter by Date",
                                    options=sorted(all_exercises_df["Date"].unique()))
    selected_exercises = st.multiselect("Filter by Exercise",
                                        options= sorted(all_exercises_df["Exercise"].unique()))

    filtered_df = all_exercises_df

    if selected_dates:
        filtered_df = filtered_df[filtered_df["Date"].isin(selected_dates)]

    if selected_exercises:
        filtered_df = filtered_df[filtered_df["Exercise"].isin(selected_exercises)]

    st.dataframe(filtered_df)

with tab3:
    plotly_chart = get_plotly_volume_chart()
    st.plotly_chart(plotly_chart, use_container_width=True)
