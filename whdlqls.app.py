import streamlit as st
import requests
import base64
import time
import json
from datetime import datetime, timezone, timedelta
import extra_streamlit_components as stx

# ------------------------------------------------------------------
# 1. 페이지 기본 설정 및 시간 설정
# ------------------------------------------------------------------
st.set_page_config(page_title="일상 저장소", page_icon="📸", layout="wide")
KST = timezone(timedelta(hours=9))

cookie_manager = stx.CookieManager(key="cookie_manager")

if "favorites" not in st.session_state:
    st.session_state["favorites"] = set()

# ------------------------------------------------------------------
# 2. Secrets 토큰 및 사용자 설정
# ------------------------------------------------------------------
if "GITHUB_TOKEN" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 'GITHUB_TOKEN'이 설정되어 있지 않습니다!")
    st.stop()

GITHUB_TOKEN = str(st.secrets["GITHUB_TOKEN"]).strip()
REPO_OWNER = "TDequalMa"
REPO_NAME = "Memory_Archive"

api_headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ------------------------------------------------------------------
# 3. 깃허브 API 연동 함수들 (파일 & 댓글)
# ------------------------------------------------------------------
def fetch_github_files():
    timestamp = int(time.time())
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/uploads?t={timestamp}"
    response = requests.get(url, headers=api_headers)
    if response.status_code == 200:
        return response.json()
    return []

def delete_github_file(file_path, sha, file_name):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    data = {
        "message": f"Delete {file_name} via Streamlit",
        "sha": sha
    }
    response = requests.delete(url, headers=api_headers, json=data)
    return response.status_code == 200

# ⭐ 댓글 불러오기
def fetch_comments():
    timestamp = int(time.time())
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/comments.json?t={timestamp}"
    res = requests.get(url, headers=api_headers)
    if res.status_code == 200:
        content = res.json()
        decoded = base64.b64decode(content['content']).decode('utf-8')
        try:
            return json.loads(decoded), content['sha']
        except json.JSONDecodeError:
            return {}, content['sha']
    return {}, None

