# YouTube Scheduler and Uploader

## Description

This project is a Python-based application designed to automate the process of uploading videos to YouTube. It allows users to schedule uploads and provide video metadata through a CSV file. The application uses the YouTube Data API for interacting with YouTube.

## Features

This script offers a comprehensive solution for automating YouTube video uploads:

*   **Automated Video Uploads:** Leverages the YouTube Data API v3 to upload videos to your channel.
*   **OAuth 2.0 Authentication:** Securely authenticates using your `client_secret.json` file and stores session tokens in `token.pickle` for subsequent runs.
*   **Advanced CSV-Based Metadata & Schedule Management (`video_metadata.csv`):**
    *   **Centralized Control:** All video details (filename, desired upload date/time, title, description, tags) are managed through a single CSV file.
    *   **Automatic Row Generation for New Videos:** The script scans the `videos/` folder and automatically adds entries to the CSV for any new video files it finds.
    *   **Intelligent Title Pre-filling:** The `Title` field in the CSV is automatically pre-filled using the video's filename (without the extension), which you can then customize.
    *   **Automated Scheduling & Sequencing:**
        *   New videos are assigned an `UploadDate` sequentially, starting from today or the latest date already present in the CSV.
        *   A random `UploadTime` (currently configured between 4:30 PM and 6:30 PM local time) is assigned to new video entries, helping to mimic organic upload patterns.
    *   **Flexible Date Input:** The script attempts to parse various common date formats (e.g., MM/DD/YY, DD-MM-YYYY) from the CSV and normalizes them to `YYYY-MM-DD`.
    *   **Upload Status Tracking:** An `Uploaded` column in the CSV is updated to 'Yes' after a video is successfully processed, preventing re-uploads.
*   **Precise YouTube Scheduling:**
    *   Videos are uploaded as 'private' and scheduled to go public at the `UploadDate` and `UploadTime` specified in the CSV. The script handles the conversion to the required ISO 8601 UTC format for YouTube's `publishAt` field.
*   **Pre-Upload Metadata Validation:** Before attempting an upload, the script checks if essential fields (`Title`, `Description`, `Tags`) are filled in the CSV for videos due to be uploaded. It will alert you if information is missing.
*   **Video File Management:**
    *   Automatically detects video files (common formats like .mp4, .mov, .avi, etc.) within a designated `videos/` folder.
    *   The `videos/` folder is created automatically if it doesn't exist.
*   **Comprehensive YouTube Video Settings:**
    *   Sets video title, description, and tags.
    *   Assigns a default category ("People & Blogs", ID 22) and language ("en-US").
    *   Explicitly marks videos as "not made for kids".
    *   Sets the `recordingDate` on YouTube based on the `UploadDate` from the CSV, which can be useful for YouTube's metadata.
*   **Robust Uploading:**
    *   Utilizes resumable uploads, making it efficient for large files.
    *   Includes a retry mechanism for common intermittent HTTP errors (e.g., 500, 503) that can occur during the upload process.
*   **User-Friendly Execution:**
    *   Comes with a `run_youtube_uploader.command` script for easy execution on macOS.
    *   Provides clear console logging of its operations, progress, and any errors encountered, including a final summary.

## Requirements

*   Python 3.x
*   Google API Client Library for Python:
    *   `google-api-python-client`
    *   `google-auth-oauthlib`
    *   `google-auth-httplib2`
*   A `client_secret.json` file obtained from the Google Developers Console with access to the YouTube Data API v3.
*   A `video_metadata.csv` file with details for the videos to be uploaded.

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/MasoomChoudhury/YouTube-Scheduler-and-Uploader.git
    cd YouTube-Scheduler-and-Uploader
    ```

2.  **Install Dependencies:**
    It's recommended to use a virtual environment:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install google-api-python-client google-auth-oauthlib google-auth-httplib2 pandas 
    # Assuming pandas might be used for CSV handling, if not, remove it.
    ```

