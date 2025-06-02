import os
import csv
import random
import datetime
import time
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from google.auth.transport.requests import Request

# --- YouTube API Configuration ---
CLIENT_SECRETS_FILE = "client_secret.json"
API_SERVICE_NAME = "youtube"
API_VERSION = "v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_PICKLE_FILE = "token.pickle"

# --- Script Configuration ---
VIDEO_FOLDER = "videos"
METADATA_CSV = "video_metadata.csv"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M"

def get_video_files(folder):
    """Gets a list of video files from the specified folder."""
    allowed_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.flv']
    return [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)) and os.path.splitext(f)[1].lower() in allowed_extensions]

def generate_random_time():
    """Generates a random time between 4:30 PM and 6:30 PM."""
    start_minutes = 16 * 60 + 30
    end_minutes = 18 * 60 + 30
    random_total_minutes = random.randint(start_minutes, end_minutes)
    hours = random_total_minutes // 60
    minutes = random_total_minutes % 60
    return datetime.time(hours, minutes).strftime(TIME_FORMAT)

def read_or_create_metadata_csv(video_files_in_folder):
    """
    Reads or creates the metadata CSV. User is expected to name files as their intended titles.
    The script pre-fills the 'Title' column from the filename.
    """
    fieldnames = ['FileName', 'UploadDate', 'UploadTime', 'Title', 'Description', 'Tags', 'Uploaded']
    rows = []
    file_exists = os.path.isfile(METADATA_CSV)
    
    existing_filenames_in_csv = set()

    if file_exists:
        with open(METADATA_CSV, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row_from_csv in reader:
                # Ensure all fields are present, defaulting to empty string
                processed_row = {field: row_from_csv.get(field, '') for field in fieldnames}
                
                # Normalize UploadDate
                original_csv_date = processed_row['UploadDate']
                try:
                    dt_obj = datetime.datetime.strptime(original_csv_date, DATE_FORMAT)
                    processed_row['UploadDate'] = dt_obj.strftime(DATE_FORMAT)
                except ValueError:
                    possible_formats = ["%m/%d/%y", "%m/%d/%Y", "%d/%m/%y", "%d/%m/%Y", "%Y/%m/%d", "%y/%m/%d"]
                    parsed = False
                    for fmt in possible_formats:
                        try:
                            dt_obj = datetime.datetime.strptime(original_csv_date, fmt)
                            processed_row['UploadDate'] = dt_obj.strftime(DATE_FORMAT)
                            parsed = True; print(f"Notice: Converted date '{original_csv_date}' to '{processed_row['UploadDate']}' for '{processed_row['FileName']}'.")
                            break
                        except ValueError: continue
                    if not parsed: print(f"Warning: Could not parse date '{original_csv_date}' for '{processed_row['FileName']}'.")

                if not processed_row['Uploaded']: processed_row['Uploaded'] = 'No'
                
                rows.append(processed_row)
                existing_filenames_in_csv.add(processed_row['FileName'])
    
    # Determine the next date for new videos
    latest_date_in_csv = datetime.date.min
    if rows:
        valid_dates = [datetime.datetime.strptime(r['UploadDate'], DATE_FORMAT).date() for r in rows if r['UploadDate']]
        if valid_dates: latest_date_in_csv = max(valid_dates)
    
    next_upload_date_counter = 0
    for disk_file in video_files_in_folder:
        if disk_file not in existing_filenames_in_csv:
            # Assign date for new file
            current_processing_date = max(datetime.date.today(), latest_date_in_csv)
            if latest_date_in_csv != datetime.date.min and current_processing_date <= latest_date_in_csv : # Ensure new dates are after existing ones
                 current_processing_date = latest_date_in_csv

            upload_date_obj = current_processing_date + datetime.timedelta(days=next_upload_date_counter + (1 if latest_date_in_csv >= datetime.date.today() or latest_date_in_csv != datetime.date.min else 0) )
            
            # If the very first date to be assigned is today, and latest_date_in_csv was min (empty/old CSV)
            # ensure we don't add timedelta(1) unnecessarily for the first new item.
            if latest_date_in_csv == datetime.date.min and next_upload_date_counter == 0 and upload_date_obj > datetime.date.today():
                 upload_date_obj = datetime.date.today()


            upload_date_str = upload_date_obj.strftime(DATE_FORMAT)
            
            file_title_part = os.path.splitext(disk_file)[0]
            rows.append({
                'FileName': disk_file,
                'UploadDate': upload_date_str,
                'UploadTime': generate_random_time(),
                'Title': file_title_part, # Pre-fill Title from filename
                'Description': '',
                'Tags': '',
                'Uploaded': 'No'
            })
            existing_filenames_in_csv.add(disk_file) # Add to set to handle next_upload_date_counter correctly if CSV was empty
            if latest_date_in_csv == datetime.date.min or upload_date_obj > latest_date_in_csv: # Update latest date for sequential assignment
                latest_date_in_csv = upload_date_obj 
            next_upload_date_counter +=1


    rows.sort(key=lambda x: (datetime.datetime.strptime(x['UploadDate'], DATE_FORMAT), x['FileName']))

    with open(METADATA_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Metadata CSV '{METADATA_CSV}' {'updated' if file_exists else 'created'}.")
    return rows, fieldnames # Return fieldnames as well

def check_metadata_completeness(metadata_rows):
    """Checks if Title, Description, and Tags are filled."""
    for i, row in enumerate(metadata_rows):
        # Title is now pre-filled from filename, but user might clear it.
        # User still needs to confirm/edit title and fill description/tags.
        if not row['Title'] or not row['Description'] or not row['Tags']:
            print(f"\nERROR: Metadata for video '{row['FileName']}' (scheduled for {row['UploadDate']}) is incomplete.")
            print(f"Please ensure Title (matches filename), Description, and Tags are filled in '{METADATA_CSV}'.")
            print(f"Row {i+2}: Title='{row['Title']}', Description='{row['Description']}', Tags='{row['Tags']}'")
            return False
    return True

def upload_to_youtube(video_path, title, description, tags, publish_at_iso, upload_date_for_recording):
    """Handles the YouTube API upload logic."""
    print(f"\n--- Attempting to schedule upload for: {os.path.basename(video_path)} ---")
    print(f"  Title: {title}")
    print(f"  Description: {description}")
    processed_tags = [tag.strip() for tag in tags.split(',') if tag.strip()] if isinstance(tags, str) else [str(tag).strip() for tag in tags if str(tag).strip()]
    print(f"  Tags: {processed_tags}")
    print(f"  Scheduled Upload Time (ISO 8601 UTC): {publish_at_iso}")
    print(f"  Video Language: en-US (fixed)")
    print(f"  Recording Date: {upload_date_for_recording}T00:00:00Z (derived from upload date)")

    creds = None
    if os.path.exists(TOKEN_PICKLE_FILE):
        with open(TOKEN_PICKLE_FILE, 'rb') as token: creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try: creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}. Please delete '{TOKEN_PICKLE_FILE}' and re-authorize.")
                return False
        else:
            if not os.path.exists(CLIENT_SECRETS_FILE):
                print(f"ERROR: '{CLIENT_SECRETS_FILE}' not found."); return False
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            try: creds = flow.run_local_server(port=0)
            except Exception as e: print(f"Error during OAuth flow: {e}"); return False
        with open(TOKEN_PICKLE_FILE, 'wb') as token: pickle.dump(creds, token)

    try:
        youtube = googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=creds)
        snippet = {"title": title, "description": description, "tags": processed_tags, "categoryId": "22", "defaultLanguage": "en-US"}
        status = {"privacyStatus": "private", "publishAt": publish_at_iso, "selfDeclaredMadeForKids": False}
        body = {"snippet": snippet, "status": status}
        request_parts = ["snippet", "status"]

        if upload_date_for_recording:
            try:
                datetime.datetime.strptime(upload_date_for_recording, DATE_FORMAT) # Validate
                body["recordingDetails"] = {"recordingDate": f"{upload_date_for_recording}T00:00:00Z"}
                request_parts.append("recordingDetails")
            except ValueError: print(f"Warning: Invalid recording date format '{upload_date_for_recording}'. Not set.")

        insert_request = youtube.videos().insert(
            part=",".join(request_parts), body=body,
            media_body=googleapiclient.http.MediaFileUpload(video_path, chunksize=-1, resumable=True)
        )
        
        response = None; retry_count = 0
        while response is None:
            try:
                print(f"Uploading chunk... (Attempt {retry_count + 1})"); status_resp, response = insert_request.next_chunk()
                if response and 'id' in response: print(f"Video id '{response['id']}' uploaded."); return True
                elif response: print(f"Upload failed: {response}"); return False
            except googleapiclient.errors.HttpError as e:
                if e.resp.status in [500, 502, 503, 504] and retry_count < 5:
                    retry_count += 1; delay = (2**retry_count) + random.random()
                    print(f"Retriable HTTP error {e.resp.status}: {e.content.decode()}. Retrying in {delay:.2f}s..."); time.sleep(delay)
                else: print(f"HTTP error {e.resp.status}: {e.content.decode()}"); return False
            except Exception as e: print(f"Upload error: {e}"); return False
        return False # Should not be reached
            
    except Exception as e:
        print(f"API interaction error: {e}"); import traceback; traceback.print_exc(); return False

