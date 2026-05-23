import streamlit as st
import re
import os
import tempfile
import subprocess
from aip import AipSpeech

st.set_page_config(page_title="直播领航员", page_icon="🎙️")
st.title("直播领航员 · 话术诊断")
st.write("上传直播录屏，自动识别并生成话术质量报告。可在侧边栏自定义关键词。")

# -------------------- 自定义关键词（默认中文） --------------------
st.sidebar.header("自定义关键词")
st.sidebar.caption("多个词请用逗号分隔，留空则使用默认词库")

默认风险词 = "不是, 不知道, 怎么说呢, 等会儿, 那个那个, 我我我"
默认信任词 = "干干净净, 给你们看, 收到什么样, 挑出来, 没有区别"
默认行动词 = "可以看看, 喜欢就拍, 直接带, 多少钱"

用户风险词 = st.sidebar.text_area("风险词（口癖/犹豫词）", value=默认风险词, height=100)
用户信任词 = st.sidebar.text_area("信任词（品质/展示）", value=默认信任词, height=100)
用户行动词 = st.sidebar.text_area("行动词（促单/引导）", value=默认行动词, height=100)

def 解析词表(文本):
    return [w.strip() for w in 文本.replace("，", ",").split(",") if w.strip()]

关键词库 = {
    "风险": 解析词表(用户风险词),
    "信任": 解析词表(用户信任词),
    "行动": 解析词表(用户行动词)
}

# -------------------- 密钥加载 --------------------
try:
    BAIDU_APP_ID = st.secrets["BAIDU_APP_ID"]
    BAIDU_API_KEY = st.secrets["BAIDU_API_KEY"]
    BAIDU_SECRET_KEY = st.secrets["BAIDU_SECRET_KEY"]
    密钥就绪 = True
except:
    st.error("密钥未配置，请联系管理员。")
    密钥就绪 = False

# -------------------- 音频处理 --------------------
def 提取音频(视频路径, 输出音频路径):
    subprocess.run(["ffmpeg", "-i", 视频路径, "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", "-y", 输出音频路径],
                   check=True, capture_output=True)

def 获取时长(音频路径):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", 音频路径],
                       capture_output=True, text=True)
    return float(r.stdout.strip())

def 切分音频(音频路径, 每段秒数=55):
    总时长 = 获取时长(音频路径)
    片段列表 = []
    临时目录 = tempfile.mkdtemp()
    for 起始秒 in range(0, int(总时长), 每段秒数):
        片段路径 = os.path.join(临时目录, f"c_{起始秒}.wav")
        subprocess.run(["ffmpeg", "-i", 音频路径, "-ss", str(起始秒), "-t", str(每段秒数),
                        "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", "-y", 片段路径],
                       check=True, capture_output=True)
        片段列表.append(片段路径)
    return 片段列表

def 语音识别(音频路径):
    客户端 = AipSpeech(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)
    片段列表 = 切分音频(音频路径, 55)
    全部文本 = []
    进度条 = st.progress(0)
    状态文字 = st.empty()
    for 序号, 片段 in enumerate(片段列表):
        时长 = 获取时长(片段)
        状态文字.markdown(f"正在识别第 {序号+1}/{len(片段列表)} 段（{时长:.1f}秒）")
        with open(片段, "rb") as f:
            音频数据 = f.read()
        结果 = 客户端.asr(音频数据, 'wav', 16000, {'dev_pid': 1537})
        if 结果['err_no'] == 0:
            全部文本.append(结果['result'][0])
        else:
            st.warning(f"第{序号+1}段识别失败：{结果['err_msg']}")
        进度条.progress((序号+1)/len(片段列表))
        os.unlink(片段)
    if 片段列表:
        os.rmdir(os.path.dirname(片段列表[0]))
    状态文字.markdown("语音识别完成")
    return "".join(全部文本)

# -------------------- 分析核心 --------------------
def 分析文本(文本):
    统计 = {}
    for 类别, 词列表 in 关键词库.items():
        统计[类别] = {}
        for 词 in 词列表:
            统计[类别][词] = {"次数": len([m.start() for m in re.finditer(词, 文本)])}
    得分 = sum(
        -信息["次数"]*2 if "风险" in 类别 else 信息["次数"]*1
        for 类别, 词字典 in 统计.items()
        for 信息 in 词字典.values()
    )
    总字数 = len(文本.replace(" ", ""))
    健康分 = max(0, min(100, 50 + (得分/总字数)*1000)) if 总字数 > 0 else 50
    return 统计, 健康分

