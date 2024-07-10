
# Finance Advisor Application

## Overview
This project is a combined skill representation of data science (data handling, processing etc.), AI handling i.e. working with the model and bending it in a way to work the way the project requires.

The Finance Advisor Application is a GUI-based tool designed to interactively guide users through their financial planning and investment decisions. The application leverages various libraries and APIs for audio processing, speech-to-text transcription, and natural language processing.

It is a totally hands-free experience, the user does not have to type anything, and the user's speech will be transcribed using AssemblyAI's API key. The responses by the model will also be spoken out.  

## Features

- **Interactive Financial Guidance**: Provides personalized financial advice based on user input.
- **Speech Recognition**: Records user queries and transcribes them into text using AssemblyAI.
- **Real-time Response**: Uses the Ollama API for generating responses based on user input.
- **Audio Visualization**: Visualizes audio amplitude in real-time during recording.
- **Data Persistence**: Saves user data to a CSV file for future reference.

## Dependencies

The application requires the following Python libraries:

- `sys`
- `os`
- `pandas`
- `ollama`
- `pyaudio`
- `audioop`
- `wave`
- `assemblyai`
- `numpy`
- `subprocess`
- `queue`
- `PyQt5`

Ensure you have these libraries installed using `pip`:

```sh
pip install pandas ollama pyaudio assemblyai numpy PyQt5
```

## Setup

1. **API Key Configuration**:
   - Set your AssemblyAI API key in the `api_key` variable.
   ```python
   api_key = "your_api_key_here"
   ```

2. **Data File**:
   - Ensure you have a CSV file named `finance_data2.csv` in the same directory as the script. If it doesn't exist, the application will create it.

## Usage

1. **Run the Application**:
   - Execute the script to start the application.
   ```sh
   python finance_advisor.py
   ```

2. **Interact with the Advisor**:
   - The application will greet you and prompt you to input various financial details. 
   - You can type your responses or speak them into the microphone.
   - The advisor will provide feedback based on your input.

3. **End the Conversation**:
   - Type or say "bye" to end the session.
   - The application will save your data to the CSV file and close.

## Code Structure

- **FinanceApp Class**: Main application window handling user interaction and displaying responses.
- **TokenStreamThread Class**: Handles streaming responses from the Ollama API.
- **AudioVisualizer Class**: Visualizes audio amplitude during recording.
- **RecordingThread Class**: Handles audio recording and transcription.

## Notes

- The application uses the `say` command on macOS to provide audio feedback. Modify this part of the code if you're using a different operating system.
- The user data collected during the session is stored in a CSV file for future reference.

---

Feel free to customize the `README` file as per your requirements.
