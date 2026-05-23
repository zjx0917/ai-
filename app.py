import streamlit as st
import re
import os
import tempfile
import subprocess
from aip import AipSpeech

st.set_page_config(page_title="领航员·直播话术诊断", page_icon="🎙️")
st.title("🎙️ 领航员·直播话术诊断 v3.0")
st.write("上传直播录屏，自动识别并生成话术质量报告——无需填写任何密钥")

try:
    BAIDU_APP_ID = st.secrets["BAIDU_APP_ID"]
    BAIDU_API_KEY = st.secrets["BAIDU_API_KEY"]
    BAIDU_SECRET_KEY = st.secrets["BAIDU_SECRET_KEY"]
    keys_ready = True
except:
    st.error("后端密钥未配置，请联系管理员")
    keys_ready = False

keywords = {
    "流失风险": ["不是", "不知道", "怎么说呢", "等会儿", "那个那个", "我我我"],
    "信任建立": ["干干净净", "给你们看", "收到什么样", "挑出来", "没有区别"],
    "行动号召": ["可以看看", "喜欢就拍", "直接带", "多少钱"]
}

def extract_audio(video_path, audio_path):
    """用 ffmpeg 提取音频为 16kHz 单声道 wav"""
    cmd = [
        "ffmpeg", "-i", video_path,
        "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
        "-y", audio_path
    ]
    subprocess.run(cmd, check=True, capture_output=True)

def recognize_audio(audio_path):
    client = AipSpeech(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)
    # 读取整个音频文件
    with open(audio_path, "rb") as f:
        audio_data = f.read()
    # 如果音频大于60秒，需要切片；这里先简单处理，建议用户上传5分钟以内
    # 为了稳定，直接用短语音接口，如果文件过大可能失败，后续可加切片逻辑
    result = client.asr(audio_data, 'wav', 16000, {'dev_pid': 1537})
    if result['err_no'] == 0:
        return result['result'][0]
    else:
        raise Exception(f"语音识别失败：{result['err_msg']}")

def analyze_text(text):
    stats = {}
    for cat, words in keywords.items():
        stats[cat] = {}
        for w in words:
            stats[cat][w] = {"count": len([m.start() for m in re.finditer(w, text)])}
    score = sum(
        -info["count"]*2 if cat == "流失风险" else info["count"]*1
        for cat, word_dict in stats.items()
        for info in word_dict.values()
    )
    total = len(text.replace(" ", ""))
    health = max(0, min(100, 50 + (score/total)*1000)) if total > 0 else 50
    return stats, health

video_file = st.file_uploader("上传直播录屏（mp4）", type=["mp4"])

if video_file and keys_ready:
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_file.read())
        video_path = tmp.name
    st.info("正在处理，请稍候...")
    try:
        # 提取音频
        audio_path = tempfile.mktemp(suffix=".wav")
        extract_audio(video_path, audio_path)
        # 语音识别
        text = recognize_audio(audio_path)
        st.success("识别完成，可编辑修正后点击分析")
        edited_text = st.text_area("识别结果（可编辑）", value=text, height=200)
        if st.button("开始分析", type="primary") and edited_text:
            stats, health = analyze_text(edited_text)
            st.subheader("话术健康分")
            c1, c2, c3 = st.columns(3)
            c1.metric("流失风险词", sum(stats["流失风险"][w]["count"] for w in stats["流失风险"]))
            c2.metric("信任建立词", sum(stats["信任建立"][w]["count"] for w in stats["信任建立"]))
            c3.metric("行动号召词", sum(stats["行动号召"][w]["count"] for w in stats["行动号召"]))
            if health >= 60:
                st.success(f"{health:.0f}/100 表现良好")
            elif health >= 30:
                st.warning(f"{health:.0f}/100 需要改进")
            else:
                st.error(f"{health:.0f}/100 存在严重问题")
            for cat, wd in stats.items():
                st.write(f"**{cat}**")
                for w, i in wd.items():
                    if i["count"] > 0:
                        st.write(f"  · '{w}'：{i['count']}次")
            st.subheader("改进建议")
            rc = sum(stats["流失风险"][w]["count"] for w in stats["流失风险"])
            tc = sum(stats["信任建立"][w]["count"] for w in stats["信任建立"])
            if rc > tc * 3:
                st.write("核心问题：废话过多，建议准备产品手卡，贴禁词提醒")
            else:
                st.write("话术结构基本健康")
            st.caption("领航员·AI驱动的人机协同直播先行者")
        # 清理临时文件
        os.unlink(video_path)
        os.unlink(audio_path)
    except Exception as e:
        st.error(f"处理失败：{e}")
  
