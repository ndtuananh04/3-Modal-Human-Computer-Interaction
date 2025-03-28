import speech_recognition as sr
import time

# Initialize recognizer
recognizer = sr.Recognizer()

# Adjust for ambient noise and microphone sensitivity
with sr.Microphone() as source:
    print("Adjusting for ambient noise... Please wait...")
    recognizer.adjust_for_ambient_noise(source, duration=2)
    print("Ready to listen!")

def listen_continuously():
    while True:
        with sr.Microphone() as source:
            try:
                print("\nListening...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                
                # Recognize speech using Google Speech Recognition
                text = recognizer.recognize_google(audio, language="vi-VN")
                print("Bạn đã nói: " + text)
                
            except sr.WaitTimeoutError:
                print("No speech detected within timeout")
                continue
            except sr.UnknownValueError:
                print("Không thể nhận diện được giọng nói")
                continue
            except sr.RequestError as e:
                print(f"Lỗi kết nối tới dịch vụ Google: {e}")
                time.sleep(1)  # Wait before retrying
                continue
            except Exception as e:
                print(f"Error occurred: {e}")
                continue

if __name__ == "__main__":
    try:
        listen_continuously()
    except KeyboardInterrupt:
        print("\nStopped by user")