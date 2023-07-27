
from sklearn.cluster import DBSCAN
import numpy as np
import srt
import datetime

# import pytube
import os
from traceback import print_exception
from google.cloud import storage
# import json
# import io
from google.cloud import speech_v1
# import google.cloud.exceptions
import subprocess
from pydub.utils import mediainfo
import subprocess
# import math
import datetime
import srt
import time

import pickle
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from threading import Thread
import os
#from dotenv import load_dotenv

# Load environment variables from .env file
# load_dotenv()

# Now you can access the environment variables using os.getenv
#BUCKET_NAME = os.getenv("BUCKET_NAME")
BUCKET_NAME = "video-subtitles" # update this with your bucket name
# link="https://www.youtube.com/watch?v=ImEnWAVRLU0"
#os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="credentials.json"


# def ensure_bucket_exists(bucket_name):
#     """Creates a new bucket if it does not already exist."""
#     try:
#         storage_client = storage.Client()
#         storage_client.get_bucket(bucket_name)
#     except google.cloud.exceptions.NotFound:
#         bucket = storage_client.create_bucket(bucket_name)
#            # Set lifecycle policy
#         rule = {
#             'action': {'type': 'Delete'},
#             'condition': {'age': 1}  # Age in days
#         }
#         bucket.lifecycle_rules = [rule]
#         bucket.update()
# ensure_bucket_exists(BUCKET_NAME)

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    # bucket_name = "your-bucket-name"
    # source_file_name = "local/path/to/file"
    # destination_blob_name = "storage-object-name"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )

def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()
    
#def download_video(link):
#    try: 
#        #object creation using YouTube which was imported in the beginning 
#        yt = pytube.YouTube(link) 
#    except: 
#        print("Connection Error") #to handle exception 
#    video_path = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()
#    
#    # rename the path
#    new_path = video_path.split('/')
#    new_filename = f"video.mp4"
#    new_path[-1]= new_filename
#    new_path='/'.join(new_path)
#    os.rename(video_path, new_path)
#        
#    return new_path

def video_info(video_filepath):
    """ this function returns number of channels, bit rate, and sample rate of the video"""

    video_data = mediainfo(video_filepath)
    channels = video_data["channels"]
    bit_rate = video_data["bit_rate"]
    sample_rate = video_data["sample_rate"]

    return channels, bit_rate, sample_rate

def video_to_audio(video_filepath, audio_filename, video_channels, video_bit_rate, video_sample_rate):
    # Check if temporary audio file exists and delete it if it does
    if os.path.exists(audio_filename):
        os.remove(audio_filename)
        
    command = f"ffmpeg -i \"{video_filepath}\" -b:a {video_bit_rate} -ac {video_channels} -ar {video_sample_rate} -vn \"{audio_filename}\""
    subprocess.call(command, shell=True)
    
    return audio_filename

def upload_audio(audio_filename):
    
    # Create a unique blob name by prepending the current time to the audio_filename
    timestamp = int(time.time())
    blob_name = f"{timestamp}_{audio_filename}"
    upload_blob(BUCKET_NAME, audio_filename, blob_name)
    
    # Delete the temporary audio file after uploading
    os.remove(audio_filename)
    
    return blob_name

def do_long_running_recognize(storage_uri, channels, sample_rate, language_code):
    
    client = speech_v1.SpeechClient()
    
    
    config = {
        "language_code": language_code,
        "sample_rate_hertz": int(sample_rate),
        "encoding": speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
        "audio_channel_count": int(channels),
        "enable_word_time_offsets": True,
        # "model": "video", # an enhanced model choice is possible but hebrew does not support video , search a language see models avalible https://cloud.google.com/speech-to-text/docs/speech-to-text-supported-languages
        "enable_automatic_punctuation":True
    }
    
    audio = {"uri": storage_uri}

    operation = client.long_running_recognize(config=config, audio=audio)

    print(u"Waiting for operation to complete...")
    response = operation.result()
    return response


