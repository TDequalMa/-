import streamlit as st
import requests
import base64

# --- 설정 변수 ---
# 주의: 실제 서비스할 때는 토큰을 코드에 직접 적지 말고 st.secrets를 사용하세요!
GITHUB_TOKEN = "여기에_발급받은_토큰_입력"
REPO_OWNER = "깃허브_유저명"
REPO_NAME = "저장소_이름"

st.title("GitHub로 사진/글 업로드하기")

# 1. Streamlit 파일 업로더 생성 (웹 화면에 업로드 버튼 생성)
uploaded_file = st.file_uploader("업로드할 사진을 선택하세요", type=["png", "jpg", "jpeg", "txt"])

if uploaded_file is not None:
    # 화면에 선택한 파일 이름 보여주기
    st.write(f"선택된 파일: {uploaded_file.name}")
    
    # 업로드 실행 버튼
    if st.button("GitHub에 저장하기"):
        with st.spinner("GitHub에 업로드 중입니다..."):
            
            # 2. 업로드된 파일 데이터를 읽어서 Base64로 변환
            # open() 함수 대신 Streamlit의 uploaded_file.read()를 사용합니다.
            file_bytes = uploaded_file.read()
            encoded_content = base64.b64encode(file_bytes).decode('utf-8')

            # GitHub에 저장될 경로와 파일명 (원래 파일명을 그대로 사용)
            FILE_PATH = f"uploads/{uploaded_file.name}"

            # 3. GitHub API 호출 설정
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"

            headers = {
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }

            data = {
                "message": f"Streamlit에서 {uploaded_file.name} 업로드",
                "content": encoded_content
            }

            # 4. 파일 업로드 실행 (PUT 요청)
            response = requests.put(url, headers=headers, json=data)

            if response.status_code == 201:
                st.success("✅ 성공적으로 업로드되었습니다!")
                st.markdown(f"[업로드된 파일 확인하기]({response.json()['content']['html_url']})")
            else:
                st.error(f"❌ 업로드 실패 (에러 코드: {response.status_code})")
                st.json(response.json())
