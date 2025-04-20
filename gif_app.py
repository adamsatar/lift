import streamlit as st
import json
import imageio.v2 as imageio
from moviepy import ImageSequenceClip
from PIL import Image
import numpy as np
from tempfile import NamedTemporaryFile

# --- Load JSON Data ---
with open("exercises.json") as f:
    exercises = json.load(f)

# --- Collect filter options ---
muscle_groups = sorted(set(e["muscle_group"] for e in exercises))
equipments = sorted(set(e["equipment"] for e in exercises))
difficulties = sorted(set(e["difficulty"] for e in exercises))

# --- Sidebar filters ---
st.sidebar.header("Filter Exercises")
selected_group = st.sidebar.selectbox("Muscle Group", ["All"] + muscle_groups)
selected_equipment = st.sidebar.selectbox("Equipment", ["All"] + equipments)
selected_difficulty = st.sidebar.selectbox("Difficulty", ["All"] + difficulties)

# --- Apply filters ---
filtered = [
    e for e in exercises
    if (selected_group == "All" or e["muscle_group"] == selected_group) and
       (selected_equipment == "All" or e["equipment"] == selected_equipment) and
       (selected_difficulty == "All" or e["difficulty"] == selected_difficulty)
]

# --- Dropdown to select exercise ---
if not filtered:
    st.warning("No exercises match your filters.")
    st.stop()

selected_exercise = st.sidebar.selectbox("Select an Exercise", [e["name"] for e in filtered])
exercise = next(e for e in filtered if e["name"] == selected_exercise)

# --- Display exercise instructions ---
st.header(exercise["name"])
for i, step in enumerate(exercise["instructions"], 1):
    st.markdown(f"{i}. {step}")

# --- Load and display GIF as video ---
gif_path = exercise["gif_path"]
reader = imageio.get_reader(gif_path)
frames = list(reader)
rgb_frames = [Image.fromarray(f).convert("RGB") for f in frames]

target_duration = 3.0
fps = len(frames) / target_duration

clip = ImageSequenceClip([np.array(f) for f in rgb_frames], fps=fps)
with NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_video:
    clip.write_videofile(tmp_video.name, codec="libx264", audio=False, logger=None)
    tmp_video.seek(0)
    st.video(tmp_video.name)

