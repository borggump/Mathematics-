
import speech_recognition as sr
import pyaudio

def speech_to_text():
    # Initialize recognizer
    recognizer = sr.Recognizer()

    # Use the default microphone as the audio source
    with sr.Microphone() as source:
        print("Adjusting for ambient noise. Please wait...")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Ready! Please start speaking.")

        try:
            # Listen for speech and convert to audio data
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=15)
            print("Speech detected. Processing...")

            # Use Google Speech Recognition to convert audio to text
            text = recognizer.recognize_google(audio)
            print("You said: " + text)
            return text

        except sr.WaitTimeoutError:
            print("No speech detected within the timeout period.")
        except sr.UnknownValueError:
            print("Sorry, I couldn't understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

def main():
    while True:
        choice = input("Press Enter to start speech recognition, or 'q' to quit: ")
        if choice.lower() == 'q':
            break
        speech_to_text()

if __name__ == "__main__":
    main() b