def subtitle_generation_old_algorithm(response, bin_size=3):
    """We define a bin of time period to display the words in sync with audio. 
    Here, bin_size = 3 means each bin is of 3 secs. 
    All the words in the interval of 3 secs in result will be grouped togather."""
    transcriptions = []
    index = 0
 
    for result in response.results:
        try:
            if result.alternatives[0].words[0].start_time.seconds:
                # bin start -> for first word of result
                start_sec = result.alternatives[0].words[0].start_time.seconds 
                start_microsec = result.alternatives[0].words[0].start_time.microseconds
            else:
                # bin start -> For First word of response
                start_sec = 0
                start_microsec = 0 
            end_sec = start_sec + bin_size # bin end sec
            
            # for last word of result
            last_word_end_sec = result.alternatives[0].words[-1].end_time.seconds
            last_word_end_microsec = result.alternatives[0].words[-1].end_time.microseconds
            
            # bin transcript
            transcript = result.alternatives[0].words[0].word
            
            index += 1 # subtitle index

            for i in range(len(result.alternatives[0].words) - 1):
                try:
                    word = result.alternatives[0].words[i + 1].word
                    word_start_sec = result.alternatives[0].words[i + 1].start_time.seconds
                    word_start_microsec = result.alternatives[0].words[i + 1].start_time.microseconds # 0.001 to convert nana -> micro
                    word_end_sec = result.alternatives[0].words[i + 1].end_time.seconds
                    word_end_microsec = result.alternatives[0].words[i + 1].end_time.microseconds

                    if word_end_sec < end_sec:
                        transcript = transcript + " " + word
                    else:
                        previous_word_end_sec = result.alternatives[0].words[i].end_time.seconds
                        previous_word_end_microsec = result.alternatives[0].words[i].end_time.microseconds
                        
                        # append bin transcript
                        transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, start_sec, start_microsec), datetime.timedelta(0, previous_word_end_sec, previous_word_end_microsec), transcript))
                        
                        # reset bin parameters
                        start_sec = word_start_sec
                        start_microsec = word_start_microsec
                        end_sec = start_sec + bin_size
                        transcript = result.alternatives[0].words[i + 1].word
                        
                        index += 1
                except IndexError:
                    pass
            # append transcript of last transcript in bin
            transcriptions.append(srt.Subtitle(index, datetime.timedelta(0, start_sec, start_microsec), datetime.timedelta(0, last_word_end_sec, last_word_end_microsec), transcript))
            index += 1
        except IndexError:
            pass
    
    # turn transcription list into subtitles
    subtitles = srt.compose(transcriptions)
    return subtitles


def calculate_eps(time_diffs):
    # elbow method
    
    # Sort the time differences
    sorted_diffs = np.sort(time_diffs)

    # Create the coordinates for the line
    x = np.arange(len(sorted_diffs))
    y = sorted_diffs

    # Calculate the line from first to last point
    first_point = np.array([0, y[0]])
    last_point = np.array([len(y) - 1, y[-1]])
    line = np.poly1d(np.polyfit(x, y, 1))

    # Calculate the distance from each point to the line
    distances = np.abs(y - line(x))

    # Find the index of the maximum distance
    max_distance_index = np.argmax(distances)

    # Return the corresponding time difference
    # make it little higher than last small distance  but less than first large distance, midway between them.
    eps=sorted_diffs[max_distance_index]+((sorted_diffs[max_distance_index+1]-sorted_diffs[max_distance_index])/2)
    
    return eps

