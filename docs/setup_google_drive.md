# Google Drive Integration Setup

To enable the Google Drive integration in Bark, you need to create a Google Cloud Project, enable the Drive API, and obtain credentials.

## Step 1: Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown at the top of the page.
3. Click **New Project**.
4. Enter a name (e.g., "Bark Chatbot") and click **Create**.

## Step 2: Enable the Google Drive API
1. Select your new project.
2. Go to **APIs & Services** > **Library**.
3. Search for "Google Drive API".
4. Click **Google Drive API** and then click **Enable**.

## Step 3: Configure OAuth Consent Screen
1. Go to **APIs & Services** > **OAuth consent screen**.
2. Select **External** (unless you are in a Google Workspace organization and want to restrict it internally) and click **Create**.
3. Fill in the required fields:
    - **App Information**: App name (e.g., "Bark"), User support email.
    - **Developer Contact Information**: Your email.
4. Click **Save and Continue** essentially 3 times (you don't need to add scopes or test users for this initial setup if you login as the owner, but adding yourself as a Test User is recommended if you keep it in "Testing" mode).
5. **Important**: Under **Test users**, click **Add Users** and add your own Google email address.

## Step 4: Create Credentials
1. Go to **APIs & Services** > **Credentials**.
2. Click **Create Credentials** > **OAuth client ID**.
3. Select **Desktop app** as the Application type.
4. Name it "Bark Desktop Client".
5. Click **Create**.
6. A popup will appear. Click **Download JSON** (or close and click the download icon next to the client ID in the list).
7. Rename the downloaded file to `credentials.json`.

## Step 5: Install Credentials (Local Dev)
1. Move the `credentials.json` file to the root of the Bark repository:
   ```bash
   mv ~/Downloads/credentials.json /path/to/ScottyLabs/bark/credentials.json
   ```
2. Ensure you are in the `bark` directory.
3. Run the bot or test script. It will open a browser to log in.
4. A `token.json` file will be created.

## Step 6: Deployment (Railway / Cloud)
Since you cannot open a browser on a cloud server, you must provide your local credentials.

### Method A: Use `token.json`
1. Run the bot locally to generate `token.json` (see Step 5).
2. Open `token.json` and copy its entire content.
3. IN Railway, add a new Environment Variable:
   - Key: `GOOGLE_DRIVE_TOKEN_JSON`
   - Value: (Paste the content of `token.json`)

### Method B: Service Account (Recommended for Organizations)
1. In Google Cloud Console, go to **IAM & Admin** > **Service Accounts**.
2. Create a Service Account.
3. Go to **Keys** > **Add Key** > **Create new key** > **JSON**.
4. Download the file.
5. In Railway, add a new Environment Variable:
   - Key: `GOOGLE_DRIVE_CREDENTIALS_JSON`
   - Value: (Paste the content of the JSON file)
6. **Important**: You must **Share** the Google Drive folders you want to index with the Service Account's email address (e.g., `bark-bot@project-id.iam.gserviceaccount.com`).

## Optional: Restrict to a Specific Folder
If you only want Bark to index a specific folder:
1. Open Google Drive and navigate to the folder.
2. Copy the folder ID from the URL (the string after `folders/`).
3. Update `src/bark/core/config.py` or set the env var `GOOGLE_DRIVE_FOLDER_ID`.
