import os 
import RPi.GPIO as GPIO  
import pyaudio  
from vosk import Model, KaldiRecognizer  

# Here we have declared the Constants
LED_PIN = 18  # here we define the GPIO pin number connected to the LED (using BCM numbering)
MODEL_PATH = "/home/pi/vosk-model"  # it is the path to the Vosk speech recognition model directory 
AUDIO_RATE = 16000  # The sample rate 16 kHz that will be used for audio capture compatible with the Vosk model
BUFFER_SIZE = 4096  # Size of the audio bufferthat is how much audio data is captured per frame (4096 samples)

# Function to set up GPIO and configure the LED pin
def setup_gpio():
    """
    Configures the GPIO pins for controlling the LED.
    The LED is initially set to LOW (off).
    """
    GPIO.setmode(GPIO.BCM)  # Use the Broadcom (BCM) numbering scheme for referencing GPIO pins
    GPIO.setup(LED_PIN, GPIO.OUT)  # Configure the LED pin as an output pin (to control LED on/off state)
    GPIO.output(LED_PIN, GPIO.LOW)  # Initialize the LED to OFF (set the pin to LOW voltage)

# Function to initialize and set up the Vosk recognizer
def setup_recognizer():
    """
    Loads the Vosk speech recognition model from the specified path
    if the model path is invalid or missing, raise an error and exit
    """
    # Check if the model directory exists at the specified path
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("Please download the Vosk model and unpack it to the correct path.")  # Error if model is missing

    # Load the Vosk model (contains the language model and acoustic model for speech recognition)
    model = Model(MODEL_PATH)

    # Create a KaldiRecognizer object that will process audio data with the loaded model
    # '16000' is the expected audio sample rate
    return KaldiRecognizer(model, AUDIO_RATE)

# Function to initialize the PyAudio stream for microphone input
def setup_audio_stream():
    """
    Initializes the PyAudio stream for capturing audio input from the microphone in real time.
    The stream is set up with specific parameters: 16-bit depth, mono (1 channel), and 16kHz sample rate.
    """
    p = pyaudio.PyAudio()  # Create a PyAudio instance to manage audio input/output
    # Open an audio stream with the required format: 16-bit PCM, mono channel, 16kHz sample rate, with a buffer size of 4096 frames
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=AUDIO_RATE, input=True, frames_per_buffer=BUFFER_SIZE)
    stream.start_stream()  # Start the stream so that it is ready to capture audio data immediately
    return p, stream  # Return both the PyAudio instance and the audio stream for future use

# Function to handle recognized voice commands and control the LED
def handle_command(command_text):
    """
    Controls the LED based on the recognized voice command.
    If the recognized command contains 'on', it turns the LED on.
    If the recognized command contains 'off', it turns the LED off.
    
    Args:
        command_text (str): The recognized text from the speech input, typically in lowercase.
    """
    # Check if the recognized command contains the word "on"
    if "on" in command_text:
        print("Command recognized: Turning LED ON")  # Print feedback to the user that "on" command was detected
        GPIO.output(LED_PIN, GPIO.HIGH)  # Set the LED pin to HIGH, turning the LED on
    # Check if the recognized command contains the word "off"
    elif "off" in command_text:
        print("Command recognized: Turning LED OFF")  # Print feedback to the user that "off" command was detected
        GPIO.output(LED_PIN, GPIO.LOW)  # Set the LED pin to LOW, turning the LED off

# Main function to run the voice-controlled LED system
def main():
    """
    Main program function that sets up the GPIO, Vosk recognizer, and PyAudio stream.
    It continuously listens for speech commands to turn the LED on or off.
    """
    setup_gpio()  # Set up the GPIO system, configuring the LED pin and initializing the LED in the off state

    recognizer = setup_recognizer()  # Set up the Vosk speech recognizer by loading the language model from the model path

    p, stream = setup_audio_stream()  # Set up the PyAudio system and start the audio stream to capture the real time microphone input

    print("Listening for 'ON' or 'OFF' commands...")  # Inform the user that the system is ready and listening for commands

    try:
        # here we apply infinite loop to continuously capture audio and process speech commands
        while True:
            data = stream.read(BUFFER_SIZE)  # Capture a chunk of audio data (4096 samples) from the microphone

            # If no audio data is captured, continue to the next iteration (skip processing)
            if len(data) == 0:
                continue

            # Use the recognizer to analyze the audio data and check if a full command (phrase) has been recognized
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()  # Get the final result from the recognizer (a full recognized phrase in JSON format)
                print(f"Full result: {result}")  # Print the full recognition result for debugging

                # Convert the result to lowercase for easier comparison (optional step based on your JSON parsing)
                command_text = result.lower()

                # Call the handle_command function to process the recognized command ("on" or "off")
                handle_command(command_text)

            else:
                # If the recognizer has only recognized part of a phrase (not complete), get the partial result
                partial_result = recognizer.PartialResult()  # Get the partial result from the recognizer (in JSON format)
                print(f"Partial result: {partial_result}")  # Print the partial recognition result for debugging

    except KeyboardInterrupt:
        # Catch a keyboard interrupt (Ctrl+C) to allow the program to exit gracefully
        print("Program interrupted by user.")

    finally:
        # Always clean up GPIO and audio resources when exiting, regardless of how the program ended
        GPIO.cleanup()  # Reset the GPIO settings to their default state, ensuring no pins remain in output mode
        stream.stop_stream()  # Stop the audio stream to release the microphone resource
        stream.close()  # Close the stream to clean up the audio system properly
        p.terminate()  # Terminate the PyAudio instance, releasing all audio-related resources
        print("Cleaned up and exiting...")  # Print a final message indicating that cleanup is complete and the program is exiting

# Run the main function if this script is executed as the main program (not imported as a module)
if __name__ == "__main__":
    main()  # Start the main program
