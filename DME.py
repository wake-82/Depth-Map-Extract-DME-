import sys
import os
import json
import shutil
import subprocess
import re
import platform
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QSlider, QCheckBox, 
                             QComboBox, QProgressBar, QTextEdit, QFileDialog, QMessageBox, 
                             QGroupBox, QDoubleSpinBox, QStyleFactory, QGridLayout, QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# ==========================================
# 1. 인코딩 작업자 스레드
# ==========================================
class EncoderWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self.is_running = True
        self.process = None

    def get_duration(self, file_path):
        ffmpeg_path = self.params.get('ffmpeg_path')
        base_dir = os.path.dirname(ffmpeg_path)
        ffprobe_name = "ffprobe.exe" if platform.system() == "Windows" else "ffprobe"
        ffprobe_path = os.path.join(base_dir, ffprobe_name)
        creation_flags = 0x08000000 if platform.system() == "Windows" else 0

        if os.path.exists(ffprobe_path):
            try:
                cmd = [ffprobe_path, "-v", "error", "-show_entries", "format=duration", 
                       "-of", "default=noprint_wrappers=1:nokey=1", file_path]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                        text=True, encoding='utf-8', creationflags=creation_flags, timeout=5)
                return float(result.stdout.strip())
            except: pass
        return 0

    def get_unique_path(self, folder, base_name, ext):
        path = os.path.join(folder, f"{base_name}.{ext}")
        if not os.path.exists(path): return path
        counter = 1
        while True:
            new_path = os.path.join(folder, f"{base_name} ({counter}).{ext}")
            if not os.path.exists(new_path): return new_path
            counter += 1

    def run(self):
        ffmpeg_path = self.params.get('ffmpeg_path')
        input_path = self.params['input_path']
        output_folder = self.params['output_folder']
        
        duration = self.get_duration(input_path)
        filename = os.path.basename(input_path)
        name_only, _ = os.path.splitext(filename)
        
        setting_suffix = f"_G{self.params['blur']:.2f}_S{self.params['sigmar']:.3f}"
        output_path = self.get_unique_path(output_folder, f"{name_only}{setting_suffix}", self.params['ext'])

        vf_chain = ["crop=iw/2:ih:iw/2:0"] 
        if self.params['use_filter']:
            vf_chain.append(f"gblur=sigma={self.params['blur']}")
            vf_chain.append(f"bilateral=sigmaS={self.params['blur']}:sigmaR={self.params['sigmar']}")
        if self.params['res_mode'] != "none":
            vf_chain.append(f"scale={self.params['res_mode']}:{self.params['res_mode']}")
            
        if self.params.get('aspect_ratio', "NONE") != "NONE":
            vf_chain.append(f"setdar={self.params['aspect_ratio']}")
        
        cmd = [ffmpeg_path, "-y", "-i", input_path, "-vf", ",".join(vf_chain), 
               "-c:v", self.params['codec'], "-preset", self.params['preset']]
        
        if "nvenc" in self.params['codec']:
            cmd.extend(["-cq", str(self.params['crf'])])
        else:
            cmd.extend(["-crf", str(self.params['crf'])])
        cmd.extend(["-c:a", "copy", output_path])

        self.log_signal.emit(f"▶ Start Processing: {filename}")
        creation_flags = 0x08000000 if platform.system() == "Windows" else 0
        
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            universal_newlines=True, encoding='utf-8', errors='ignore', creationflags=creation_flags
        )
        
        for line in self.process.stdout:
            if not self.is_running: break
            time_match = re.search(r"time=(\d+):(\d+):(\d+).(\d+)", line)
            if time_match and duration > 0:
                h, m, s, _ = map(int, time_match.groups())
                current_time = h * 3600 + m * 60 + s
                prog = int((current_time / duration) * 100)
                self.progress_signal.emit(min(prog, 99))
        
        if self.process:
            self.process.wait()
        
        if self.is_running:
            self.progress_signal.emit(100)
            self.finished_signal.emit()

    def stop(self):
        self.is_running = False
        if self.process:
            self.process.kill()
            self.process = None

