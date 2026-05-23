import streamlit as st
import re
import os
import tempfile
import subprocess
from aip import AipSpeech

st.set_page_config(page_title="Live Navigator", page_icon="🎙️")
st.title("Live Navigator - Core Test")
st.write("Upload a replay video, get speech analysis.")

try:
    BAIDU_APP_ID = st.secrets["BAIDU_APP_ID"]
    BAIDU_API_KEY = st.secrets["BAIDU_API_KEY"]
    BAIDU_SECRET_KEY = st.secrets["BAIDU_SECRET_KEY"]
    keys_ready = True
except:
    st.error("Keys not configured")
    keys_ready = False

keywords = {
    "risk": ["not", "dont know", "wait", "that that", "I I I"],
    "trust": ["clean", "show you", "what you get", "no difference"],
    "action": ["take a look", "grab it", "order now"]
}

def extract_audio(video_path, out_wav):
    subprocess.run(["ffmpeg", "-i", video_path, "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", "-y", out_wav], check=True, capture_output=True)

def get_duration(wav_path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", wav_path], capture_output=True, text=True)
    return float(r.stdout.strip())

def split_wav(wav_path, chunk_sec=55):
    dur = get_duration(wav_path)
    chunks = []
    base = tempfile.mkdtemp()
    for s in range(0, int(dur), chunk_sec):
        p = os.path.join(base, f"c_{s}.wav")
        subprocess.run(["ffmpeg", "-i", wav_path, "-ss", str(s), "-t", str(chunk_sec), "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", "-y", p], check=True, capture_output=True)
        chunks.append(p)
    return chunks

def recognize_audio(wav_path):
    client = AipSpeech(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)
    chunks = split_wav(wav_path, 55)
    full_text = []
    prog = st.progress(0)
    stat = st.empty()
    for i, c in enumerate(chunks):
        d = get_duration(c)
        stat.markdown(f"Recognizing chunk {i+1}/{len(chunks)} ({d:.1f}s)")
        with open(c, "rb") as f:
            data = f.read()
        res = client.asr(data, 'wav', 16000, {'dev_pid': 1537})
        if res['err_no'] == 0:
            full_text.append(res['result'][0])
        else:
            st.warning(f"Chunk {i+1} failed: {res['err_msg']}")
        prog.progress((i+1)/len(chunks))
        os.unlink(c)
    if chunks:
        os.rmdir(os.path.dirname(chunks[0]))
    stat.markdown("Transcription complete")
    return "".join(full_text)

def analyze_text(text):
    stats = {}
    for cat, words in keywords.items():
        stats[cat] = {}
        for w in words:
            stats[cat][w] = {"count": len([m.start() for m in re.finditer(w, text)])}
    score = sum(
        -info["count"]*2 if "risk" in cat else info["count"]*1
        for cat, wd in stats.items()
        for info in wd.values()
    )
    total = len(text.replace(" ", ""))
    health = max(0, min(100, 50 + (score/total)*1000)) if total > 0 else 50
    return stats, health

video_file = st.file_uploader("Upload mp4", type=["mp4"])

if video_file and keys_ready:
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_file.read())
        vpath = tmp.name
    st.info("Processing...")
    try:
        apath = tempfile.mktemp(suffix=".wav")
        extract_audio(vpath, apath)
        text = recognize_audio(apath)
        st.success("Transcription ready, editable")
        edited = st.text_area("Text", value=text, height=200)
        if st.button("Analyze") and edited:
            stats, health = analyze_text(edited)
            st.subheader("Speech Energy")
            c1, c2, c3 = st.columns(3)
            c1.metric("Risk", sum(stats["risk"][w]["count"] for w in stats["risk"]))
            c2.metric("Trust", sum(stats["trust"][w]["count"] for w in stats["trust"]))
            c3.metric("Action", sum(stats["action"][w]["count"] for w in stats["action"]))
            if health >= 60: st.success(f"Energy {health:.0f}/100 Stable")
            elif health >= 30: st.warning(f"Energy {health:.0f}/100 Warning")
            else: st.error(f"Energy {health:.0f}/100 Critical")
            st.subheader("Word Stats")
            for cat, wd in stats.items():
                st.write(f"**{cat}**")
                for w, i in wd.items():
                    if i["count"] > 0: st.write(f"  - {w}: {i['count']}")
            st.subheader("Advice")
            rc = sum(stats["risk"][w]["count"] for w in stats["risk"])
            tc = sum(stats["trust"][w]["count"] for w in stats["trust"])
            if rc > tc*3:
                st.warning("Too many filler words. Prepare a script.")
            else:
                st.success("Good job!")
        os.unlink(vpath)
        os.unlink(apath)
    except Exception as e:
        st.error(f"Error: {e}")
