import streamlit as st
import numpy as np
import librosa
import soundfile as sf
import io
import plotly.graph_objects as go
from scipy.signal import butter, lfilter
from pydub import AudioSegment

# Audio Filtering Function
def apply_filter(audio, sr, filter_type, cutoff_freq):
    nyquist = 0.5 * sr
    normal_cutoff = cutoff_freq / nyquist
    b, a = butter(4, normal_cutoff, btype=filter_type, analog=False)
    return lfilter(b, a, audio)

# Generate Interactive Audiogram (Optimized)
def generate_audiogram(audio, sr, title="Audiogram Visualization", max_points=5000):
    time = np.linspace(0, len(audio) / sr, num=len(audio))
    
    # Reduce number of points for visualization to avoid exceeding memory limit
    if len(audio) > max_points:
        indices = np.linspace(0, len(audio) - 1, max_points, dtype=int)
        audio = audio[indices]
        time = time[indices]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=time, y=audio, mode="lines", name=title))

    fig.update_layout(
        title=title,
        xaxis_title="Time (s)",
        yaxis_title="Amplitude",
        hovermode="x",
        template="plotly_white",
        height=300,
    )

    # Enable zoom, pan, and fullscreen controls
    fig.update_layout(
        dragmode="zoom", 
        autosize=True,
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis=dict(showspikes=True),
        yaxis=dict(showspikes=True),
    )

    return fig

# Convert uploaded file to WAV if needed
def convert_to_wav(uploaded_file):
 # space
    audio = AudioSegment.from_file(uploaded_file)  # Auto-detect format
#space
    wav_io = io.BytesIO()
#space
    audio.export(wav_io, format="wav")  # Convert to WAV
#space
    wav_io.seek(0)
#space
    return wav_io

# Streamlit UI
st.title("🔊 AudioScope - Audio Processing Tool")

uploaded_file = st.file_uploader("Upload an audio file (WAV/MP3/M4A)", type=["wav", "mp3", "m4a"])

if uploaded_file is not None:
    # Convert file to WAV if necessary
    converted_audio = convert_to_wav(uploaded_file)

    # Load audio with Librosa (Downsample to reduce memory usage)
    audio, sr = librosa.load(converted_audio, sr=16000, mono=True)  # Downsample to 16kHz to reduce data size
    st.audio(uploaded_file, format='audio/wav')

    # Display original audiogram
    st.subheader("Audio Visualizations")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Original Audio Visualization")
        st.plotly_chart(generate_audiogram(audio, sr, title="Original Audio"), use_container_width=True)

    # Filter selection
    filter_type_option = st.selectbox("Choose a filter", ["None", "Low-pass", "High-pass"])
    cutoff_freq = st.slider("Select Cutoff Frequency (Hz)", min_value=100, max_value=5000, step=100, value=1000)

    filter_map = {"Low-pass": "low", "High-pass": "high"}
    filter_type = filter_map.get(filter_type_option, None)

    if filter_type:
        filtered_audio = apply_filter(audio, sr, filter_type, cutoff_freq)
        with col2:
            st.subheader("Filtered Audio Visualization")
            st.plotly_chart(generate_audiogram(filtered_audio, sr, title="Filtered Audio"), use_container_width=True)

        # Convert filtered audio to WAV for playback
        processed_audio_io = io.BytesIO()
        sf.write(processed_audio_io, filtered_audio, sr, format='WAV')
        processed_audio_io.seek(0)

        # Play the processed (filtered) audio
        st.subheader("🎵 Processed Audio Playback")
        st.audio(processed_audio_io, format="audio/wav")
    else:
        filtered_audio = audio

    # Download processed audio
    processed_audio = io.BytesIO()
    sf.write(processed_audio, filtered_audio, sr, format='WAV')
    processed_audio.seek(0)  # Important for download to work
    st.download_button("Download Processed Audio", data=processed_audio, file_name="processed_audio.wav", mime="audio/wav")
