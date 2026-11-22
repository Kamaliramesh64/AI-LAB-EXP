# Deploy to Streamlit Community Cloud (free, public link)

1. Create a free account at github.com and click New repository. Name it nids-dashboard, set it to Public, and create it.
2. On the repository page click "uploading an existing file". Open the `project` folder on your computer, select EVERYTHING inside it
   (app.py, train.py, common.py, requirements.txt, data, models, results, .streamlit, live_version ...) and drag it into the browser. Click Commit changes.
   The main file app.py must be at the top level of the repository, not inside another folder.
3. Go to share.streamlit.io and sign in with GitHub. Click Create app, choose the repository, branch main, main file path app.py.
4. Under Advanced settings choose Python 3.12 or 3.13. Click Deploy. The first start takes a few minutes.
5. Copy the link (it ends in .streamlit.app). It opens on any phone.

Notes
- requirements.txt pins exact library versions so the saved model loads. If it ever does not match, app.py retrains it automatically (about 2 minutes).
- The app sleeps after a period of no visits. Opening the link wakes it in under a minute. Open it once before your review.
- Alerts are saved in a temporary log that resets when the app restarts.
