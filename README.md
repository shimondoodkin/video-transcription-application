# Video Transcription Application

This application is designed to transcribe video files into text using Google's Speech-to-Text API. It is particularly useful for generating subtitles for videos. The application supports multiple languages and provides a graphical user interface for easy use.

## Features

- Transcribes video files into text.
- Supports multiple languages.
- Converts video files to audio for transcription.
- Provides a graphical user interface for easy use.
- Generates subtitle files in SRT format.

## Setup

### Install Python Dependencies

You need to install the following Python packages:

""""bash
pip install --upgrade google-cloud-speech google-cloud-storage srt pydub
""""

### Install FFmpeg

Ensure that `ffmpeg` is installed. 

Example installation of FFmpeg for Windows:

FFmpeg executable should be available in path. However, we can reuse a directory which is already in path, for example, the Python scripts folder.

1. Download FFmpeg from [here](https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip).
2. Extract the files from the `bin` folder (exe files only without folders) and put them into `c:\Python\Scripts\`.
3. Now you have FFmpeg available from Python.
   
### Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the Speech-to-Text API for your project.
4. Create a new service account.
5. Download the JSON key for the service account and rename it to `credentials.json`. Place this file in the same directory as the Python script.
6. Create a new storage bucket named `video-subtitles`.
7. Add a lifecycle rule to the bucket to delete files after 1 day.
8. Grant the service account the `Storage Object Admin` role for the bucket.

Detailed instructions for each step are provided below.

#### Create a New Project

- Go to [Google Cloud Console](https://console.cloud.google.com/).
- Create a new project (from the dropdown-select-box at the top left, with 3 dots inside it, then click the new project button at the popup dialog).
- Name the project (for example, "transcribe video").
- After the project is created, select the project from the project selection dropdown at the top left.

#### Enable the Speech-to-Text API

- In the top text input search box, type: "speech".
- Select: "Audio to text & text to audio conversion".
- In "Advanced transcription, powered by Google’s AI", click "Enable API".

#### Create a New Service Account

- Click on the menu (3 lines at the top left).
- Select "IAM & Admin" > "Service Accounts".
- Name the service account (for example, "captions py").
- Click the "Create and Continue" button.
- Click the "Done" button (the current role is owner, no need to change, no need to grant other users access to this account).

#### Download the JSON Key for the Service Account

- In the service accounts list, manage keys for the created account (on the item in the 3 dots menu aside to the account item, select from the menu "Manage Keys").
- In "Manage Keys" for the account, click the "Add Key" button. Select from the menu: "Create New Key".
- Select "JSON".
- You will download a JSON file.
- Rename the downloaded file to `credentials.json` and place it in the same directory as the Python script.

#### Create a New Storage Bucket

- Click on the menu, 3 lines on the top left.
- Go to "Cloud Storage" -> "Buckets".
- Click the "Create New" button.
- Name the bucket `video-subtitles`.
- Choose a region. A single region is good enough. For Israel, a region in Europe is good.
- Set the storage class to "Standard".
- Enforce public access prevention on this bucket.
- In the "Lifecycle" tab, add a rule to delete files after 1 day.

#### Grant the Service Account Access to the Bucket

- Open "IAM" in a new tab and find out your name of the service account (for example, `captions-py@transcribe-video-393321.iam.gserviceaccount.com`).
- Go back to storage. In "Bucket Details" (our bucket is `video-subtitles`), in the "Permissions" tab, click the "Grant Access" button.
- Enter the name of the service account in "Add Principals" and click on the found item in the dropdown list.
- Select the role: "Cloud Storage" > "Storage Object Admin".
- Click "Save".

Now you are ready to run the application!