# ==========================================
# 2. 메인 GUI 클래스
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_lang = "EN"
        self.worker = None
        self.config_file = "settings_single.json"
        self.ffmpeg_path = self.check_ffmpeg()
        
        self.texts = {
            "KO": {
                "title": "Depth Map Extract (DME) v1.0",
                "path_group": "파일 경로 설정", "input_path": "입력 파일:", "output_path": "출력 폴더:",
                "select": "찾아보기", "opt_group": "영상 처리 옵션", "apply_filter": "필터 적용",
                "resolution": "해상도:", "res_orig": "원본", "gblur": "G 블러:",
                "sigmar": "Sigma R:", "auto_balance": "자동 밸런스", "enc_group": "인코딩 엔진",
                "format": "포맷:", "codec": "코덱:", "quality": "품질(CRF/CQ):", "preset": "프리셋:",
                "start": "변환 시작", "stop": "중단", "finish_msg": "변환이 완료되었습니다.", "err_ffmpeg": "FFmpeg가 없습니다."
            },
            "EN": {
                "title": "Depth Map Extract (DME) v1.0",
                "path_group": "Path Settings", "input_path": "Input File:", "output_path": "Output Folder:",
                "select": "Browse", "opt_group": "Image Processing", "apply_filter": "Apply Filter",
                "resolution": "Res:", "res_orig": "Original", "gblur": "G-Blur:",
                "sigmar": "Sigma R:", "auto_balance": "Auto Balance", "enc_group": "Engine",
                "format": "Format:", "codec": "Codec:", "quality": "Quality:", "preset": "Preset:",
                "start": "Start", "stop": "Stop", "finish_msg": "Conversion complete.", "err_ffmpeg": "FFmpeg not found."
            }
        }

        self.init_ui()
        self.load_settings() # 설정 파일 로드
        self.retranslate_ui()
        self.toggle_filter_ui(self.use_filter_check.isChecked())

    def check_ffmpeg(self):
        local_path = os.path.join(os.getcwd(), "ffmpeg.exe")
        if os.path.exists(local_path): return local_path
        sys_path = shutil.which("ffmpeg")
        return sys_path if sys_path else None

    def init_ui(self):
        self.setGeometry(100, 100, 950, 750)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        lang_layout = QHBoxLayout()
        self.btn_lang_ko = QRadioButton("한국어"); self.btn_lang_en = QRadioButton("English")
        self.lang_group = QButtonGroup(self); self.lang_group.addButton(self.btn_lang_ko); self.lang_group.addButton(self.btn_lang_en)
        self.lang_group.buttonToggled.connect(lambda: [setattr(self, 'current_lang', "KO" if self.btn_lang_ko.isChecked() else "EN"), self.retranslate_ui()])
        lang_layout.addStretch(); lang_layout.addWidget(self.btn_lang_ko); lang_layout.addWidget(self.btn_lang_en)
        main_layout.addLayout(lang_layout)

        self.input_group = QGroupBox()
        path_layout = QGridLayout()
        self.lbl_input = QLabel(); path_layout.addWidget(self.lbl_input, 0, 0)
        self.input_edit = QLineEdit(); path_layout.addWidget(self.input_edit, 0, 1)
        self.input_btn = QPushButton(); self.input_btn.clicked.connect(self.select_input); path_layout.addWidget(self.input_btn, 0, 2)
        self.lbl_output = QLabel(); path_layout.addWidget(self.lbl_output, 1, 0)
        self.output_edit = QLineEdit(); path_layout.addWidget(self.output_edit, 1, 1)
        self.output_btn = QPushButton(); self.output_btn.clicked.connect(self.select_output); path_layout.addWidget(self.output_btn, 1, 2)
        self.input_group.setLayout(path_layout); main_layout.addWidget(self.input_group)

        self.filter_group = QGroupBox()
        filter_layout = QGridLayout()
        self.use_filter_check = QCheckBox(); self.use_filter_check.toggled.connect(self.toggle_filter_ui)
        filter_layout.addWidget(self.use_filter_check, 0, 0)
        
        res_box = QHBoxLayout(); self.lbl_res = QLabel(); res_box.addWidget(self.lbl_res)
        self.res_none = QRadioButton(); self.res_518 = QRadioButton("518"); self.res_512 = QRadioButton("512")
        self.res_504 = QRadioButton("504"); self.res_392 = QRadioButton("392")
        self.res_group = QButtonGroup(self)
        [self.res_group.addButton(b) for b in [self.res_none, self.res_518, self.res_512, self.res_504, self.res_392]]
        [res_box.addWidget(b) for b in [self.res_none, self.res_518, self.res_512, self.res_504, self.res_392]]
        filter_layout.addLayout(res_box, 0, 1)
        
        self.lbl_gblur = QLabel(); filter_layout.addWidget(self.lbl_gblur, 1, 0)
        self.blur_slider = QSlider(Qt.Orientation.Horizontal); self.blur_slider.setRange(0, 300); filter_layout.addWidget(self.blur_slider, 1, 1)
        self.blur_spin = QDoubleSpinBox(); self.blur_spin.setRange(0.00, 3.00); self.blur_spin.setSingleStep(0.05); filter_layout.addWidget(self.blur_spin, 1, 2)
        
        self.lbl_sigma = QLabel(); filter_layout.addWidget(self.lbl_sigma, 2, 0)
        self.sigmar_slider = QSlider(Qt.Orientation.Horizontal); self.sigmar_slider.setRange(0, 40); filter_layout.addWidget(self.sigmar_slider, 2, 1)
        self.sigmar_spin = QDoubleSpinBox(); self.sigmar_spin.setRange(0.000, 0.040); self.sigmar_spin.setDecimals(3); filter_layout.addWidget(self.sigmar_spin, 2, 2)
        self.auto_check = QCheckBox(); self.auto_check.toggled.connect(self.toggle_auto_mode); filter_layout.addWidget(self.auto_check, 2, 3)
        self.filter_group.setLayout(filter_layout); main_layout.addWidget(self.filter_group)

        self.enc_group = QGroupBox()
        enc_layout = QGridLayout()
        self.lbl_fmt = QLabel(); enc_layout.addWidget(self.lbl_fmt, 0, 0)
        self.ext_combo = QComboBox(); self.ext_combo.addItems(["mp4", "mkv", "ts"]); enc_layout.addWidget(self.ext_combo, 0, 1)
        self.lbl_cdc = QLabel(); enc_layout.addWidget(self.lbl_cdc, 0, 2)
        self.codec_combo = QComboBox(); self.codec_combo.addItems(["libx265", "libx264", "hevc_nvenc"])
        self.codec_combo.currentTextChanged.connect(self.update_presets) # 코덱 변경시 프리셋 갱신
        enc_layout.addWidget(self.codec_combo, 0, 3)
        self.lbl_qty = QLabel(); enc_layout.addWidget(self.lbl_qty, 1, 0)
        self.crf_spin = QDoubleSpinBox(); self.crf_spin.setRange(0, 51); self.crf_spin.setDecimals(0); enc_layout.addWidget(self.crf_spin, 1, 1)
        self.lbl_pst = QLabel(); enc_layout.addWidget(self.lbl_pst, 1, 2)
        self.preset_combo = QComboBox(); enc_layout.addWidget(self.preset_combo, 1, 3)
        self.enc_group.setLayout(enc_layout); main_layout.addWidget(self.enc_group)

        self.progress_bar = QProgressBar(); main_layout.addWidget(self.progress_bar)
        self.log_text = QTextEdit(); self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #00FF00; font-family: Consolas; font-size: 11px;")
        main_layout.addWidget(self.log_text)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton(); self.start_btn.setFixedHeight(50); self.start_btn.clicked.connect(self.start_encoding)
        self.stop_btn = QPushButton(); self.stop_btn.setFixedHeight(50); self.stop_btn.setEnabled(False); self.stop_btn.clicked.connect(self.stop_encoding)
        btn_layout.addWidget(self.start_btn); btn_layout.addWidget(self.stop_btn)
        main_layout.addLayout(btn_layout)

        self.lbl_copyright = QLabel("Copyright (c) 2025 Wake-82. All rights reserved.")
        self.lbl_copyright.setAlignment(Qt.AlignmentFlag.AlignCenter); self.lbl_copyright.setStyleSheet("color: #888888; font-size: 10px;")
        main_layout.addWidget(self.lbl_copyright)

        self.blur_slider.valueChanged.connect(self.sync_blur_from_slider)
        self.blur_spin.valueChanged.connect(self.sync_blur_from_spin)
        self.sigmar_slider.valueChanged.connect(self.sync_sigmar_from_slider)
        self.sigmar_spin.valueChanged.connect(self.sync_sigmar_from_spin)

    def update_presets(self):
        current_codec = self.codec_combo.currentText()
        self.preset_combo.clear()
        if "nvenc" in current_codec:
            presets = ["p1", "p2", "p3", "p4", "p5", "p6", "p7", "fast", "medium", "slow"]
            self.preset_combo.addItems(presets)
        else:
            presets = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
            self.preset_combo.addItems(presets)

    def sync_blur_from_slider(self, v):
        self.blur_spin.blockSignals(True); self.blur_spin.setValue(v/100.0); self.blur_spin.blockSignals(False)
        self.update_sigmar_balance()

    def sync_blur_from_spin(self, v):
        self.blur_slider.blockSignals(True); self.blur_slider.setValue(int(v*100)); self.blur_slider.blockSignals(False)
        self.update_sigmar_balance()

    def sync_sigmar_from_slider(self, v):
        self.sigmar_spin.blockSignals(True); self.sigmar_spin.setValue(v/1000.0); self.sigmar_spin.blockSignals(False)

    def sync_sigmar_from_spin(self, v):
        self.sigmar_slider.blockSignals(True); self.sigmar_slider.setValue(int(v*1000)); self.sigmar_slider.blockSignals(False)

    def update_sigmar_balance(self):
        if self.auto_check.isChecked() and self.use_filter_check.isChecked():
            bv = self.blur_spin.value()
            if bv <= 0.6: sv = 0.020
            elif bv <= 0.8: sv = 0.020 + (bv - 0.6) * 0.03
            elif bv <= 1.0: sv = 0.026 + (bv - 0.8) * 0.035
            elif bv <= 1.2: sv = 0.033 + (bv - 1.0) * 0.035
            else: sv = 0.040
            self.sigmar_spin.blockSignals(True); self.sigmar_slider.blockSignals(True)
            self.sigmar_spin.setValue(round(sv, 3)); self.sigmar_slider.setValue(int(round(sv, 3)*1000))
            self.sigmar_spin.blockSignals(False); self.sigmar_slider.blockSignals(False)

    def retranslate_ui(self):
        t = self.texts[self.current_lang]; self.setWindowTitle(t["title"])
        self.input_group.setTitle(t["path_group"]); self.lbl_input.setText(t["input_path"]); self.input_btn.setText(t["select"])
        self.lbl_output.setText(t["output_path"]); self.output_btn.setText(t["select"])
        self.filter_group.setTitle(t["opt_group"]); self.use_filter_check.setText(t["apply_filter"]); self.lbl_res.setText(t["resolution"])
        self.res_none.setText(t["res_orig"]); self.lbl_gblur.setText(t["gblur"]); self.lbl_sigma.setText(t["sigmar"])
        self.auto_check.setText(t["auto_balance"]); self.enc_group.setTitle(t["enc_group"]); self.lbl_fmt.setText(t["format"])
        self.lbl_cdc.setText(t["codec"]); self.lbl_qty.setText(t["quality"]); self.lbl_pst.setText(t["preset"])
        self.start_btn.setText(t["start"]); self.stop_btn.setText(t["stop"])

    def select_input(self):
        f, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Videos (*.mp4 *.mkv *.ts)")
        if f: self.input_edit.setText(f)

    def select_output(self):
        d = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if d: self.output_edit.setText(d)

    def toggle_filter_ui(self, c):
        self.blur_slider.setEnabled(c); self.blur_spin.setEnabled(c); self.auto_check.setEnabled(c)
        self.sigmar_slider.setEnabled(c and not self.auto_check.isChecked())
        self.sigmar_spin.setEnabled(c and not self.auto_check.isChecked())

    def toggle_auto_mode(self, c):
        if self.use_filter_check.isChecked():
            self.sigmar_slider.setEnabled(not c); self.sigmar_spin.setEnabled(not c)
            if c: self.update_sigmar_balance()

    def start_encoding(self):
        self.ffmpeg_path = self.check_ffmpeg()
        if not self.ffmpeg_path: QMessageBox.critical(self, "Error", self.texts[self.current_lang]["err_ffmpeg"]); return
        if not self.input_edit.text() or not self.output_edit.text():
            QMessageBox.warning(self, "Warning", "Please select input file and output folder."); return

        res_val = "none"
        if self.res_518.isChecked(): res_val = "518"
        elif self.res_512.isChecked(): res_val = "512"
        elif self.res_504.isChecked(): res_val = "504"
        elif self.res_392.isChecked(): res_val = "392"

        params = {
            'input_path': self.input_edit.text(), 'output_folder': self.output_edit.text(),
            'ffmpeg_path': self.ffmpeg_path, 'use_filter': self.use_filter_check.isChecked(),
            'res_mode': res_val, 'aspect_ratio': "NONE",
            'blur': self.blur_spin.value(), 'sigmar': self.sigmar_spin.value(),
            'ext': self.ext_combo.currentText(), 'codec': self.codec_combo.currentText(), 
            'crf': int(self.crf_spin.value()), 'preset': self.preset_combo.currentText()
        }

        self.start_btn.setEnabled(False); self.stop_btn.setEnabled(True)
        self.log_text.clear(); self.progress_bar.setValue(0)
        self.worker = EncoderWorker(params)
        self.worker.log_signal.connect(self.log_text.append)
        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.error_signal.connect(lambda e: [QMessageBox.critical(self, "Error", e), self.on_finished()])
        self.worker.start()

    def stop_encoding(self):
        if self.worker:
            self.worker.stop()
            self.log_text.append("<span style='color:red;'><b>🛑 Aborted.</b></span>")
            self.on_finished()

    def on_finished(self):
        self.start_btn.setEnabled(True); self.stop_btn.setEnabled(False)
        if self.worker and self.worker.is_running and self.progress_bar.value() >= 100:
            QMessageBox.information(self, "Done", self.texts[self.current_lang]["finish_msg"])
        self.worker = None
        self.save_settings()

    def save_settings(self):
        res_val = "none"
        if self.res_518.isChecked(): res_val = "518"
        elif self.res_512.isChecked(): res_val = "512"
        elif self.res_504.isChecked(): res_val = "504"
        elif self.res_392.isChecked(): res_val = "392"

        s = {"lang": self.current_lang, "input": self.input_edit.text(), "output": self.output_edit.text(),
             "use_filter": self.use_filter_check.isChecked(), "res_mode": res_val,
             "aspect": "NONE", "blur": self.blur_spin.value(), "sigmar": self.sigmar_spin.value(), "auto": self.auto_check.isChecked(),
             "ext": self.ext_combo.currentText(), "codec": self.codec_combo.currentText(), "crf": self.crf_spin.value(), 
             "preset": self.preset_combo.currentText()} # 프리셋 저장
        with open(self.config_file, 'w') as f: json.dump(s, f)

    def load_settings(self):
        if not os.path.exists(self.config_file):
            self.btn_lang_en.setChecked(True)
            self.update_presets() # 기본 프리셋 목록 생성
            self.preset_combo.setCurrentText("medium")
            return
        try:
            with open(self.config_file, 'r') as f: d = json.load(f)
            self.current_lang = d.get("lang", "EN")
            if self.current_lang == "EN": self.btn_lang_en.setChecked(True)
            else: self.btn_lang_ko.setChecked(True)

            self.input_edit.setText(d.get("input","")); self.output_edit.setText(d.get("output",""))
            self.use_filter_check.setChecked(d.get("use_filter", False))
            res = d.get("res_mode", "none")
            if res=="518": self.res_518.setChecked(True)
            elif res=="512": self.res_512.setChecked(True)
            elif res=="504": self.res_504.setChecked(True)
            elif res=="392": self.res_392.setChecked(True)
            else: self.res_none.setChecked(True)
            
            self.blur_spin.setValue(d.get("blur", 0.50))
            self.auto_check.setChecked(d.get("auto", True))
            if not d.get("auto"): self.sigmar_spin.setValue(d.get("sigmar", 0.020))
            self.ext_combo.setCurrentText(d.get("ext", "mp4"))
            
            # 프리셋 로드 핵심 로직
            self.codec_combo.setCurrentText(d.get("codec", "libx265"))
            self.update_presets() # 코덱에 맞는 목록 먼저 생성
            saved_preset = d.get("preset", "medium")
            # 목록에 저장된 프리셋이 있는지 확인 후 설정
            if self.preset_combo.findText(saved_preset) >= 0:
                self.preset_combo.setCurrentText(saved_preset)
            
            self.crf_spin.setValue(d.get("crf", 18))
        except: 
            self.btn_lang_en.setChecked(True)
            self.update_presets()

    def closeEvent(self, e): self.save_settings(); e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setStyle(QStyleFactory.create("Fusion"))
    window = MainWindow(); window.show(); sys.exit(app.exec())