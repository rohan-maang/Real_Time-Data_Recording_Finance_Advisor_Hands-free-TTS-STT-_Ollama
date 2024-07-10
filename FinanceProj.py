import sys
import os
import pandas as pd
import ollama
import pyaudio
import audioop
import wave
import assemblyai as aai
import numpy as np
import subprocess
from queue import Queue
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel, QLineEdit, QMessageBox, QHBoxLayout, QFrame
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QTextCursor, QPainter, QColor, QFont

api_key = "cd9a77d105ad4036b017b090cd7df9d1"
aai.settings.api_key = api_key
transcriber = aai.Transcriber()

context = []
welcome = 'Welcome, Im Sandy, your finance advisor. Let\'s get started.'

# Use subprocess to ensure the message is fully spoken before continuing
subprocess.call(['say', welcome])


class TokenStreamThread(QThread):
    token_received = pyqtSignal(str)
    complete_response = pyqtSignal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        global context
        context.append({'role': 'user', 'content': self.prompt})
        response_stream = ollama.chat(model='llama3', messages=context, stream=True)
        
        response_message = ''
        for chunk in response_stream:
            token = chunk['message']['content']
            response_message += token
            self.token_received.emit(token)
        
        context.append({'role': 'assistant', 'content': response_message})
        self.complete_response.emit(response_message)

class AudioVisualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.amplitude = [0] * 50  # Initialize with 50 zeros

    def update_amplitude(self, new_amplitude):
        self.amplitude.pop(0)
        self.amplitude.append(new_amplitude)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        width = self.width() / len(self.amplitude)
        for i, amp in enumerate(self.amplitude):
            painter.setBrush(QColor(100, 200, 255))
            painter.drawEllipse(i * width, self.height() / 2 - amp / 2, width - 2, amp)

class FinanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.data_file = "finance_data2.csv"
        self.user_df = self.load_data()
        self.user_data = {}
        self.recording_in_progress = False  # Flag to prevent multiple recordings
        
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Finance Advisor')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()
        self.setStyleSheet("background-color: black;")

        self.greeting_label = QLabel('Welcome! I am your finance advisor. Let\'s get started.')
        self.greeting_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white; font-family: 'Cursive';")
        layout.addWidget(self.greeting_label)

        self.response_area = QTextEdit(self)
        self.response_area.setReadOnly(True)
        self.response_area.setStyleSheet("background-color: black; color: white; font-size: 16px; padding: 10px; border-radius: 10px; font-weight: bold;")
        layout.addWidget(self.response_area)

        self.visualizer = AudioVisualizer()
        self.visualizer.setStyleSheet("background-color: black; border-radius: 10px;")
        layout.addWidget(self.visualizer)

        self.input_field = QLineEdit(self)
        self.input_field.setStyleSheet("font-size: 16px; padding: 10px; border: 2px solid #2e86de; border-radius: 5px;")
        layout.addWidget(self.input_field)

        self.query_button = QPushButton('Send', self)
        self.query_button.setStyleSheet("background-color: #2e86de; color: white; font-size: 16px; padding: 10px; border-radius: 5px;")
        self.query_button.clicked.connect(self.on_query)
        layout.addWidget(self.query_button)

        self.setLayout(layout)
        
        self.greet_user()

    def greet_user(self):
        greeting_prompt = '''You are an advisor appointed by Rohan to help the users to get their investment game straight. Gather the following information from the user:
                            - Name
                            - Age
                            - Investment Type
                            - Salary Percentage
                            - Market Scenario
                            - Risk Tolerance
                            - Current Inflation
                            - Inflation Volatility
                            - Salary Hike/Year

                            Start by greeting the user and then proceed to collect each piece of information in sequence.

                            Steps to follow:
                            1. Ask for their name.
                            2. Ask for their age.
                            3. Ask what type of investment they are interested in (stocks, bonds, cryptocurrency, real estate). Based on their answer, offer the following risk tolerance options:
                            - Stocks: High Volatility, Medium Volatility, Low Volatility
                            - Bonds: High Yield to Maturity, Medium Yield to Maturity, Low Yield to Maturity
                            - Real Estate: High Appreciation, Medium Appreciation, Low Appreciation
                            - Cryptocurrency: High Risk, Medium Risk, Low Risk
                            4. Ask for their salary in rupees and the percentage they plan to invest.
                            5. Inquire about their thoughts on the market scenario (Stable, Volatile, add according to your knowledge)
                            6. Ask about the current inflation rate (6-8%, 8-10%, 10-12%, Double/year)
                            7. Ask about inflation volatility (1-2%, 2-4%, 4-6%)
                            8. Ask about their annual salary hike (in percentage)
                            9. After gathering all the information, provide a direct and slightly rude possible outlook of their investments, you have to be candid and if their investment choices seem not good then make sure to scare them off so that they are precautionary.

                            When the user is done conversing with you, they will say "bye" or whatever that means end of the convo. Your final response should include the word "bye".
                            And have fun with the user, mock them a bit, nudge them a bit, enjoy your time here!'''
        self.ask(greeting_prompt)

    def load_data(self):
        if os.path.exists(self.data_file):
            return pd.read_csv(self.data_file)
        else:
            return pd.DataFrame(columns=["Index", "Name", "Age", "Investment Type", "Salary Percentage", "Market Scenario", "Risk Tolerance", "Current Inflation", "Inflation Volatility", "Salary Hike/Year"])

    def save_data(self):
        new_entry_df = pd.DataFrame([self.user_data])
        self.user_df = pd.concat([self.user_df, new_entry_df], ignore_index=True)
        self.user_df.to_csv(self.data_file, index=False)
        self.user_data = {}

    def ask(self, query):
        self.thread = TokenStreamThread(query)
        self.thread.token_received.connect(self.update_response_area)
        self.thread.complete_response.connect(self.speak_response)
        self.assistant_response_started = False  # Reset flag at the start of a new query
        self.thread.start()

    def update_response_area(self, token):
        self.response_area.moveCursor(QTextCursor.End)
        if not self.assistant_response_started:
            self.response_area.insertHtml('<span style="color: green;">Assistant:</span> ')
            self.assistant_response_started = True
        self.response_area.insertPlainText(token)

    def speak_response(self, response):
        os.system(f'say "{response}"')
        QTimer.singleShot(1000, self.start_recording)  # Delay before starting recording

    def start_recording(self):
        if not self.recording_in_progress:
            self.recording_in_progress = True
            self.recording_thread = RecordingThread()
            self.recording_thread.transcription_received.connect(self.handle_transcription)
            self.recording_thread.amplitude_received.connect(self.visualizer.update_amplitude)
            self.recording_thread.start()

    def handle_transcription(self, transcription):
        print(f"Transcription received: {transcription}")  # Debugging statement
        if transcription.strip():  # Check if transcription is not empty
            self.response_area.append(f"\nUser: {transcription}\n\n")
            self.ask(transcription)
        self.recording_in_progress = False

    def extract_information(self):
        extraction_prompt = f'''Now from this entire data find out the Name, Age etc and paste only the key info and not the whole sentence, just like this example:
                                Name: Rohan
                                Age: 24
                                Investment Type: Stocks
                                Salary Percentage: 50%
                                Market Scenario: Volatile
                                Risk Tolerance: Highly volatile
                                Current Inflation: 6-8%
                                Inflation Volatility: 2-4%
                                Salary Hike/Year: 3%
                                
                                Try not to add any stars (*) or any other character other than % which if involved in the users response'''

        final_context = context + [{'role': 'user', 'content': extraction_prompt}]
        response_stream = ollama.chat(model='llama3', messages=final_context, stream=True)
        
        extraction_response = ''
        for chunk in response_stream:
            extraction_response += chunk['message']['content']

        self.user_data = {}
        lines = extraction_response.split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                self.user_data[key.strip()] = value.strip()

    def on_query(self):
        query = self.input_field.text()
        self.input_field.clear()
        self.response_area.append(f"User: {query}\n")
        self.response_area.insertHtml(f'<span style="color: blue;">User: {query}\n</span> ')
        self.ask(query)
        if "bye" in query.lower():
            self.extract_information()
            self.save_data()
            QMessageBox.information(self, "Session Ended", "The conversation has ended and the data is saved successfully.")
            self.close()

