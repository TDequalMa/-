import streamlit as st
import requests
import base64
from urllib.parse import quote

# ------------------------------------------------------------------
# 1. 페이지 기본 설정 및 제목
# ------------------------------------------------------------------
st.set_page_config(page_title="GitHub 파일 업로더", page_icon="📤")
st.title("일상 저장소 (●'◡'●)")

# ------------------------------------------------------------------
# 2. Secrets(비밀 창고) 토큰 확인
# ------------------------------------------------------------------
if "GITHUB_TOKEN" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 'GITHUB_TOKEN'이 설정되어 있지 않습니다!")
    st.info("Streamlit Settings -> Secrets 메뉴에서 토큰을 입력해 주세요.")
    st.stop()

# ------------------------------------------------------------------
# 3. 사용자 설정 (⚠️ 여기 두 줄만 본인 정보로 바꿔주세요!)
# ------------------------------------------------------------------
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]

REPO_OWNER = "TDequalMa"      # 👈 예: "honggildong"
REPO_NAME = "Memory_Archive"   # 👈 예: "my-photo-album"

# ------------------------------------------------------------------
# 4. 파일 업로드 화면 UI
# ------------------------------------------------------------------
uploaded_file = st.file_uploader(
    "업로드할 파일(사진 또는 텍스트)을 선택하세요", 
    type=["png", "jpg", "jpeg", "gif", "txt", "pdf"]
)

if uploaded_file is not None:
    st.info(f"📁 선택된 파일: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")
    
    # 이미지 파일인 경우 미리보기
    if uploaded_file.type.startswith("image/"):
        st.image(uploaded_file, caption="업로드할 이미지 미리보기", width=300)
    
    # 저장 버튼
    if st.button("GitHub에 저장하기", type="primary"):
        with st.spinner("GitHub에 업로드하는 중입니다..."):
            
            # [1] 파일 읽기 & Base64 인코딩
            file_bytes = uploaded_file.read()
            encoded_content = base64.b64encode(file_bytes).decode('utf-8')

            # [2] 한글 파일명 에러 방지 (URL 인코딩)
            safe_filename = quote(uploaded_file.name)
            file_path = f"uploads/{safe_filename}"

            # [3] GitHub API 호출
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{file_path}"
            
            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "message": f"Upload {uploaded_file.name} via Streamlit",
                "content": encoded_content
            }

            response = requests.put(url, headers=headers, json=data)

            # [4] 결과 처리
            if response.status_code in [200, 201]:
                res_data = response.json()
                st.success("🎉 성공적으로 업로드되었습니다!")
                st.markdown(f"👉 [GitHub에서 올려진 파일 확인하기]({res_data['content']['html_url']})")
            else:
                st.error(f"❌ 업로드 실패 (상태 코드: {response.status_code})")
                st.json(response.json())
