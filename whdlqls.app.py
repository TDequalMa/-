import streamlit as st
import requests
import base64
from urllib.parse import quote, unquote

# ------------------------------------------------------------------
# 1. 페이지 기본 설정 및 제목
# ------------------------------------------------------------------
st.set_page_config(page_title="일상 저장소", page_icon="📸", layout="wide")
st.title("📸 일상 저장소 (●'◡'●)")

# ------------------------------------------------------------------
# 2. Secrets 토큰 및 사용자 설정
# ------------------------------------------------------------------
if "GITHUB_TOKEN" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 'GITHUB_TOKEN'이 설정되어 있지 않습니다!")
    st.stop()

GITHUB_TOKEN = str(st.secrets["GITHUB_TOKEN"]).strip()
REPO_OWNER = "TDequalMa"
REPO_NAME = "Memory_Archive"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ------------------------------------------------------------------
# 3. 깃허브 API 연동 함수들 (목록 조회 / 삭제)
# ------------------------------------------------------------------
# [목록 가져오기]
def fetch_github_files():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/uploads"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

# [파일 삭제하기] ⭐ 신규 추가
def delete_github_file(file_path, sha, file_name):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
    data = {
        "message": f"Delete {file_name} via Streamlit",
        "sha": sha  # 깃허브 파일 삭제 필수 값
    }
    response = requests.delete(url, headers=headers, json=data)
    return response.status_code == 200

# ------------------------------------------------------------------
# 4. 화면 탭 분리 (업로드하기 / 갤러리 구경하기)
# ------------------------------------------------------------------
tab1, tab2 = st.tabs(["📤 파일 업로드", "🖼️ 공유 갤러리"])

# ==================================================================
# [TAB 1] 파일 업로드
# ==================================================================
with tab1:
    st.subheader("새로운 추억 올리기")
    uploaded_file = st.file_uploader(
        "사진이나 문서를 선택하세요", 
        type=["png", "jpg", "jpeg", "gif", "txt", "pdf"]
    )

    if uploaded_file is not None:
        st.info(f"📁 선택된 파일: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
        
        if uploaded_file.type.startswith("image/"):
            st.image(uploaded_file, caption="업로드할 이미지 미리보기", width=300)
        
        if st.button("GitHub에 저장하기", type="primary"):
            with st.spinner("저장 중입니다..."):
                file_bytes = uploaded_file.read()
                encoded_content = base64.b64encode(file_bytes).decode('utf-8')

                safe_filename = quote(uploaded_file.name)
                file_path = f"uploads/{safe_filename}"

                url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
                data = {
                    "message": f"Upload {uploaded_file.name} via Streamlit",
                    "content": encoded_content
                }

                res = requests.put(url, headers=headers, json=data)

                if res.status_code in [200, 201]:
                    st.success("🎉 성공적으로 업로드되었습니다! '공유 갤러리' 탭에서 확인해보세요.")
                    st.rerun()
                else:
                    st.error(f"❌ 업로드 실패 (상태 코드: {res.status_code})")
                    st.json(res.json())

# ==================================================================
# [TAB 2] 공유 갤러리 (삭제 기능 추가)
# ==================================================================
with tab2:
    st.subheader("모두가 공유한 일상들")
    
    if st.button("🔄 갤러리 새로고침"):
        st.rerun()

    files = fetch_github_files()

    if not files:
        st.warning("아직 업로드된 사진이나 파일이 없습니다. 첫 번째 사진을 올려보세요!")
    else:
        files = list(reversed(files))  # 최신순 정렬
        cols = st.columns(3)           # 3열 격자 배치
        
        for idx, file_info in enumerate(files):
            col = cols[idx % 3]
            file_name = unquote(file_info['name'])
            download_url = file_info['download_url']
            file_path = file_info['path']
            file_sha = file_info['sha']
            
            with col:
                # 사진 또는 일반 파일 표시
                if file_name.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
                    st.image(download_url, caption=file_name, use_container_width=True)
                else:
                    st.write(f"📄 **{file_name}**")
                    st.markdown(f"[📥 파일 보기/다운로드]({download_url})")
                
                # ⭐ 삭제 버튼 추가 (버튼 키 중복 방지를 위해 sha값 사용)
                if st.button("🗑️ 삭제", key=f"del_{file_sha}"):
                    with st.spinner("삭제 처리 중..."):
                        if delete_github_file(file_path, file_sha, file_name):
                            st.success(f"'{file_name}' 파일이 삭제되었습니다!")
                            st.rerun()  # 삭제 후 화면 즉시 갱신
                        else:
                            st.error("❌ 삭제 실패! 권한을 확인해주세요.")
                
                st.divider()
