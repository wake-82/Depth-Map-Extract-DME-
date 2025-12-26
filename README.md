# DME (Depth Map Extract) v1.0

# DME (뎁스맵 추출기) v1.0

DME is a standalone GUI utility designed to process debug depth videos from IW3 (IW-GUI). 
It specializes in extracting specific frame areas and improving depth map quality through Gaussian blur and bilateral filtering.

IW3(IW-GUI)의 디버그 뎁스 비디오를 처리하기 위한 독립형 GUI 도구입니다. 
영상의 절반을 추출하고 가우시안 블러 후처리를 통해 뎁스 맵의 품질을 개선합니다.

## ✨ Key Features
* **Half-Frame Extraction:** Automatically crops and extracts the relevant half (iw/2) of the video frame.
* **Advanced Post-processing:** Enhance depth maps using adjustable Gaussian Blur and Bilateral Filters.
* **Resolution Scaling:** Provides multiple preset scaling options (518, 512, 504, 392) to fit your needs.
* **Multi-Codec Support:** High-performance encoding options including H.264, H.265 (HEVC), and NVENC hardware acceleration.
* **Smart Settings:** Automatically saves and restores your last-used language, paths, and encoding configurations.

* ## ✨ 주요 기능 (Key Features)
* **Half-Frame Extraction:** 비디오 프레임의 절반(iw/2)을 자동으로 크롭하여 추출합니다.
* **Post-processing:** 가우시안 블러(Gaussian Blur) 및 바이래터럴 필터(Bilateral Filter)를 적용할 수 있습니다.
* **Resolution Scaling:** 518, 512, 504, 392 등 다양한 해상도 조절 옵션을 제공합니다.
* **Multi-Codec Support:** H.264, H.265(HEVC) 및 NVENC 하드웨어 가속 인코딩을 지원합니다.
* **Smart Settings:** 마지막 사용 언어, 경로, 인코딩 설정 등을 자동으로 저장하고 불러옵니다.

## 🚀 Getting Started

## 🚀 시작하기 (Getting Started)

### Prerequisites
1. **Python 3.x**
2. **FFmpeg:** Must be installed in your system PATH or placed as `ffmpeg.exe` in the program root directory.

### 필수 요소 (Prerequisites)
1. **Python 3.x**
2. **FFmpeg:** 시스템 경로에 추가되어 있거나 프로그램 폴더에 `ffmpeg.exe`가 있어야 합니다.

### Installation & Usage
```bash
# Clone the repository
git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)

### 설치 및 실행
```bash
# 저장소 클론
git clone [https://github.com/사용자이름/저장소이름.git](https://github.com/사용자이름/저장소이름.git)

# Install required dependencies
pip install -r requirements.txt

# 필요한 라이브러리 설치
pip install -r requirements.txt

# Run the application
python DME.py

# 실행
python DME.py














