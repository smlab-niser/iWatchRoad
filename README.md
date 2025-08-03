# RoadWatch
[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org)
![RoadWatch Main Interface](images/Main.png)

## Overview

RoadWatch is an intelligent road infrastructure monitoring system that combines computer vision with web based mapping technology. The system automatically detects and tracks potholes using dashcam footage and provides a comprehensive web interface for monitoring and managing road conditions.

> [!important]
> Please go here for the Tirtha site: https://smlab.niser.ac.in/project/tirtha/.
> New features will be added to the dev site first: https://smlab.niser.ac.in/project/tirtha/dev/.

### Key Features

**🎥 Dashcam Processing System:**
- **YOLO-based Detection**: Real-time pothole detection using YOLOv8 object detection models
- **GPS Integration**: Precise location mapping using GPS data from dashcam footage
- **Computer Vision Pipeline**: Powered by OpenCV, CVZone, and Ultralytics for robust image processing
- **OCR Processing**: Automatic text extraction using EasyOCR for additional context
- **Machine Learning**: Advanced filtering and classification using scikit-learn and scipy

**🌐 Web Application:**
- **Interactive Mapping**: Built with React, TypeScript, and Leaflet for dynamic map visualization
- **Real-time Data**: Django REST Framework backend for seamless data management
- **Responsive Design**: Modern React based frontend with clustering and filtering capabilities
- **Data Analytics**: Comprehensive reporting and statistics for road authorities

## Technology Stack

### Backend (Django)
- **Framework**: Django 5.2+ with Django REST Framework
- **Database**: SQLite (configurable to PostgreSQL/MySQL)
- **Image Processing**: Pillow, OpenCV
- **API**: RESTful API with CORS support

### Frontend (React + TypeScript)
- **Framework**: React 19+ with TypeScript
- **Mapping**: Leaflet with React-Leaflet integration
- **Build Tool**: Vite for fast development and building
- **Clustering**: React-Leaflet-Cluster for marker management

### AI/ML Processing
- **Object Detection**: Ultralytics YOLOv8
- **Computer Vision**: OpenCV, CVZone
- **OCR**: EasyOCR for text recognition
- **Data Processing**: Pandas, NumPy for data manipulation
- **Machine Learning**: scikit-learn, scipy for advanced analytics

## Environment Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/smlab-niser/roadwatch.git
cd roadwatch
```

### 2. Backend Setup (Django)

#### Create Python Environment
```bash
# Using conda (recommended)
conda create -n roadwatch python=3.11 -y
conda activate roadwatch

# Or using venv
python -m venv roadwatch-env
# Windows
roadwatch-env\Scripts\activate
# Linux/Mac
source roadwatch-env/bin/activate
```

#### Install Backend Dependencies
```bash
cd code/backend
pip install -e .
```

#### Install Dashcam Processing Dependencies
```bash
cd dashcam_processor
pip install -r requirements.txt

# Install PyTorch with CUDA support (if you have a compatible GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. Frontend Setup (React)
```bash
cd code
npm install
```

## Configuration

### Database Configuration
**Important**: Before running the application, you must configure the secret key:

1. Navigate to `code/backend/pothole_tracker/settings.py`
2. Replace the `SECRET_KEY` value:
```python
# Change this line:
SECRET_KEY = '#######'

# To a secure secret key (generate one at https://djecrety.ir/):
SECRET_KEY = 'your-secure-secret-key-here'
```

### Database Setup
```bash
cd code/backend
python manage.py migrate
python manage.py createsuperuser  # Optional: create admin user
```

## Running the Application

### Development Mode

#### Start the Backend Server
```bash
cd code/backend
python manage.py runserver
```
The Django backend will be available at `http://localhost:8000`

#### Start the Frontend Development Server
```bash
cd code
npm run dev
```
The React frontend will be available at `http://localhost:5173`

### Production Deployment

#### Build Frontend for Production
```bash
cd code
npm run build
```

#### Collect Static Files (Django)
```bash
cd code/backend
python manage.py collectstatic
```

#### Start Production Server
```bash
cd code/backend
python start_production.py
```

## Usage

### Processing Dashcam Footage
1. Navigate to the upload section of the web interface
2. Upload your dashcam video files with GPS data
3. The system will automatically:
   - Process the video frame by frame
   - Detect potholes using YOLO models
   - Extract GPS coordinates
   - Store results in the database

### Viewing Results
1. Access the interactive map interface
2. Use filters to view specific time ranges or severity levels
3. Click on markers to view detailed information about detected potholes


### API Access
The system provides RESTful APIs for integration with other systems:
- `GET /api/potholes/` - List all detected potholes
- `POST /api/upload/` - Upload new dashcam footage
- `GET /api/statistics/` - Get summary statistics

## Project Structure
```
roadwatch/
├── images/                     # Documentation images
├── code/
│   ├── backend/               # Django backend
│   │   ├── pothole_tracker/   # Main Django project
│   │   ├── potholes/          # Potholes app
│   │   ├── accounts/          # User management
│   │   └── dashcam_processor/ # AI processing module
│   ├── src/                   # React frontend source
│   ├── public/                # Static assets
│   └── package.json           # Node.js dependencies
└── README.md
```

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License
This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg

See the [LICENSE](LICENSE) file for details.

## 👥 Development Team 

- **[Subhankar Mishra's Lab](https://www.niser.ac.in/~smishra/)** - NISER ([GitHub](https://github.com/smlab-niser))
- **Lab Project Website**: [NISER SMLab](https://smlab.niser.ac.in)

## Support
For questions and support, please open an issue on GitHub or contact the development team.