# -------------------- 主界面 --------------------
上传文件 = st.file_uploader("上传直播录屏（mp4）", type=["mp4"])

if 上传文件 and 密钥就绪:
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(上传文件.read())
        视频路径 = tmp.name
    st.info("正在处理，请稍候…")
    try:
        音频路径 = tempfile.mktemp(suffix=".wav")
        提取音频(视频路径, 音频路径)
        识别文本 = 语音识别(音频路径)
        st.success("识别完成，可编辑修正")
        编辑后文本 = st.text_area("识别文本", value=识别文本, height=200)
        if st.button("开始分析") and 编辑后文本:
            统计, 健康分 = 分析文本(编辑后文本)
            风险总数 = sum(统计["风险"][词]["次数"] for 词 in 统计["风险"])
            信任总数 = sum(统计["信任"][词]["次数"] for 词 in 统计["信任"])

            st.subheader("话术能量评分")
            列1, 列2, 列3 = st.columns(3)
            列1.metric("风险词", 风险总数)
            列2.metric("信任词", 信任总数)
            列3.metric("行动词", sum(统计["行动"][词]["次数"] for 词 in 统计["行动"]))
            if 健康分 >= 60:
                st.success(f"能量 {健康分:.0f}/100 —— 话术矩阵稳定")
            elif 健康分 >= 30:
                st.warning(f"能量 {健康分:.0f}/100 —— 检测到干扰词汇，建议优化")
            else:
                st.error(f"能量 {健康分:.0f}/100 —— 话术崩溃风险！")

            st.subheader("词汇统计")
            for 类别, 词字典 in 统计.items():
                st.write(f"**{类别}**")
                for 词, 信息 in 词字典.items():
                    if 信息["次数"] > 0:
                        st.write(f"  - {词}：{信息['次数']}次")

            st.subheader("改进建议")
            if 风险总数 > 信任总数*3:
                st.warning("风险词过多，信任词严重不足。建议准备产品手卡，用具体描述替代口头禅。")
            else:
                st.success("话术结构基本健康，继续保持。")

            # PDF 报告下载
            if st.button("下载 PDF 报告"):
                from fpdf import FPDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)

                pdf.set_font("Arial", style="B", size=16)
                pdf.cell(200, 10, txt="直播领航员 · 话术诊断报告", ln=True, align="C")
                pdf.ln(10)

                pdf.set_font("Arial", size=12)
                pdf.cell(200, 10, txt=f"话术能量评分：{健康分:.0f}/100", ln=True)

                pdf.ln(5)
                pdf.set_font("Arial", style="B", size=12)
                pdf.cell(200, 10, txt="词汇统计：", ln=True)
                pdf.set_font("Arial", size=11)
                类别名称 = {"风险": "风险词", "信任": "信任词", "行动": "行动词"}
                for 类别 in ["风险", "信任", "行动"]:
                    总数 = sum(统计[类别][词]["次数"] for 词 in 统计[类别])
                    pdf.cell(200, 8, txt=f"{类别名称[类别]}：{总数} 次", ln=True)
                    for 词, 信息 in 统计[类别].items():
                        if 信息["次数"] > 0:
                            pdf.cell(200, 8, txt=f"  - {词}：{信息['次数']}次", ln=True)

                pdf.ln(5)
                pdf.set_font("Arial", style="B", size=12)
                pdf.cell(200, 10, txt="改进建议：", ln=True)
                pdf.set_font("Arial", size=11)
                if 风险总数 > 信任总数*3:
                    pdf.multi_cell(0, 8, txt="风险词过多，信任词严重不足。建议准备产品手卡，用具体描述替代口头禅。")
                else:
                    pdf.multi_cell(0, 8, txt="话术结构基本健康，继续保持。")

                临时PDF路径 = tempfile.mktemp(suffix=".pdf")
                pdf.output(临时PDF路径)
                with open(临时PDF路径, "rb") as f:
                    pdf数据 = f.read()
                st.download_button(
                    label="点击下载报告",
                    data=pdf数据,
                    file_name="话术诊断报告.pdf",
                    mime="application/pdf"
                )
                os.unlink(临时PDF路径)

        os.unlink(视频路径)
        os.unlink(音频路径)
    except Exception as e:
        st.error(f"处理出错：{e}")
