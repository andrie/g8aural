# G8aural: ABRSM Aural Training App

G8aural is an interactive web application that helps students prepare for ABRSM (Associated Board of the Royal Schools of Music) aural tests. It features two main training modules:

1. **Cadence Identification** - Practice identifying cadence types by ear
2. **Voice Singing** - Practice singing melodies with real-time pitch feedback

## Features

- **Grade-specific exercises** for ABRSM Grades 5-8
- **Interactive audio playback** with high-quality piano sounds
- **Real-time pitch detection** for voice singing practice
- **Visual notation display** to reinforce learning
- **Immediate feedback** on your performance
- **Responsive design** that works on desktop and mobile devices

## What are ABRSM Aural Tests?

ABRSM aural tests are a component of music examinations that assess a student's listening skills and musical understanding. These tests include:

- Identifying cadence types (how musical phrases end)
- Singing back melodies played by the examiner
- Identifying musical features and characteristics
- Sight-singing and rhythm exercises

G8aural helps you practice the cadence identification and melody singing components of these tests.

## Installation

### Prerequisites

- Python 3.9+ installed on your system
- A modern web browser (Chrome, Firefox, Safari, or Edge)
- Microphone access (for voice singing feature)

### Setup Instructions

1. Clone or download this repository
2. Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

Start the application with:

```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
shiny run app.py --reload
```

Then open your browser to: **http://localhost:8000**

## User Guide

### Getting Started

1. When you first open the application, you'll see two tabs:
   - **Cadence Identification**
   - **Voice Singing**

2. Use the grade selector at the top to choose which ABRSM grade you want to practice (5-8)

### Cadence Identification Practice

1. **Select a grade** (6-8) using the slider
2. Click the **Play Cadence** button to hear a chord progression
3. Identify which cadence type you heard:
   - **Perfect** (V-I, strong resolution)
   - **Plagal** (IV-I, "Amen" cadence)
   - **Imperfect** (ends on V, feels unresolved)
   - **Interrupted** (V-vi, unexpected resolution)
4. Click the corresponding button with your answer
5. Receive immediate feedback and view notation after correct answers
6. Click **Next** to try another progression

#### Tips for Cadence Identification
- Perfect cadences sound complete and final
- Plagal cadences sound gentle and settled
- Imperfect cadences sound unfinished, waiting for resolution
- Interrupted cadences sound surprising or unexpected

### Voice Singing Practice

1. **Select a grade** (5-8) using the slider
2. Click **Start Task** to begin
3. Listen to the melody played twice
4. When recording begins (indicated on screen), sing back the melody
5. Your pitch will be analyzed and you'll receive feedback on accuracy
6. View your pitch contour compared to the target melody
7. Use **Try Again** to practice the same melody

#### What You'll Sing by Grade
- **Grade 5**: A single melody line
- **Grade 6**: The upper part of a two-part phrase
- **Grade 7**: The lower part of a two-part phrase
- **Grade 8**: The lowest part of a three-part phrase

## Troubleshooting

### Common Issues

#### Audio Doesn't Play
- Make sure your device volume is turned up
- Try refreshing the page
- Some browsers require a user interaction before audio can play

#### Microphone Access Denied
- Check that you've granted microphone permission in your browser
- If you denied permission, you may need to reset it in your browser settings

#### Voice Singing Features Not Working
- Make sure your microphone is working properly
- Check that you've allowed microphone access in your browser
- Try using Chrome, which has better Web Audio API support

#### Application Doesn't Start
- Make sure you've activated the virtual environment
- Check that all dependencies are installed correctly
- Verify Python version is 3.9 or higher

## Technology

G8aural is built with:
- **Shiny for Python**: Interactive web framework
- **music21**: Python toolkit for computer-aided musicology
- **Tone.js**: JavaScript framework for interactive audio
- **VexFlow**: JavaScript library for music notation rendering

## Resources for ABRSM Preparation

- [ABRSM Syllabus Information](https://www.abrsm.org/en/our-exams/aural-tests/)
- [ABRSM Specimen Aural Tests](https://www.abrsm.org/en/our-exams/supporting-your-learning/)
- [Music Theory Resources](https://www.musictheory.net/)

## License

[License information to be added]