import streamlit as st
import requests
import base64
from urllib.parse import quote

# 🔒 Secrets에 토큰이 제대로 등록되어 있는지 안전하게 확인
if "GITHUB_TOKEN" not in st.secrets:
    st.error("⚠️ Streamlit Secrets에 GITHUB_TOKEN 설정이 누락되었습니다. Settings -> Secrets에서 토큰을 등록해 주세요!")
    st.stop()

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_OWNER = "TDequalMa"  # 👈 본인 아이디로 변경
REPO_NAME = "Memory_Archive"     # 👈 본인 저장소 이름으로 변경

# (이하 기존 업로드 로직 동일)

# (이하 기존 업로드 로직 동일)

# --- 설정 변수 ---
# ⚠️ 중요: "ghp_..." 로 시작하는 실제 깃허브 토큰으로 반드시 변경해주세요!
GITHUB_TOKEN = "ghp_여기에_실제_토큰_입력"
REPO_OWNER = "깃허브_유저명"
REPO_NAME = "저장소_이름"

st.title("GitHub로 사진/글 업로드하기")

uploaded_file = st.file_uploader("업로드할 사진을 선택하세요", type=["png", "jpg", "jpeg", "txt"])

if uploaded_file is not None:
    st.write(f"선택된 파일: {uploaded_file.name}")
    
    if st.button("GitHub에 저장하기"):
        # 토큰에 한글이 그대로 남아있는지 검사
        if not GITHUB_TOKEN.isascii():
            st.error("❌ GITHUB_TOKEN 변수에 한글이 포함되어 있습니다. 'ghp_'로 시작하는 실제 토큰 값으로 바꿔주세요!")
            st.stop()
            
        with st.spinner("GitHub에 업로드 중입니다..."):
            file_bytes = uploaded_file.read()
            encoded_content = base64.b64encode(file_bytes).decode('utf-8')

            # ⭐ [해결 포인트] 한글 파일명이 들어와도 에러가 나지 않도록 URL 인코딩 처리
            safe_filename = quote(uploaded_file.name)
            FILE_PATH = f"uploads/{safe_filename}"

            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"

            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }

            data = {
                "message": f"Streamlit에서 {uploaded_file.name} 업로드",
                "content": encoded_content
            }

            # API 호출
            response = requests.put(url, headers=headers, json=data)

            if response.status_code in [200, 201]:
                st.success("✅ 성공적으로 업로드되었습니다!")
                st.markdown(f"[업로드된 파일 확인하기]({response.json()['content']['html_url']})")
            else:
                st.error(f"❌ 업로드 실패 (에러 코드: {response.status_code})")
                st.json(response.json())
