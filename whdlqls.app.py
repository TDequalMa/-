import requests
import base64

# --- 설정 변수 ---
GITHUB_TOKEN = "여기에_발급받은_토큰_입력"
REPO_OWNER = "깃허브_유저명"  # 예: "myusername"
REPO_NAME = "저장소_이름"     # 예: "my-repository"
FILE_PATH = "uploads/my_photo.png"  # 저장될 경로와 파일명 (텍스트라면 test.txt)

# 1. 업로드할 파일 읽기 및 Base64 인코딩
# [텍스트를 올릴 경우]
# content_string = "이것은 깃허브에 올라갈 텍스트입니다."
# encoded_content = base64.b64encode(content_string.encode('utf-8')).decode('utf-8')

# [사진(이미지)을 올릴 경우]
with open("로컬에_있는_사진경로.png", "rb") as image_file:
    encoded_content = base64.b64encode(image_file.read()).decode('utf-8')

# 2. GitHub API 호출 설정
url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

data = {
    "message": "사진 업로드 커밋 메시지", # 깃허브 커밋 내역에 뜰 메시지
    "content": encoded_content
}

# 3. 파일 업로드 실행 (PUT 요청)
response = requests.put(url, headers=headers, json=data)

if response.status_code == 201:
    print("✅ 성공적으로 업로드되었습니다!")
    print("파일 다운로드 URL:", response.json()['content']['download_url'])
else:
    print("❌ 업로드 실패:", response.status_code)
    print(response.json())
