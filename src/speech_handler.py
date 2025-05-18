import time

class SpeechHandler:
    def __init__(self, voice_to_text, cooldown=1):
        self.voice_to_text = voice_to_text
        self.cooldown = cooldown
        self.last_mouth_open_time = 0
    
    def handle_mouth_open(self, mouth_is_open):
        """
        Xử lý cử chỉ mở miệng để bắt đầu/dừng ghi âm.
        
        Args:
            mouth_is_open: Có phát hiện miệng mở không
            
        Returns:
            str: Trạng thái hiện tại ("recording_started", "recording_stopped", "")
        """
        if not mouth_is_open:
            return ""
            
        curr_time = time.time()
        
        # Chỉ xử lý nếu đã qua thời gian cooldown
        if curr_time - self.last_mouth_open_time <= self.cooldown:
            return ""
            
        # Đánh dấu thời điểm mở miệng
        self.last_mouth_open_time = curr_time
        
        if not self.voice_to_text.is_recording:
            # Nếu chưa ghi âm -> bắt đầu ghi
            self.voice_to_text.start_recording()
            return "recording_started"
        else:
            # Nếu đang ghi âm -> dừng ghi và xử lý
            self.voice_to_text.stop_recording()
            return "recording_stopped"
    
    def set_transcription_callback(self, callback):
        """Thiết lập callback khi nhận dạng hoàn tất."""
        self.voice_to_text.on_transcription_done = callback
    
    def set_status_callback(self, callback):
        """Thiết lập callback cập nhật trạng thái."""
        self.voice_to_text.on_status_change = callback
    
    def cleanup(self):
        """Dọn dẹp tài nguyên."""
        if self.voice_to_text.is_recording:
            self.voice_to_text.stop_recording(process_audio=False)