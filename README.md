# Digitalize It

A web app to scan an old photo album and extract the photos from it.

## Docker

To run the app using Docker Compose, run the following command:

```bash
docker compose up
```

The app will be available at `http://localhost:3000`.
(And the API will be available at `http://localhost:8000`)

## Manual Installation and Setup

### Python Backend
```bash
cd server
pip install -r requirements.txt
fastapi dev main.py
```

### Vue Frontend
```bash
cd client
npm install
npm run dev
```

## Features

- Upload images of photo album
- Automatically detect photos in the image and allow user to adjust the regions
- Extract photos from the image (crop)
- Download the extracted photos

## Credits

The helper functions for image processing are taken from Andrew Campbell's repository ["OpenCV-Document-Scanner"](https://github.com/andrewdcampbell/OpenCV-Document-Scanner).