def main():
    print("Starting YouTube Video Scheduler and Uploader...")
    video_files = get_video_files(VIDEO_FOLDER)
    if not video_files: print(f"No videos in '{VIDEO_FOLDER}'. Add videos and retry."); return
    print(f"Found videos in folder: {video_files}")

    metadata_rows, csv_fieldnames = read_or_create_metadata_csv(video_files) # Unpack fieldnames
    if not check_metadata_completeness(metadata_rows): return
    print("\nMetadata check passed.")

    print("\nStarting YouTube upload process...")
    successful_uploads, failed_uploads, needs_csv_update = 0, 0, False
    today = datetime.date.today()

    for i, row in enumerate(metadata_rows):
        try: upload_date = datetime.datetime.strptime(row['UploadDate'], DATE_FORMAT).date()
        except ValueError: print(f"Invalid date for '{row['FileName']}'. Skipping."); failed_uploads+=1; continue

        if row.get('Uploaded', 'No').lower() == 'yes' or upload_date > today: continue
        
        print(f"\nProcessing '{row['Title']}' (File: {row['FileName']}) for {row['UploadDate']}")
        video_path = os.path.join(VIDEO_FOLDER, row['FileName'])
        if not os.path.exists(video_path):
            print(f"ERROR: File '{row['FileName']}' not found. Skipping."); failed_uploads+=1; continue

        try:
            naive_dt = datetime.datetime.strptime(f"{row['UploadDate']} {row['UploadTime']}", f"{DATE_FORMAT} {TIME_FORMAT}")
            local_tz = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
            publish_at_iso = naive_dt.replace(tzinfo=local_tz).astimezone(datetime.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
        except ValueError: print(f"Invalid date/time for '{row['FileName']}'. Skipping."); failed_uploads+=1; continue

        if upload_to_youtube(video_path, row['Title'], row['Description'], row['Tags'], publish_at_iso, row['UploadDate']):
            metadata_rows[i]['Uploaded'] = 'Yes'
            successful_uploads += 1; needs_csv_update = True
            print(f"Successfully processed '{row['FileName']}'. Marked 'Uploaded=Yes'.")
        else:
            failed_uploads += 1; print(f"Failed to upload '{row['FileName']}'.")
            
    if needs_csv_update:
        with open(METADATA_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames) # Use the returned fieldnames
            writer.writeheader(); writer.writerows(metadata_rows)
        print(f"\n'{METADATA_CSV}' updated.")

    print(f"\n--- Summary ---\nSuccess: {successful_uploads}, Fail/Skip: {failed_uploads}")

if __name__ == "__main__":
    if not os.path.exists(VIDEO_FOLDER): os.makedirs(VIDEO_FOLDER); print(f"Created '{VIDEO_FOLDER}'.")
    main()
