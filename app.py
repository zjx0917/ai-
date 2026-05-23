import streamlit as st
import streamlit.components.v1 as components
导入re
import os
import tempfile
导入子进程
from aip import AipSpeech

# -------------------- 粒子光感背景特效 --------------------
particle_js = """
<script>
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
        const dx = mouse.x - this.x;
        const dy = mouse.y - this.y;
        const dist = Math.sqrt(dx*dx + dy*dy);
        if (dist < 200 && dist > 0) {
            this.vx += dx / dist * 0.02;
            this.vy += dy / dist * 0.02;
        }
        this.x += this.vx;
        this.y += this.vy;
如果 (this.x < 0 或 this.x > 宽度) this.vx *= -1;
        if (this.y < 0 || this.y > height) this.vy *= -1;
        this.vx *= 0.998;
        this.vy *= 0.998;
    }
    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(0, 242, 254, ${this.opacity})`;
        ctx.fill();
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

components.html(particle_js, height=0, width=0)

# -------------------- 贾维斯风格全局CSS --------------------
st.markdown("""
<style>
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
    h1 {
        color: #00f2fe;
        text-shadow: 0 0 15px #00f2fe, 0 0 30px #0066ff;
        font-weight: 900;
        letter-spacing: 4px;
        font-family: 'Courier New', monospace;
    }
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

st.set_page_config(page_title="直播领航员", page_icon="🛡️")
st.title("直播领航员")
st.markdown("**上传直播录屏 · 自动战术分析 · 话术能量评分**")
st.markdown("---")

try:
    BAIDU_APP_ID = st.secrets["BAIDU_APP_ID"]
    BAIDU_API_KEY = st.secrets["BAIDU_API_KEY"]
    BAIDU_SECRET_KEY = st.secrets["BAIDU_SECRET_KEY"]
    keys_ready = True
except:
    st.error("🔐 核心密钥未配置，请联系管理员")
    keys_ready = False

keywords = {
    "🔴 流失风险": ["不是", "不知道", "怎么说呢", "等会儿", "那个那个", "我我我"],
    "🟢 信任建立": ["干干净净", "给你们看", "收到什么样", "挑出来", "没有区别"],
    "🟡 行动号召": ["可以看看", "喜欢就拍", "直接带", "多少钱"]
}

# -------------------- 音频处理（ffmpeg）--------------------
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
        stat.markdown(f"🔍 **识别片段 {i+1}/{len(chunks)}**（{d:.1f}s）")
        with open(c, "rb") as f:
            data = f.read()
        res = client.asr(data, 'wav', 16000, {'dev_pid': 1537})
        if res['err_no'] == 0:
            full_text.append(res['result'][0])
        else:
            st.warning(f"片段{i+1}识别失败：{res['err_msg']}")
        prog.progress((i+1)/len(chunks))
        os.unlink(c)
    if chunks:
        os.rmdir(os.path.dirname(chunks[0]))
    stat.markdown("✅ **转录完成**")
    return "".join(full_text)

def analyze_text(text):
    stats = {}
    for cat, words in keywords.items():
        stats[cat] = {}
        forw在词:
            stats[cat][w] = {"count": len([m.start() for m in re.finditer(w, text)])}
分数 =总和(
-info["count"]*2如果"流失"在分类中则info1
        for cat, wd in stats.items()
        用于信息在wd。值()
    )
总长度 =len(text.replace(" ", ""))
健康 =max(0, min(100, 50 + (分数/总分)*1000)) 如果总分 > 00 否则 50
    返回stats, health

col1, col2 = st.columns([3,1])
列1:
    st.markdown("### 📤 上传录像")
    video_file = st.file_uploader("", type=["mp4"], label_visibility="collapsed")
with col2:
    st.markdown("### ⚡ 状态")
    如果密钥就绪：
        st.markdown"🟢 在线")
    否则:
        st.markdown("🔴 离网")

if video_file and keys_ready:
    使用tempfile.NamedTemporaryFile(".mp4", delete=False) 作为tmp:
        tmp.write(video_file.read())
        vpath = tmp.name
st.info(“处理中...”)
    尝试:
        apath = tempfile.mktemp(suffix=".wav")
        extract_audio(vpath, apath)
        text = recognize_audio(apath)
        st.success("📜 转录完成，可编辑")
编辑 = st.(“识别文本”, value=文本, 高度=200)
        如果st.按钮(“开始分析”) 且编辑:
统计数据，健康 =(已编辑)
小标题(“⚡ 话术能量”)
            c1, c2, c3 = st.columns(3)
c1.度量, 求和(统计["流失风险"][权重]["计数"] 按权重在统计["流失风险"
            c2.metric("🟢信任", sum(stats["🟢 信任建立"][w]["count"] for w in stats["🟢 信任建立"]))
c3.指标, 总和(统计[" 行动号召"][w]["计数"] 用于w在统计[" 行动号召"
            如果健康 >=60
圣.成功f" {健康:}/100 稳定")
            如果健康 >=30:
(f"⚠️{健康:
            否则:
                st.error(f"💀 {health:.0f}/100 危险")
对于猫，wd在统计。项中
                st.write(f"**{cat}**")
                 w, i in wd.items():
                    如果i[“count”] > 0:
                        st.write(f"  · {w}：{i['count']}次")
            st.markdown("### 🧠 建议")
            rc = sum(stats["🔴 流失风险"][w]["count"] for w in stats["🔴 流失风险"])
            tc = sum(stats["🟢 信任建立"][w]["count"] for w in stats["🟢 信任建立"])
            如果rc > tc*
                st.markdown("<div style='background:#1a0a0a;border-left:4px solid #f44;padding:15px;'><strong>⚠️ 风险：</strong>废话过多，准备手卡。</div>", unsafe_allow_html=True)
            否则:
圣。标记(, unsafe_allow_html=True)
            st.caption("直播领航员 · v3.0")
        os.unlink(vpath)
        os.unlink(apath)
    except异常ase:
st.error(f"异常：{e}")

    
   

  
