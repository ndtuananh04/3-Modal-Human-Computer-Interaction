import os
import time
import threading
import numpy as np
import pyaudio
import wave
import whisper
import keyboard
import pyautogui
from tempfile import NamedTemporaryFile

class VoiceToText:
    def __init__(self, model_name="small"):
        """
        Khởi tạo module voice-to-text
        
        Args:
            model_name: Kích thước model Whisper ("tiny", "base", "small", "medium", "large")
        """
        self.is_recording = False
        self.audio_thread = None
        self.audio_file = None
        self.last_transcript = ""
        self.model = None
        self.model_name = model_name
        
        # Thông số ghi âm
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.recording_time = 5  # Thời gian tối đa ghi âm (giây)
        
        # Khởi tạo PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Callback khi xử lý xong
        self.on_transcription_done = None
        
        # Tự động load model
        self.load_model()
    
    def load_model(self):
        """Tải model Whisper"""
        try:
            self.model = whisper.load_model(self.model_name)
            return True
        except Exception as e:
            print(f"Lỗi tải model Whisper: {e}")
            return False
    
    def start_recording(self):
        """Bắt đầu ghi âm"""
        if self.is_recording:
            return False
        
        self.is_recording = True
        self.audio_thread = threading.Thread(target=self._record_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        return True
    
    def stop_recording(self):
        """Dừng ghi âm và bắt đầu chuyển đổi thành văn bản"""
        if not self.is_recording:
            return False
        
        self.is_recording = False
        if self.audio_thread:
            self.audio_thread.join(timeout=1.0)
        
        # Chuyển đổi âm thanh thành văn bản trong thread khác
        threading.Thread(target=self._transcribe_audio, daemon=True).start()
        return True
    
    def _record_audio(self):
        """Ghi âm và lưu vào file tạm"""
        # Tạo file tạm để lưu âm thanh
        with NamedTemporaryFile(suffix=".wav", delete=False) as f:
            self.audio_file = f.name
        
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk
        )
        
        print("Đang ghi âm...")
        frames = []
        start_time = time.time()
        
        while self.is_recording and (time.time() - start_time) < self.recording_time:
            data = stream.read(self.chunk)
            frames.append(data)
        
        print("Ghi âm kết thúc!")
        
        # Dừng và đóng stream
        stream.stop_stream()
        stream.close()
        
        # Lưu file âm thanh
        wf = wave.open(self.audio_file, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
    
    def _transcribe_audio(self):
        """Chuyển đổi âm thanh thành văn bản"""
        if not self.audio_file or not os.path.exists(self.audio_file):
            print("Không tìm thấy file âm thanh!")
            return
        
        try:
            print("Đang chuyển đổi âm thanh thành văn bản...")
            result = self.model.transcribe(self.audio_file)
            self.last_transcript = result["text"].strip()
            print(f"Kết quả: {self.last_transcript}")
            
            # Xóa file tạm
            try:
                os.unlink(self.audio_file)
                self.audio_file = None
            except:
                pass
            
            # Gọi callback nếu có
            if self.on_transcription_done:
                self.on_transcription_done(self.last_transcript)
            
            # Tự động nhập văn bản tại vị trí con trỏ
            self.type_text(self.last_transcript)
            
        except Exception as e:
            print(f"Lỗi khi chuyển đổi âm thanh: {e}")
    
    def type_text(self, text):
        """Nhập văn bản vào vị trí con trỏ hiện tại"""
        if not text:
            return
        
        pyautogui.typewrite(text)
    
    def close(self):
        """Giải phóng tài nguyên"""
        if self.is_recording:
            self.stop_recording()
        
        if self.audio:
            self.audio.terminate()
            
        if self.audio_file and os.path.exists(self.audio_file):
            try:
                os.unlink(self.audio_file)
            except:
                pass