def subtitle_generation(response, min_group_size=3, max_group_size=5):
    # First pass: group words that are close together in time using DBSCAN
    words = [word for result in response.results for word in result.alternatives[0].words]
    time_diffs = np.array([ (words[i+1].start_time.total_seconds() - words[i].end_time.total_seconds())*1_000_000 for i in range(len(words) - 1)])
    
    eps = calculate_eps(time_diffs)
    times = np.cumsum(time_diffs)
    
    db = DBSCAN(eps=eps, min_samples=1).fit(times.reshape(-1, 1))
    labels = db.labels_
    groups = []
    current_group = [words[0]]
    current_group_name = labels[0]
    
    for i in range(1,len(words)):
        current_group_label=labels[i-1] 
        if current_group_name == current_group_label:  # -1 label is for noise
            current_group.append(words[i])
        else:
            groups.append(current_group)
            current_group = [words[i]]
            current_group_name = current_group_label
    groups.append(current_group)

    # Second pass: break groups into chunks of up to max_group_size words
    transcriptions = []
    index = 1
    for group in groups:
        i = 0
        while i < len(group):
            if i + max_group_size < len(group) or i + min_group_size > len(group):
                chunk_size = max_group_size
            else:
                chunk_size = len(group) - i
            chunk = group[i:i+chunk_size]
            start_time = datetime.timedelta(0, chunk[0].start_time.seconds, chunk[0].start_time.microseconds)
            end_time = datetime.timedelta(0, chunk[-1].end_time.seconds, chunk[-1].end_time.microseconds)
            transcript = " ".join(word.word for word in chunk)
            transcriptions.append(srt.Subtitle(index, start_time, end_time, transcript))
            index += 1
            i += chunk_size

    # turn transcription list into subtitles
    subtitles = srt.compose(transcriptions)
    return subtitles



