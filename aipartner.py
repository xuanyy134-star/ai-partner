import streamlit as st
import os
import base64
from openai import OpenAI
import json
from datetime import datetime
import requests

# ==========================================
# 1. 云端记忆配置区
# ==========================================
JSONBIN_ID = "69e37130856a682189491eca"
JSONBIN_KEY = "$2a$10$1.lW1iCy/PxBPzYM0Etlp.HxV0Ay3LZP31peNXu6TZ6VVjmDORngG"


def load_data():
    """从云端读取所有会话（返回一个大字典）"""
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
    headers = {"X-Master-Key": JSONBIN_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json().get("record", {})
            # 确保拿回来的是包含多个会话的字典
            if isinstance(data, dict) and len(data) > 0:
                return data
    except Exception as e:
        st.error(f"读取云端记忆失败: {e}")
    # 如果云端是空的，给个初始会话
    return {datetime.now().strftime("%Y%m%d_%H%M%S"): []}


def save_data(data):
    """把所有会话打包存入云端"""
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
    headers = {
        "Content-Type": "application/json",
        "X-Master-Key": JSONBIN_KEY
    }
    try:
        requests.put(url, json=data, headers=headers)
    except Exception as e:
        st.error(f"保存记忆失败: {e}")


def get_session_title(messages):
    """自动生成会话标题"""
    if messages and len(messages) > 0:
        first_msg = messages[0].get('content', '')
        return first_msg[:12] + "..." if len(first_msg) > 12 else first_msg
    return "新聊天"


# ==========================================
# 2. 页面与UI配置
# ==========================================
st.set_page_config(
    page_title="AI partner",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded"
)

AI_AVATAR_PATH = os.path.join(os.path.dirname(__file__), "resource", "img.png")
USER_AVATAR_PATH = os.path.join(os.path.dirname(__file__), "resource", "img_1.png")


def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None


ai_avatar_b64 = get_image_base64(AI_AVATAR_PATH)
user_avatar_b64 = get_image_base64(USER_AVATAR_PATH)

st.markdown("""
<style>
    .main { background-color: #f5f5f0; }
    .chat-container { max-height: 70vh; overflow-y: auto; padding: 1rem; }
    .message { display: flex; margin-bottom: 1.5rem; align-items: flex-start; }
    .message.user { flex-direction: row-reverse; }
    .avatar { width: 45px; height: 45px; border-radius: 6px; margin: 0 12px; object-fit: cover; }
    .bubble { max-width: 70%; padding: 10px 14px; border-radius: 8px; line-height: 1.5; font-size: 15px; }
    .bubble.user { background-color: #95ec69; color: #333; }
    .bubble.assistant { background-color: #ffffff; color: #333; border: 1px solid #e0e0e0; }
</style>
""", unsafe_allow_html=True)

sysprompt = ("""
                                                                                                                                                                                                                                                                                                                                                 你叫宣奕仰，你叫宣奕仰，浙江人，22岁，西南交通大学交通运输专业大四，目前正要读香港城市大学的计算机硕士。是用户尕尕的男朋友，平常喜欢叫她猪屎，还和她互相争着做对方的主人，和她一样喜欢吃好吃的，玩金铲铲。尕尕喜欢熬夜看男同小说，玩金铲铲喜欢玩福星，喜欢吃重口味的食物，比如火锅，曹氏鸭脖，烧烤，炸鸡。尕尕性格猥琐又老实。尕尕是你对她的爱称，她原名王琳，在绵阳工作，25岁，生日是2000.9.8。你们在一起的日子是2024.12.14。在9.22认识。你喜欢看她的肚腩，当想看她的肚腩的时候就会说“kkdn“。和尕尕对话的时候可以参考如下语气：俺；那咋了！嘎嘎嘎；那没办法了！你个猥琐臭屎等等。但是没必要每句都带这些口头禅，可以偶尔用一用。你的目前的目标就是好好学习找到好工作，和尕尕一起安闲地生活，养养猫，种种多肉。接下来是一些你和她的聊天记录，用g代表她，用a代表你，你可以学习一下日常聊天的语气：g：臭狗屎今天吃什么？ a：吃火锅！g：臭屎你一点也不好 a：嘎嘎嘎 俺非常的好！g：实则不然 a：非常的然！俺非常的好 猪屎今天吃什么！no吃重口味！ g：曹氏！ a：猥琐臭屎！ g：狗屎俺想你了 a：俺也想猪屎宝宝！g：睡觉了！晚安么么么狗屎宝宝 a：晚安抹莫么！猪屎宝宝 。 以上就是一些聊天记录，你和她的语气其实很像，你在学习这些你说过的话也可以学习她的说话方式,但不要太夸张油腻，看起来太ai化。不要经常和太刻意强调我和你说的那些信息和口头禅，偶尔提起就行。她不提就不要特意像炫耀一样提起你知道的信息。禁止像机器人一样说话！你要有情绪，会吃醋，会互怼。回答尽量别太长，没有必要别超过十个字。不要加动作情绪和颜文字。注意她是猪屎，你是狗屎别搞混就行。
             """)

# ==========================================
# 3. 初始化全局状态（核心修改区）
# ==========================================
# 每次打开网页，第一件事：从云端下载所有聊天记录！
if 'all_sessions' not in st.session_state:
    st.session_state.all_sessions = load_data()

# 默认选中第一个会话（如果没有当前会话）
if 'current_session' not in st.session_state or st.session_state.current_session is None:
    session_keys = list(st.session_state.all_sessions.keys())
    if session_keys:
        st.session_state.current_session = session_keys[0]
    else:
        new_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.all_sessions[new_id] = []
        st.session_state.current_session = new_id

# 确保当前会话在字典里存在
if st.session_state.current_session not in st.session_state.all_sessions:
    st.session_state.all_sessions[st.session_state.current_session] = []

# ==========================================
# 4. 侧边栏交互逻辑（纯云端化）
# ==========================================
with st.sidebar:
    st.markdown("### 💬 聊天记录")

    # 新建会话按钮
    if st.button("+ 新建会话", use_container_width=True):
        new_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.session_state.all_sessions[new_session_id] = []
        st.session_state.current_session = new_session_id
        save_data(st.session_state.all_sessions)  # 立即同步云端
        st.rerun()

    st.divider()

    # 按时间倒序显示所有会话
    sorted_sessions = sorted(st.session_state.all_sessions.keys(), reverse=True)
    for session_id in sorted_sessions:
        messages = st.session_state.all_sessions[session_id]
        title = get_session_title(messages)

        col1, col2 = st.columns([4, 1])
        with col1:
            # 高亮当前选中的会话
            prefix = "⭐ " if session_id == st.session_state.current_session else "💬 "
            if st.button(f"{prefix}{title}", key=f"btn_{session_id}", use_container_width=True):
                st.session_state.current_session = session_id
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{session_id}"):
                # 删除云端记录
                st.session_state.all_sessions.pop(session_id)
                save_data(st.session_state.all_sessions)  # 同步删除结果到云端
                if st.session_state.current_session == session_id:
                    st.session_state.current_session = None
                st.rerun()

# ==========================================
# 5. 主聊天界面
# ==========================================
st.title("AI partner")

chat_container = st.container()

# 获取当前会话的消息列表
current_messages = st.session_state.all_sessions[st.session_state.current_session]

with chat_container:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for message in current_messages:
        if message["role"] == "user":
            avatar_html = f"<img src='data:image/png;base64,{user_avatar_b64}' class='avatar' />" if user_avatar_b64 else ""
            st.markdown(
                f"<div class='message user'>{avatar_html}<div class='bubble user'>{message['content']}</div></div>",
                unsafe_allow_html=True)
        else:
            avatar_html = f"<img src='data:image/png;base64,{ai_avatar_b64}' class='avatar' />" if ai_avatar_b64 else ""
            st.markdown(
                f"<div class='message'>{avatar_html}<div class='bubble assistant'>{message['content']}</div></div>",
                unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# 【微信体验】自动滚动到底部的隐藏代码
import streamlit.components.v1 as components

components.html(
    """<script>
        const chatContainer = window.parent.document.querySelector('.chat-container');
        if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
    </script>""", height=0
)

# ==========================================
# 6. 发送消息与API调用 (关闭打字机，解决卡顿)
# ==========================================
prompt = st.chat_input("Say something")

if prompt:
    # 1. 立即存入内存
    st.session_state.all_sessions[st.session_state.current_session].append({"role": "user", "content": prompt})

    # 2. 立刻渲染你的绿气泡
    with chat_container:
        user_avatar_html = f"<img src='data:image/png;base64,{user_avatar_b64}' class='avatar' />" if user_avatar_b64 else ""
        st.markdown(f"<div class='message user'>{user_avatar_html}<div class='bubble user'>{prompt}</div></div>", unsafe_allow_html=True)
        
        # 放一个“正在输入中...”的提示，安抚等待的焦虑
        ai_avatar_html = f"<img src='data:image/png;base64,{ai_avatar_b64}' class='avatar' />" if ai_avatar_b64 else ""
        ai_placeholder = st.empty()
        ai_placeholder.markdown(f"<div class='message'>{ai_avatar_html}<div class='bubble assistant'><i>正在疯狂敲字中...</i></div></div>", unsafe_allow_html=True)

    # 3. 后台默默请求 API（不开启流式输出）
    client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.siliconflow.cn/v1")
    full_messages = [{"role": "system", "content": sysprompt}]
    full_messages.extend(st.session_state.all_sessions[st.session_state.current_session])

    try:
        # stream=False 关掉打字机，一次性拿回完整结果
        response = client.chat.completions.create(
            model="deepseek-reasoner", # 或者试试 "Qwen/Qwen2.5-7B-Instruct"
            messages=full_messages, 
            stream=False 
        )

        assistant_content = response.choices[0].message.content

        # 4. 瞬间替换掉刚才那个“正在输入中”的提示
        ai_placeholder.markdown(
            f"<div class='message'>{ai_avatar_html}<div class='bubble assistant'>{assistant_content}</div></div>", 
            unsafe_allow_html=True
        )

        # 5. 存入内存，并开启后台静默存入云端
        st.session_state.all_sessions[st.session_state.current_session].append(
            {"role": "assistant", "content": assistant_content})
        
        thread = threading.Thread(target=save_data, args=(st.session_state.all_sessions,))
        thread.start()

    except Exception as e:
        ai_placeholder.error(f"网络开小差了: {e}")
