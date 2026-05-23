import streamlit as st
import streamlit.components.v1 as components
import re
import os
import tempfile
from pydub import AudioSegment
from aip import AipSpeech

# -------------------- 粒子光感背景特效 --------------------
particle_js = """
<script>
// 粒子光感网络 - 贾维斯背景
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');
canvas.style.position = 'fixed';
canvas.style.top = '0';
canvas.style.left = '0';
canvas.style.width = '100%';
canvas.style.height = '100%';
canvas.style.zIndex = '-1';
canvas.style.background = 'radial-gradient(circle at 20% 30%, #0a0f1e, #03050a)';
document.body.appendChild(canvas);

let width, height, particles;
const maxParticles = 80;
const connectionDist = 120;
const mouse = { x: -1000, y: -1000 };

function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
}

class Particle {
    constructor() {
        this.reset();
        this.y = Math.random() * height;
    }
    reset() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * 0.6;
        this.vy = (Math.random() - 0.5) * 0.6;
        this.radius = Math.random() * 2.5 + 1;
        this.opacity = Math.random() * 0.5 + 0.3;
    }
    update() {
        // 鼠标轻微吸引效果
        const dx = mouse.x - this.x;
        const dy = mouse.y - this.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 200 && dist > 0) {
            this.vx += dx / dist * 0.02;
            this.vy += dy / dist * 0.02;
        }
        this.x += this.vx;
        this.y += this.vy;
        // 边界反弹
        if (this.x < 0 || this.x > width) this.vx *= -1;
        if (this.y < 0 || this.y > height) this.vy *= -1;
        // 阻力
        this.vx *= 0.998;
        this.vy *= 0.998;
    }
    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 242, 254, ${this.opacity})`;
        ctx.fill();
        // 光晕
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius * 3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 242, 254, ${this.opacity * 0.15})`;
        ctx.fill();
    }
}

function init() {
    resize();
    particles = [];
    for (let i = 0; i < maxParticles; i++) {
        particles.push(new Particle());
    }
}

function drawLines() {
    for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < connectionDist) {
                ctx.beginPath();
                ctx.moveTo(particles[i].x, particles[i].y);
                ctx.lineTo(particles[j].x, particles[j].y);
                ctx.strokeStyle = `rgba(0, 242, 254, ${0.12 * (1 - dist/connectionDist)})`;
                ctx.lineWidth = 0.8;
                ctx.stroke();
            }
        }
    }
}

function animate() {
    ctx.clearRect(0, 0, width, height);
    particles.forEach(p => {
        p.update();
        p.draw();
    });
    drawLines();
    requestAnimationFrame(animate);
}

window.addEventListener('resize', () => {
    resize();
    particles.forEach(p => p.reset());
});

window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
});

init();
animate();
</script>
"""

# 注入粒子特效
components.html(particle_js, height=0, width=0)