class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()
        self.cancelled = False

    def create_widgets(self):
        
        
        # languages = [
        #     "af-ZA", "am-ET", "hy-AM", "az-AZ", "id-ID", "ms-MY", "bn-BD", "bn-IN", "ca-ES",
        #     "cs-CZ", "da-DK", "de-DE", "en-AU", "en-CA", "en-GH", "en-GB", "en-IN", "en-IE",
        #     "en-KE", "en-NZ", "en-NG", "en-PH", "en-ZA", "en-TZ", "en-US", "es-AR", "es-BO",
        #     "es-CL", "es-CO", "es-CR", "es-EC", "es-SV", "es-ES", "es-US", "es-GT", "es-HN",
        #     "es-MX", "es-NI", "es-PA", "es-PY", "es-PE", "es-PR", "es-DO", "es-UY", "es-VE",
        #     "eu-ES", "fil-PH", "fr-CA", "fr-FR", "gl-ES", "ka-GE", "gu-IN", "hr-HR", "zu-ZA",
        #     "is-IS", "it-IT", "jv-ID", "kn-IN", "km-KH", "lo-LA", "lv-LV", "lt-LT", "hu-HU",
        #     "ml-IN", "mr-IN", "nl-NL", "ne-NP", "nb-NO", "pl-PL", "pt-BR", "pt-PT", "pa-IN",
        #     "ro-RO", "si-LK", "sk-SK", "sl-SI", "su-ID", "sw-TZ", "sw-KE", "fi-FI", "sv-SE",
        #     "ta-IN", "ta-SG", "ta-LK", "ta-MY", "te-IN", "vi-VN", "tr-TR", "ur-PK", "ur-IN",
        #     "el-GR", "bg-BG", "ru-RU", "sr-RS", "uk-UA", "he-IL", "ar-IL", "ar-JO", "ar-AE",
        #     "ar-BH", "ar-DZ", "ar-SA", "ar-IQ", "ar-KW", "ar-MA", "ar-TN", "ar-OM", "ar-PS",
        #     "ar-QA", "ar-LB", "ar-EG", "fa-IR", "hi-IN", "th-TH", "ko-KR", "cmn-Hant-TW",
        #     "yue-Hant-HK", "ja-JP", "cmn-Hans-HK", "cmn-Hans-CN"
        # ]
        
        self.language_var = tk.StringVar(self)
        self.language_var.set("iw-IL")  # default value
        self.languages = ["iw-IL", "en-US", "ru-RU"]  # add more languages as needed
        self.language_menu = tk.OptionMenu(self, self.language_var, *self.languages)
        self.language_menu.pack(side="top")
        
        self.start_button = tk.Button(self)
        self.start_button["text"] = "Browse.. Start"
        self.start_button["command"] = self.start_process
        self.start_button["state"] = "normal"
        self.start_button.pack(side="top")

        self.progress = ttk.Progressbar(self, length=200)
        self.progress.pack(side="top")

        self.cancel_button = tk.Button(self)
        self.cancel_button["text"] = "Cancel"
        self.cancel_button["state"] = "disabled"
        self.cancel_button["command"] = self.cancel_process
        self.cancel_button.pack(side="top")

        self.status_label = tk.Label(self, text="")
        self.status_label.pack(side="top")

    def load_file(self):
        self.filename = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.flv")])
        
        self.cancel_button["state"] = "disabled"

    def start_process(self):
        self.load_file()
        if not self.filename:
            return
        self.cancelled = False
        self.start_button["state"] = "disabled"
        self.cancel_button["state"] = "normal"
        self.thread = Thread(target=self.run_process)
        self.thread.start()

    def run_process(self):
        try:
            video_path = self.filename
            if self.cancelled: return

            channels, bit_rate, sample_rate = self.get_video_info(video_path)
            if self.cancelled: return

            filename = self.convert_video_to_audio(video_path, channels, bit_rate, sample_rate)
            if self.cancelled: return

            blob_name = self.upload_audio(filename)
            if self.cancelled: return

            response = self.recognize_speech(blob_name, channels, sample_rate, self.language_var.get())
                        
            # for debugging: save result , then comment out previous two functions and load result instead of them while debugging multiple times next time
            
            # with open('recognize_speech_response.pkl', 'wb') as file:
            #     pickle.dump(response, file)
            
            # with open('recognize_speech_response.pkl', 'rb') as file:
            #     response = pickle.load(file)
        
            if self.cancelled: return

            self.generate_subtitles(response)
            if self.cancelled: return

        except Exception as e:
            print_exception(e)
            self.status_label["text"] = f"An error occurred: {e}"
        finally:
            self.start_button["state"] = "normal"
            self.cancel_button["state"] = "disabled"
            if self.cancelled:
                self.status_label["text"] = "Process cancelled."
                # Delete intermediate files
                if os.path.exists("audio.wav"):
                    os.remove("audio.wav")

    def get_video_info(self, video_path):
        self.status_label["text"] = "Getting video info..."
        channels, bit_rate, sample_rate = video_info(video_path)
        self.progress["value"] = 40
        return channels, bit_rate, sample_rate

    def convert_video_to_audio(self, video_path, channels, bit_rate, sample_rate):
        self.status_label["text"] = "Converting video to audio..."
        filename = video_to_audio(video_path, "audio.wav", channels, bit_rate, sample_rate)
        self.status_label["text"] = "Converted video to audio..."
        self.progress["value"] = 60
        return filename
    
    def upload_audio(self, filename):
        self.status_label["text"] = "Uploading audio..."
        blob_name = upload_audio(filename)
        self.status_label["text"] = "Uploaded audio"
        self.progress["value"] = 70
        return blob_name

    def recognize_speech(self, blob_name, channels, sample_rate, language_code):
        self.status_label["text"] = "Recognizing speech..."
        gcs_uri = f"gs://{BUCKET_NAME}/{blob_name}"
        response = do_long_running_recognize(gcs_uri, channels, sample_rate, language_code)
        self.status_label["text"] = "Recognized speech..."
        
        self.progress["value"] = 80
        return response

    def generate_subtitles(self, response):
        self.status_label["text"] = "Generating subtitles..."
        subtitles = subtitle_generation(response)
        self.progress["value"] = 100
        with open("subtitles.srt", "w", encoding='utf-8') as f:
            f.write(subtitles)
        self.status_label["text"] = "Subtitles generated successfully."

    def cancel_process(self):
        self.cancelled = True

root = tk.Tk()
app = Application(master=root)
app.mainloop()
