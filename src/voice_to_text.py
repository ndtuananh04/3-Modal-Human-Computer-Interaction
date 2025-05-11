import threading
import pyaudio
import wave
import whisper
import numpy as np
import time
import os
import tempfile
import pyautogui

class VoiceToText:
    def __init__(self, model_name="small", on_status_change=None):
        """Khởi tạo đối tượng Voice to Text.
        
        Args:
            model_name: Tên model Whisper (tiny, base, small, medium, large)
            on_status_change: Callback để cập nhật trạng thái ghi âm
        """
        self.model_name = model_name
        self.model = None
        
        # Cấu hình ghi âm
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.is_recording = False
        self.frames = []
        self.audio_thread = None
        self.audio = pyaudio.PyAudio()
        
        # Callbacks
        self.on_transcription_done = None
        self.on_status_change = on_status_change
        
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
        self.frames = []
        self.audio_thread = threading.Thread(target=self._record_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
        # Thông báo trạng thái nếu có callback
        if self.on_status_change:
            self.on_status_change("Recording Voice...")
        
        return True
    
    def _record_audio(self):
        """Quá trình ghi âm trong thread riêng"""
        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            print("Đang ghi âm...")
            
            while self.is_recording:
                data = stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
            
            stream.stop_stream()
            stream.close()
            print("Ghi âm kết thúc...")
        
        except Exception as e:
            print(f"Lỗi trong quá trình ghi âm: {e}")
            self.is_recording = False
            if self.on_status_change:
                self.on_status_change("Recording Error")
    
    def stop_recording(self, process_audio=True):
        """Dừng ghi âm và chuyển đổi thành văn bản."""
        if not self.is_recording:
            return False
        
        self.is_recording = False
        
        # Đợi audio thread kết thúc
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2.0)
        
        # Thông báo đang xử lý
        if self.on_status_change:
            self.on_status_change("Processing Voice...")
        
        if process_audio and self.frames:
            # Xử lý audio trong thread riêng để không block UI
            threading.Thread(target=self._process_audio).start()
        else:
            # Nếu không xử lý audio, đặt lại trạng thái
            if self.on_status_change:
                self.on_status_change("Not Recording")
        
        return True
    
    def _process_audio(self):
        """Xử lý audio đã ghi và chuyển đổi thành văn bản."""
        if not self.frames:
            print("Không có dữ liệu âm thanh để xử lý")
            if self.on_status_change:
                self.on_status_change("Not Recording")
            return
        
        try:
            # Lưu tạm file WAV
            temp_dir = tempfile.gettempdir()
            temp_wav = os.path.join(temp_dir, "recording.wav")
            
            wf = wave.open(temp_wav, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            print("Đang xử lý âm thanh thành văn bản...")
            
            # Xử lý với Whisper
            result = self.model.transcribe(temp_wav, language="vi")
            text = result["text"].strip()
            
            print(f"Kết quả: {text}")
            
            # Gọi callback nếu có
            if self.on_transcription_done:
                self.on_transcription_done(text)
            
            # Xóa file tạm
            try:
                os.remove(temp_wav)
            except:
                pass
            
            # Cập nhật trạng thái
            if self.on_status_change:
                self.on_status_change("Not Recording")
                
        except Exception as e:
            print(f"Lỗi khi xử lý âm thanh: {e}")
            if self.on_status_change:
                self.on_status_change("Processing Error")
    
    def transcribe_and_type(self, text, text_widget=None):
        """Hiển thị văn bản trong widget và gõ vào vị trí con trỏ hiện tại."""
        # Hiển thị văn bản trong widget nếu có
        if text_widget:
            try:
                text_widget.delete(1.0, "end")
                text_widget.insert("end", text)
            except Exception as e:
                print(f"Lỗi khi hiển thị văn bản: {e}")
        
        # Gõ văn bản vào vị trí con trỏ chuột hiện tại
        try:
            pyautogui.typewrite(text)
        except Exception as e:
            print(f"Lỗi khi gõ văn bản: {e}")
    
    def __del__(self):
        """Giải phóng tài nguyên khi đối tượng bị hủy."""
        if self.is_recording:
            self.stop_recording(process_audio=False)
        
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()