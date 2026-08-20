import streamlit as st
import requests
import base64
from urllib.parse import quote, unquote
from datetime import datetime, timezone, timedelta
import time

# ------------------------------------------------------------------
# 1. 페이지 기본 설정 및 제목
# ------------------------------------------------------------------
st.set_page_config(page_title="일상 저장소", page_icon="📸", layout="wide")
st.title("📸 일상 저장소 (●'◡'●)")

KST = timezone(timedelta(hours=9))

# ------------------------------------------------------------------
# 2. Secrets 토큰 및 사용자 설정
# ------------------------------------------------------------------
if "GITHUB_TOKEN" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 'GITHUB_TOKEN'이 설정되어 있지 않습니다!")
    st.stop()

GITHUB_TOKEN = str(st.secrets["GITHUB_TOKEN"]).strip()
REPO_OWNER = "TDequalMa"
REPO_NAME = "Memory_Archive"

# JSON 조회용 기본 API 헤더
api_headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ⭐ 실시간 바이너리 파일 다운로드 전용 Raw 헤더 (CDN 지연 회피)
raw_headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3.raw"
}

# ------------------------------------------------------------------
# 3. 깃허브 API 연동 함수들
# ------------------------------------------------------------------
def fetch_github_files():
    timestamp = int(time.time())
    # 1차 시도: uploads 폴더 탐색
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/uploads?t={timestamp}"
    response = requests.get(url, headers=api_headers)
    
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            return data, None
    elif response.status_code == 404:
        # 2차 시도: uploads 폴더가 없는 경우 루트(/) 경로 탐색 백업
        root_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents?t={timestamp}"
        root_res = requests.get(root_url, headers=api_headers)
        if root_res.status_code == 200 and isinstance(root_res.json(), list):
            return root_res.json(), "💡 uploads 폴더 대신 루트 경로에서 파일을 찾았습니다."
            
    return [], f"⚠️ 깃허브 연결 상태 코드: {response.status_code}"

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

                now_kst = datetime.now(KST)
                time_prefix = now_kst.strftime("%Y%m%d_%H%M%S")
                
                safe_filename = quote(uploaded_file.name)
                file_path = f"uploads/{time_prefix}__{safe_filename}"

                url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
                data = {
                    "message": f"Upload {uploaded_file.name} via Streamlit",
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
# [TAB 2] 공유 갤러리 (REST API 실시간 로드 적용)
# ==================================================================
with tab2:
    st.subheader("모두가 공유한 일상들")
    
    if st.button("🔄 갤러리 새로고침"):
        st.rerun()

    files, info_msg = fetch_github_files()

    if info_msg:
        st.caption(info_msg)

    # 폴더 제외, 실제 파일만 필터링
    files = [f for f in files if isinstance(f, dict) and f.get('type') == 'file']

    if not files:
        st.warning("아직 업로드된 사진이나 파일이 없습니다. 첫 번째 사진을 올려보세요!")
    else:
        files = list(reversed(files))  # 최신순 정렬
        cols = st.columns(3)
        
        for idx, file_info in enumerate(files):
            col = cols[idx % 3]
            raw_name = unquote(file_info['name'])
            api_file_url = file_info['url']  # ⭐ 깃허브 REST API 파일 고유 주소
            file_path = file_info['path']
            file_sha = file_info['sha']
            
            if "__" in raw_name:
                time_str, clean_name = raw_name.split("__", 1)
                try:
                    upload_date = datetime.strptime(time_str, "%Y%m%d_%H%M%S").strftime("%Y년 %m월 %d일 %H:%M")
                except ValueError:
                    upload_date = "날짜 정보 없음"
            else:
                clean_name = raw_name
                upload_date = "이전 업로드 파일"

            with col:
                # ⭐ CDN 반영 지연을 우회하기 위해 REST API 실시간 Raw 데이터를 요청함
                if clean_name.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'webp')):
                    img_res = requests.get(api_file_url, headers=raw_headers)
                    if img_res.status_code == 200:
                        st.image(img_res.content, use_container_width=True)
                    else:
                        # 2차 백업: download_url 시도
                        dl_url = file_info.get('download_url')
                        if dl_url and requests.get(dl_url).status_code == 200:
                            st.image(dl_url, use_container_width=True)
                        else:
                            st.error(f"❌ 이미지 읽기 실패 (코드: {img_res.status_code})")
                else:
                    file_res = requests.get(api_file_url, headers=raw_headers)
                    if file_res.status_code == 200:
                        st.download_button(
                            label="📥 파일 다운로드",
                            data=file_res.content,
                            file_name=clean_name,
                            key=f"down_{idx}_{file_sha}"
                        )

                st.caption(f"📄 **{clean_name}**")
                st.caption(f"📅 **업로드:** {upload_date}")

                if st.button("🗑️ 삭제", key=f"del_{idx}_{file_sha}"):
                    with st.spinner("삭제 처리 중..."):
                        if delete_github_file(file_path, file_sha, file_name=clean_name):
                            st.session_state["upload_msg"] = f"🗑️ '{clean_name}' 파일이 삭제되었습니다."
                            st.rerun()
                        else:
                            st.error("❌ 삭제 실패! 권한을 확인해주세요.")
                
                st.divider()
