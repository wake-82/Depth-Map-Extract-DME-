DME (Depth Map Extract) v1.0
DME is a standalone GUI utility designed to process debug depth videos from IW3 (IW-GUI). It specializes in extracting specific frame areas and improving depth map quality through Gaussian blur and bilateral filtering.

IW3(IW-GUI)의 디버그 뎁스 비디오를 처리하기 위한 독립형 GUI 도구입니다. 영상의 절반을 추출하고 가우시안 블러 후처리를 통해 뎁스 맵의 품질을 개선합니다.

✨ Key Features (주요 기능)
Half-Frame Extraction: Automatically crops and extracts the relevant half (iw/2) of the video frame. (비디오 프레임의 절반을 자동으로 크롭하여 추출합니다.)

Advanced Post-processing: Enhance depth maps using adjustable Gaussian Blur and Bilateral Filters. (가우시안 블러 및 바이래터럴 필터를 적용할 수 있습니다.)

Resolution Scaling: Provides multiple preset scaling options (518, 512, 504, 392). (다양한 해상도 조절 옵션을 제공합니다.)

Multi-Codec Support: High-performance encoding options including H.264, H.265 (HEVC), and NVENC. (H.264, H.265 및 NVENC 하드웨어 가속 인코딩을 지원합니다.)

Smart Settings: Automatically saves and restores your last-used configurations. (마지막 사용 언어, 경로, 인코딩 설정 등을 자동으로 저장하고 불러옵니다.)

🚀 Getting Started (시작하기)
Prerequisites (필수 요소)
Python 3.x

FFmpeg Binaries: * [EN] For the application to function correctly, ffmpeg.exe and ffprobe.exe must be placed in the same directory as DME.py.

[KO] 프로그램이 정상적으로 작동하려면 ffmpeg.exe와 ffprobe.exe가 DME.py와 같은 폴더에 위치해야 합니다.

Installation & Usage (설치 및 실행)
Bash

# Clone the repository (저장소 클론)
git clone https://github.com/wake-82/DME.git

# Install required dependencies (필요한 라이브러리 설치)
pip install -r requirements.txt

# Run the application (실행)
python DME.py
📝 License (라이선스)
DME: This project is licensed under the MIT License.

FFmpeg: * [EN] This software uses libraries from the FFmpeg project, licensed under the LGPLv2.1. Please visit ffmpeg.org for more details.

[KO] 본 프로그램은 LGPLv2.1 라이선스를 따르는 FFmpeg 프로젝트의 라이브러리를 사용합니다. 자세한 내용은 공식 페이지(ffmpeg.org)를 참조하십시오.