# -------------------- 贾维斯风格全局CSS --------------------
st.markdown("""
<style>
    /* 界面置于粒子层上方 */
    .stApp {
        background: transparent !important;
        position: relative;
        z-index: 1;
    }
    
    .main > div {
        background: rgba(5, 10, 25, 0.7);
        backdrop-filter: blur(8px);
        border-radius: 18px;
        padding: 20px;
        margin: 10px;
    }
    
    /* 标题发光 */
    h1 {
        color: #00f2fe;
        text-shadow: 0 0 15px #00f2fe, 0 0 30px #0066ff;
        font-weight: 900;
        letter-spacing: 4px;
        font-family: 'Courier New', monospace;
    }
    
    /* 卡片半透明效果 */
    .stFileUploader, .stTextArea, .stButton, .stMetric, .stInfo, .stSuccess, .stWarning, .stError {
        background: rgba(10, 20, 40, 0.7) !important;
        backdrop-filter: blur(10px);
        border: 1px solid #00f2fe40;
        border-radius: 12px;
        box-shadow: 0 0 20px #00f2fe20;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #003366, #001a33);
        color: #00f2fe;
        border: 1px solid #00f2fe;
        border-radius: 8px;
        font-weight: bold;
        letter-spacing: 2px;
        transition: all 0.3s ease;
        text-transform: uppercase;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #004080, #00264d);
        border-color: #00ffcc;
        box-shadow: 0 0 25px #00f2fe;
        color: #00ffcc;
    }
    
    .stFileUploader {
        border: 2px dashed #00f2fe;
        background: rgba(0, 40, 70, 0.3);
    }
    
    textarea {
        background: #0a1220 !important;
        color: #00ffcc !important;
        border: 1px solid #00f2fe !important;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #00f2fe, #0066ff) !important;
    }
    
    .stMetric {
        background: rgba(0, 20, 50, 0.7);
        border-left: 3px solid #00f2fe;
    }
    
    footer {visibility: hidden;}
    .stCaption {
        color: #4a6a8a;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# -------------------- 页面配置 --------------------
st.set_page_config(page_title="直播领航员", page_icon="🛡️")
st.title("直播领航员")
st.markdown("**上传直播录屏 · 自动战术分析 · 话术能量评分**")
st.markdown("---")

# 密钥从Secrets加载
try:
    BAIDU_APP_ID = st.secrets["BAIDU_APP_ID"]
    BAIDU_API_KEY = st.secrets["BAIDU_API_KEY"]
    BAIDU_SECRET_KEY = st.secrets["BAIDU_SECRET_KEY"]
    keys_ready = True
except:
    st.error("🔐 核心密钥未配置，请联系管理员")
    keys_ready = False

# 关键词库
keywords = {
    "🔴 流失风险": ["不是", "不知道", "怎么说呢", "等会儿", "那个那个", "我我我"],
    "🟢 信任建立": ["干干净净", "给你们看", "收到什么样", "挑出来", "没有区别"],
    "🟡 行动号召": ["可以看看", "喜欢就拍", "直接带", "多少钱"]
}

# -------------------- 音频识别引擎 --------------------
def recognize_audio(audio_path):
    client = AipSpeech(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)
    sound = AudioSegment.from_file(audio_path).set_channels(1).set_frame_rate(16000)
    chunk_length = 55 * 1000
    chunks = [sound[i:i+chunk_length] for i in range(0, len(sound), chunk_length)]
    full_text = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    for idx, chunk in enumerate(chunks):
        status_text.markdown(f"🔍 **分析音频片段 {idx+1}/{len(chunks)}** （{len(chunk)/1000:.1f}s）")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            chunk.export(tmp.name, format="wav")
            with open(tmp.name, "rb") as f:
                audio_data = f.read()
            os.unlink(tmp.name)
        result = client.asr(audio_data, 'wav', 16000, {'dev_pid': 1537})
        if result['err_no'] == 0:
            full_text.append(result['result'][0])
        else:
            st.warning(f"⚠️ 片段 {idx+1} 识别异常：{result['err_msg']}")
        progress_bar.progress((idx+1)/len(chunks))
    status_text.markdown("✅ **语音转录完成**")
    return "".join(full_text)

# -------------------- 话术分析核心 --------------------
def analyze_text(text):
    stats = {}
    for cat, words in keywords.items():
        stats[cat] = {}
        for w in words:
            stats[cat][w] = {"count": len([m.start() for m in re.finditer(w, text)])}
    score = sum(
        -info["count"]*2 if "流失" in cat else info["count"]*1
        for cat, word_dict in stats.items()
        for info in word_dict.values()
    )
    total = len(text.replace(" ", ""))
    health = max(0, min(100, 50 + (score/total)*1000)) if total > 0 else 50
    return stats, health

# -------------------- 主界面 --------------------
col1, col2 = st.columns([3,1])
with col1:
    st.markdown("### 📤 上传战场录像")
    video_file = st.file_uploader("", type=["mp4"], label_visibility="collapsed")
with col2:
    st.markdown("### ⚡ 系统状态")
    if keys_ready:
        st.markdown("🟢 **核心在线**")
    else:
        st.markdown("🔴 **密钥缺失**")

if video_file and keys_ready:
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(video_file.read())
        video_path = tmp.name
    
    st.markdown("---")
    st.info("🧠 **正在提取音频并启动语音识别...**")
    try:
        sound = AudioSegment.from_file(video_path).set_channels(1).set_frame_rate(16000)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as at:
            sound.export(at.name, format="wav")
            audio_path = at.name
        
        text = recognize_audio(audio_path)
        st.success("📜 **转录完成，可编辑修正**")
        edited_text = st.text_area("识别文本", value=text, height=200, key="edit_area")
        
        if st.button("🚀 启动战术分析"):
            if edited_text:
                stats, health = analyze_text(edited_text)
                
                st.markdown("---")
                st.subheader("⚡ 话术能量评分")
                c1, c2, c3 = st.columns(3)
                c1.metric("🔴 风险词", sum(stats["🔴 流失风险"][w]["count"] for w in stats["🔴 流失风险"]))
                c2.metric("🟢 信任词", sum(stats["🟢 信任建立"][w]["count"] for w in stats["🟢 信任建立"]))
                c3.metric("🟡 号召词", sum(stats["🟡 行动号召"][w]["count"] for w in stats["🟡 行动号召"]))
                
                if health >= 60:
                    st.success(f"🔋 能量 {health:.0f}/100 —— 话术矩阵稳定")
                elif health >= 30:
                    st.warning(f"⚠️ 能量 {health:.0f}/100 —— 检测到干扰词汇，建议优化")
                else:
                    st.error(f"💀 能量 {health:.0f}/100 —— 话术崩溃风险！立即调整")
                
                st.markdown("### 📊 词汇战术板")
                for cat, wd in stats.items():
                    st.write(f"**{cat}**")
                    for w, i in wd.items():
                        if i["count"] > 0:
                            st.write(f"  · `{w}` ：{i['count']} 次")
                
                st.markdown("### 🧠 贾维斯建议")
                rc = sum(stats["🔴 流失风险"][w]["count"] for w in stats["🔴 流失风险"])
                tc = sum(stats["🟢 信任建立"][w]["count"] for w in stats["🟢 信任建立"])
                if rc > tc*3:
                    st.markdown("""
                    <div style="background:#1a0a0a; border-left:4px solid #ff4444; padding:15px; margin:10px 0;">
                    <strong>⚠️ 话术漏洞警报：</strong> 冗余否定词过多，信任词严重不足。<br>
                    📌 <em>建议立即准备产品手卡，在镜头旁放置「禁词提示器」。</em>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background:#0a1a0a; border-left:4px solid #00ff66; padding:15px; margin:10px 0;">
                    <strong>✅ 战术执行良好：</strong> 话术结构基本健康，继续保持。
                    </div>
                    """, unsafe_allow_html=True)
                
                st.caption("🤖直播领航员 · v3.0 · 人机协同先行者")
        
        os.unlink(video_path)
        os.unlink(audio_path)
    except Exception as e:
        st.error(f"⚠️ 系统异常：{e}")
        st.markdown("可能原因：视频格式不兼容或音频流损坏，请重新录制。")

  