class RecordingThread(QThread):
    transcription_received = pyqtSignal(str)
    amplitude_received = pyqtSignal(float)

    def run(self):
        audio_file = "user_input.wav"
        self.record_audio(audio_file)
        print(f"Audio file saved: {audio_file}")  # Debugging statement
        transcript = transcriber.transcribe(audio_file)
        print("Transcription process completed")  # Debugging statement
        self.transcription_received.emit(transcript.text)

    def record_audio(self, filename):
        chunk = 1024  # Record in chunks of 1024 samples
        sample_format = pyaudio.paInt16  # 16 bits per sample
        channels = 1
        fs = 44100  # Record at 44100 samples per second
        p = pyaudio.PyAudio()  # Create an interface to PortAudio

        print('Recording')

        stream = p.open(format=sample_format,
                        channels=channels,
                        rate=fs,
                        frames_per_buffer=chunk,
                        input=True)

        frames = []
        silence_threshold = 500  # Silence threshold for RMS
        silence_duration = 2  # Duration in seconds to consider as silence
        silence_chunks = int(fs / chunk * silence_duration)

        silent_chunks = 0

        while True:
            data = stream.read(chunk)
            frames.append(data)
            rms = audioop.rms(data, 2)
            self.amplitude_received.emit(rms)  # Send amplitude data for visualization
            if rms < silence_threshold:
                silent_chunks += 1
            else:
                silent_chunks = 0

            if silent_chunks >= silence_chunks:
                break

            if self.isInterruptionRequested():
                break

        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        # Terminate the PortAudio interface
        p.terminate()

        print('Finished recording')

        # Save the recorded data as a WAV file
        wf = wave.open(filename, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(sample_format))
        wf.setframerate(fs)
        wf.writeframes(b''.join(frames))
        wf.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    finance_app = FinanceApp()
    finance_app.show()
    sys.exit(app.exec_())