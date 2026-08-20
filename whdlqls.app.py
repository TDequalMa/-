import streamlit as st
import requests
import base64
import time

# ------------------------------------------------------------------
# 1. 페이지 기본 설정 및 제목
# ------------------------------------------------------------------
st.set_page_config(page_title="일상 저장소", page_icon="📸", layout="wide")
st.title("📸 일상 저장소 (●'◡'●)")

# ⭐ 즐겨찾기 목록 저장소 초기화 (세션 상태)
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
# 3. 깃허브 API 연동 함수들
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

# ------------------------------------------------------------------
# 4. 화면 탭 분리
# ------------------------------------------------------------------
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

                clean_name = uploaded_file.name.replace(" ", "_")
                file_path = f"uploads/{clean_name}"

                url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
                data = {
                    "message": f"Upload {clean_name} via Streamlit",
                    "content": encoded_content
                }

                res = requests.put(url, headers=api_headers, json=data)

                if res.status_code in [200, 201]:
                    st.session_state["upload_msg"] = f"🎉 '{uploaded_file.name}' 파일이 성공적으로 올려졌습니다! '🖼️ 공유 갤러리' 탭을 확인해 보세요."
                    st.rerun()
                else:
                    st.error(f"❌ 업로드 실패 (상태 코드: {res.status_code})")
                    st.json(res.json())

# ==================================================================
# [TAB 2] 공유 갤러리 (즐겨찾기 기능 추가)
# ==================================================================
with tab2:
    st.subheader("모두가 공유한 일상들")
    
    # ⭐ 상단 컨트롤 (새로고침 & 즐겨찾기 필터)
    col_ref, col_fav = st.columns([1, 2])
    with col_ref:
        if st.button("🔄 갤러리 새로고침"):
            st.rerun()
    with col_fav:
        show_fav_only = st.checkbox("❤️ 즐겨찾기한 사진만 보기")

    files = fetch_github_files()

    if not files:
        st.warning("아직 업로드된 사진이나 파일이 없습니다. 첫 번째 사진을 올려보세요!")
    else:
        files = [f for f in files if isinstance(f, dict) and f.get('type') == 'file']
        files = list(reversed(files))
        
        # ⭐ 즐겨찾기 필터링 적용
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

                is_favorited = file_sha in st.session_state["favorites"]

                with col:
                    cache_busted_url = f"{download_url}?t={current_time_param}"
                    
                    if raw_name.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'webp')):
                        st.image(cache_busted_url, use_container_width=True)
                    else:
                        st.markdown(f"[📥 파일 다운로드]({cache_busted_url})")

                    st.caption(f"📄 **{raw_name}**")

                    # ⭐ 하트 버튼 & 삭제 버튼 나란히 배치
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
                                if delete_github_file(file_path, file_sha, file_name=raw_name):
                                    if is_favorited:
                                        st.session_state["favorites"].remove(file_sha)
                                    st.session_state["upload_msg"] = f"🗑️ '{raw_name}' 파일이 삭제되었습니다."
                                    st.rerun()
                                else:
                                    st.error("❌ 삭제 실패! 권한을 확인해주세요.")
                    
                    st.divider()