# ⭐ 댓글 저장하기
def add_comment(file_sha, author, text):
    comments_dict, sha = fetch_comments()
    if file_sha not in comments_dict:
        comments_dict[file_sha] = []
    
    now_str = datetime.now(KST).strftime("%m/%d %H:%M")
    comments_dict[file_sha].append({
        "author": author,
        "text": text,
        "time": now_str
    })
    
    updated_json = json.dumps(comments_dict, ensure_ascii=False, indent=2)
    encoded_content = base64.b64encode(updated_json.encode('utf-8')).decode('utf-8')
    
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/comments.json"
    payload = {
        "message": f"Add comment by {author}",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha
        
    res = requests.put(url, headers=api_headers, json=payload)
    return res.status_code in [200, 201]

# ------------------------------------------------------------------
# 4. 쿠키 및 세션 동기화 처리
# ------------------------------------------------------------------
if "user_nickname" not in st.session_state or not st.session_state["user_nickname"]:
    saved_cookie = cookie_manager.get(cookie="user_nickname")
    if saved_cookie:
        st.session_state["user_nickname"] = saved_cookie

user_nickname = st.session_state.get("user_nickname")

if not user_nickname:
    st.title("📸 일상 저장소에 오신 것을 환영합니다!")
    st.info("👋 처음 접속하셨네요! 사이트에서 사용할 닉네임을 설정해주세요.")
    
    input_nick = st.text_input("✍️ 닉네임 입력 (최대 10자)", max_chars=10)
    
    if st.button("입장하기", type="primary"):
        if input_nick.strip():
            clean_nick = input_nick.strip().replace(" ", "_")
            cookie_manager.set("user_nickname", clean_nick, key="set_nick")
            st.session_state["user_nickname"] = clean_nick
            st.success(f"🎉 환영합니다, '{clean_nick}'님!")
            time.sleep(0.3)
            st.rerun()
        else:
            st.warning("닉네임을 공백 없이 입력해주세요.")
    st.stop()

# ------------------------------------------------------------------
# 5. 메인 앱 화면
# ------------------------------------------------------------------
st.title("📸 일상 저장소 (●'◡'●)")

col_user, col_change = st.columns([4, 1])
with col_user:
    st.write(f"👤 접속자: **{user_nickname}** 님으로 자동 로그인됨")
with col_change:
    if st.button("⚙️ 닉네임 변경"):
        cookie_manager.delete("user_nickname", key="del_nick")
        if "user_nickname" in st.session_state:
            del st.session_state["user_nickname"]
        time.sleep(0.3)
        st.rerun()

tab1, tab2 = st.tabs(["📤 파일 업로드", "🖼️ 공유 갤러리"])

# ==================================================================
# [TAB 1] 파일 업로드
# ==================================================================
with tab1:
    st.subheader("새로운 추억 올리기")
    
    if "upload_msg" in st.session_state:
        st.success(st.session_state["upload_msg"])
        del st.session_state["upload_msg"]

    uploaded_file = st.file_uploader(
        "사진이나 문서를 선택하세요", 
        type=["png", "jpg", "jpeg", "gif", "txt", "pdf"]
    )

    if uploaded_file is not None:
        st.info(f"📁 선택된 파일: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
        
        if uploaded_file.type.startswith("image/"):
            st.image(uploaded_file, caption="업로드할 이미지 미리보기", width=300)
        
        if st.button("GitHub에 저장하기", type="primary"):
            with st.spinner("GitHub로 업로드 중... 잠시만 기다려주세요!"):
                uploaded_file.seek(0)
                file_bytes = uploaded_file.read()
                encoded_content = base64.b64encode(file_bytes).decode('utf-8')

                clean_filename = uploaded_file.name.replace(" ", "_")
                file_path = f"uploads/{user_nickname}__{clean_filename}"

                url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
                data = {
                    "message": f"Upload by {user_nickname}: {clean_filename}",
                    "content": encoded_content
                }

                res = requests.put(url, headers=api_headers, json=data)

                if res.status_code in [200, 201]:
                    st.session_state["upload_msg"] = f"🎉 '{uploaded_file.name}' 파일이 성공적으로 올려졌습니다!"
                    st.rerun()
                else:
                    st.error(f"❌ 업로드 실패 (상태 코드: {res.status_code})")
                    st.json(res.json())

# ==================================================================
# [TAB 2] 공유 갤러리 (댓글 기능 포함)
# ==================================================================
with tab2:
    st.subheader("모두가 공유한 일상들")
    
    col_ref, col_fav = st.columns([1, 2])
    with col_ref:
        if st.button("🔄 갤러리 새로고침"):
            st.rerun()
    with col_fav:
        show_fav_only = st.checkbox("❤️ 즐겨찾기한 사진만 보기")

    files = fetch_github_files()
    all_comments, _ = fetch_comments()  # ⭐ 전체 댓글 데이터 일괄 로딩

    if not files:
        st.warning("아직 업로드된 사진이나 파일이 없습니다. 첫 번째 사진을 올려보세요!")
    else:
        files = [f for f in files if isinstance(f, dict) and f.get('type') == 'file']
        files = list(reversed(files))
        
        if show_fav_only:
            files = [f for f in files if f['sha'] in st.session_state["favorites"]]

        if not files and show_fav_only:
            st.info("❤️ 즐겨찾기로 등록된 사진이 없습니다. 하트(🤍) 버튼을 눌러 추가해보세요!")
        else:
            cols = st.columns(3)
            current_time_param = int(time.time())
            
            for idx, file_info in enumerate(files):
                col = cols[idx % 3]
                raw_name = file_info['name']
                download_url = file_info['download_url']
                file_path = file_info['path']
                file_sha = file_info['sha']

                if "__" in raw_name:
                    uploader, clean_name = raw_name.split("__", 1)
                else:
                    uploader = "익명"
                    clean_name = raw_name

                is_favorited = file_sha in st.session_state["favorites"]
                file_comments = all_comments.get(file_sha, [])

                with col:
                    cache_busted_url = f"{download_url}?t={current_time_param}"
                    
                    if clean_name.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'webp')):
                        st.image(cache_busted_url, use_container_width=True)
                    else:
                        st.markdown(f"[📥 파일 다운로드]({cache_busted_url})")

                    st.caption(f"📄 **{clean_name}**")
                    st.caption(f"✍️ **작성자:** {uploader}")

                    # ⭐ 하트 & 삭제 버튼
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        heart_icon = "❤️ 취소" if is_favorited else "🤍 즐겨찾기"
                        if st.button(heart_icon, key=f"fav_{idx}_{file_sha}"):
                            if is_favorited:
                                st.session_state["favorites"].remove(file_sha)
                            else:
                                st.session_state["favorites"].add(file_sha)
                            st.rerun()

                    with btn_col2:
                        if st.button("🗑️ 삭제", key=f"del_{idx}_{file_sha}"):
                            with st.spinner("삭제 처리 중..."):
                                if delete_github_file(file_path, file_sha, file_name=clean_name):
                                    if is_favorited:
                                        st.session_state["favorites"].remove(file_sha)
                                    st.session_state["upload_msg"] = f"🗑️ '{clean_name}' 파일이 삭제되었습니다."
                                    st.rerun()
                                else:
                                    st.error("❌ 삭제 실패! 권한을 확인해주세요.")

                    # ⭐ 댓글 섹션 (아코디언 형태)
                    with st.expander(f"💬 댓글 ({len(file_comments)})"):
                        if file_comments:
                            for c in file_comments:
                                st.markdown(f"**{c['author']}** <small style='color:gray;'>({c.get('time', '')})</small>: {c['text']}", unsafe_allow_html=True)
                        else:
                            st.caption("첫 댓글을 남겨보세요!")

                        st.divider()
                        
                        # 댓글 작성 폼
                        with st.form(key=f"c_form_{idx}_{file_sha}", clear_on_submit=True):
                            comment_text = st.text_input("댓글 작성", placeholder="댓글을 입력하세요...", label_visibility="collapsed")
                            submit_comment = st.form_submit_button("등록")
                            
                            if submit_comment:
                                if comment_text.strip():
                                    with st.spinner("댓글 등록 중..."):
                                        if add_comment(file_sha, user_nickname, comment_text.strip()):
                                            st.rerun()
                                        else:
                                            st.error("댓글 등록 실패!")
                                else:
                                    st.warning("내용을 입력해주세요.")

                    st.divider()
