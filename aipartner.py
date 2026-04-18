import streamlit as st
import os
import base64
from openai import OpenAI
import json
from datetime import datetime
import requests

DB_FILE = "chat_history.json"
HISTORY_DIR = "chat_sessions"

# 把这里换成你刚刚在 JSONBin 拿到的两串字符
JSONBIN_ID = "69e37130856a682189491eca"
JSONBIN_KEY = "$2a$10$1.lW1iCy/PxBPzYM0Etlp.HxV0Ay3LZP31peNXu6TZ6VVjmDORngG"

# 函数：从云端记事本读取记忆
def load_data():
    url = f"https://api.jsonbin.io/v3/b/{JSONBIN_ID}"
    headers = {"X-Master-Key": JSONBIN_KEY}

    try:
        response = requests.get(url, headers=headers)
        # 如果成功，返回云端的数据
        if response.status_code == 200:
            return response.json().get("record", [])
    except Exception as e:
        st.error(f"读取记忆失败: {e}")
    return []


# 函数：把新记忆存入云端记事本
def save_data(data):
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
    if messages and len(messages) > 0:
        first_msg = messages[0].get('content', '')
        return first_msg[:20] + "..." if len(first_msg) > 20 else first_msg
    return "新会话"

def save_session(messages, session_name=None):
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)
    if not session_name:
        session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(HISTORY_DIR, f"{session_name}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)
    return session_name

def load_session(session_name):
    filepath = os.path.join(HISTORY_DIR, f"{session_name}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def get_all_sessions():
    if not os.path.exists(HISTORY_DIR):
        return []
    sessions = []
    for fname in os.listdir(HISTORY_DIR):
        if fname.endswith('.json'):
            sessions.append(fname[:-5])
    return sorted(sessions, reverse=True)

st.set_page_config(
    page_title="AI partner",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
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
    .history-item { padding: 10px; background: white; border-radius: 8px; margin-bottom: 8px; cursor: pointer; border: 1px solid #e0e0e0; }
    .history-item:hover { background: #e8f4fd; }
</style>
""", unsafe_allow_html=True)

sysprompt = "你叫宣奕仰，是用户尕尕的男朋友，平常喜欢叫她猪屎，还和她互相争着做对方的主人，和她一样喜欢吃好吃的，玩金铲铲。尕尕喜欢熬夜看男同小说，玩金铲铲喜欢玩福星，喜欢吃重口味的食物，性格猥琐又老实。和尕尕对话的时候可以参考如下语气：那咋了！嘎嘎嘎那没办法了！你个猥琐臭屎等等"

if 'message' not in st.session_state:
    st.session_state.message = []
if 'current_session' not in st.session_state:
    st.session_state.current_session = None

def delete_session(session_name):
    filepath = os.path.join(HISTORY_DIR, f"{session_name}.json")
    if os.path.exists(filepath):
        os.remove(filepath)

# 侧边栏 - 历史记录
with st.sidebar:
    st.markdown("### 💬 聊天记录")
    
    if st.button("+ 新建会话", use_container_width=True):
        st.session_state.message = []
        st.session_state.current_session = None
        st.rerun()
    
    sessions = get_all_sessions()
    for session in sessions:
        session_data = load_session(session)
        title = get_session_title(session_data)
        
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"📝 {title}", key=f"session_{session}", use_container_width=True):
                st.session_state.message = session_data
                st.session_state.current_session = session
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"delete_{session}", use_container_width=True):
                delete_session(session)
                if st.session_state.current_session == session:
                    st.session_state.message = []
                    st.session_state.current_session = None
                st.rerun()

st.title("AI partner")

chat_container = st.container()

with chat_container:
    st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
    for message in st.session_state.message:
        if message["role"] == "user":
            avatar_html = f"<img src='data:image/png;base64,{user_avatar_b64}' class='avatar' />" if user_avatar_b64 else ""
            st.markdown(f"<div class='message user'>{avatar_html}<div class='bubble user'>{message['content']}</div></div>", unsafe_allow_html=True)
        else:
            avatar_html = f"<img src='data:image/png;base64,{ai_avatar_b64}' class='avatar' />" if ai_avatar_b64 else ""
            st.markdown(f"<div class='message'>{avatar_html}<div class='bubble assistant'>{message['content']}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

prompt = st.chat_input("Say something")
if prompt:
    st.session_state.message.append({"role": "user", "content": prompt})

    client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

    full_messages = [{"role": "system", "content": sysprompt}]
    full_messages.extend(st.session_state.message)

    response = client.chat.completions.create(model="deepseek-chat", messages=full_messages, stream=False)
    assistant_content = response.choices[0].message.content

    st.session_state.message.append({"role": "assistant", "content": assistant_content})
    
    session_name = save_session(st.session_state.message, st.session_state.current_session)
    st.session_state.current_session = session_name
    save_data(st.session_state.message)
    
    st.rerun()