3.  **Obtain Your `client_secret.json` (Google API Credentials):**
    This file is essential for the application to communicate with YouTube on your behalf. **Do not share your `client_secret.json` file publicly or commit it to Git.**
    *   **Navigate to Google Developers Console:** Go to the [Google Developers Console](https://console.developers.google.com/). You'll need to sign in with your Google account.
    *   **Create or Select a Project:**
        *   If you don't have a project, click on "Select a project" (or it might show an existing project name) at the top, then click "NEW PROJECT". Give it a name (e.g., "YouTube Uploader Project") and click "CREATE".
        *   If you have an existing project you want to use, select it from the list.
    *   **Enable YouTube Data API v3:**
        *   Once your project is selected, use the search bar at the top (or navigate via "APIs & Services" > "Library") to find "YouTube Data API v3".
        *   Click on it, and then click the "ENABLE" button if it's not already enabled.
    *   **Configure OAuth Consent Screen (If not already done for the project):**
        *   Before creating credentials, you might need to configure the OAuth consent screen. Go to "APIs & Services" > "OAuth consent screen".
        *   Choose "External" (unless you are a Google Workspace user and this is an internal app). Click "CREATE".
        *   Fill in the required fields:
            *   **App name:** (e.g., "My YouTube Uploader")
            *   **User support email:** Your email address.
            *   **Developer contact information:** Your email address.
        *   Click "SAVE AND CONTINUE" through the Scopes and Test users sections (you can add test users later if needed, for a desktop app it's often not strictly necessary for your own use).
        *   Go back to the "Dashboard" or "Credentials" page.
    *   **Create OAuth 2.0 Client ID:**
        *   Go to "APIs & Services" > "Credentials".
        *   Click on "+ CREATE CREDENTIALS" at the top and select "OAuth client ID".
        *   For "Application type", choose **"Desktop app"**.
        *   Give the client ID a name (e.g., "YouTube Uploader Desktop Client").
        *   Click "CREATE".
    *   **Download `client_secret.json`:**
        *   A pop-up will appear showing "OAuth client created" with your Client ID and Client secret. Click "DOWNLOAD JSON".
        *   Rename the downloaded file to `client_secret.json` (if it's not already named that) and place it in the **root directory** of this project.

4.  **Prepare Video Metadata:**
    Create a `video_metadata.csv` file in the root directory. The expected columns might be (this is an assumption, update as per your script's needs):
    `filePath,title,description,tags,category,privacyStatus`
    Example:
    ```csv
    videos/my_video_1.mp4,My First Video,This is the description for my first video,"tag1,tag2,tag3",22,private
    videos/another_video.mp4,Another Great Video,Description here,"new tag,vlog",22,public
    ```
    *(Note: Category IDs can be found in the YouTube API documentation. 22 is often "People & Blogs")*

5.  **Place Video Files:**
    Ensure the video files listed in `video_metadata.csv` are in the correct paths (e.g., in a `videos/` subdirectory).

## Usage

1.  **Run the Uploader Script:**
    *   **On macOS:**
        You might need to make the `.command` file executable first:
        ```bash
        chmod +x run_youtube_uploader.command
        ./run_youtube_uploader.command
        ```
    *   **Directly with Python:**
        ```bash
        python youtube_uploader.py
        ```

2.  **First-time Authentication:**
    The first time you run the script, it will likely open a browser window asking you to authorize the application to access your YouTube account. Follow the prompts. After successful authorization, a `token.pickle` file will be created to store your credentials for future runs.

## Files in the Repository (Expected)

*   `youtube_uploader.py`: The main Python script for handling video uploads.
*   `run_youtube_uploader.command`: A shell script to execute the uploader on macOS.
*   `video_metadata.csv` (Example or Template): A CSV file to input video details. (This file itself might be in `.gitignore` if it contains specific video data, but a template or example should be versioned).
*   `.gitignore`: Specifies intentionally untracked files that Git should ignore.
*   `README.md`: This file.

## .gitignore Details

The `.gitignore` file is configured to exclude:
*   Sensitive credential files (`client_secret.json`, `token.pickle`).
*   macOS system files (`.DS_Store`).
*   The `videos/` directory (assuming raw video files are not versioned).
*   Python cache files and virtual environment directories (`__pycache__/`, `*.pyc`, `venv/`, etc.).
*   Log files (`*.log`).

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

(Specify your license here, e.g., MIT, Apache 2.0, or leave blank if not applicable yet)
[MIT](https://choosealicense.com/licenses/mit/)
