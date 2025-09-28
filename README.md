# Advanced CPR Assistant

A modular computer vision application for CPR training and guidance, supporting both overhead positioning and side-view compression monitoring.

## Project Structure

The project has been refactored into a modular architecture:

```
stayinalive/
├── main.py                 # Main entry point with mode selection
├── cpr_assistant.py        # Main CPR assistant coordinator
├── detection.py            # Pose and hand detection modules
├── analysis.py             # CPR analysis algorithms
├── visualization.py        # Drawing and overlay functions
├── ui.py                   # Kivy UI components
├── enums.py                # Enumerations for modes and angles
├── config.py               # Configuration constants
├── requirements.txt        # Python dependencies
├── twoPhaseSolution.py     # Original monolithic implementation
└── README.md              # This file
```

## Modules

### Core Components

- **`cpr_assistant.py`**: Main coordinator class that brings all components together
- **`detection.py`**: Handles pose detection, hand detection, and camera management
- **`analysis.py`**: Contains CPR analysis algorithms for positioning and compression monitoring
- **`visualization.py`**: Handles all drawing operations, overlays, and feedback display

### Configuration

- **`enums.py`**: Defines camera angles and CPR modes
- **`config.py`**: Contains all configuration constants, colors, and parameters
- **`ui.py`**: Kivy-based user interface components

## Features

### Overhead Mode (Positioning)
- Hand placement guidance
- Chest center detection
- Positioning accuracy feedback
- Real-time visual overlays

### Side View Mode (Compression)
- Compression rate monitoring
- Depth analysis
- Real-time feedback
- Baseline calibration

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

## Usage

The application offers two modes:

1. **CPR Assistant (Computer Vision)**: Full computer vision-based CPR training
2. **Kivy UI Application**: User interface for system control

### Controls (Computer Vision Mode)

- `1`: Switch to overhead mode
- `2`: Switch to side view mode
- `s`: Start/stop guidance
- `c`: Calibrate current mode
- `r`: Reset all counters
- `e`: Emergency call simulation
- `q`: Quit

## Architecture Benefits

### Modularity
- Each component has a single responsibility
- Easy to test individual modules
- Simplified maintenance and updates

### Extensibility
- Easy to add new detection algorithms
- Simple to extend visualization features
- Straightforward to add new analysis methods

### Maintainability
- Clear separation of concerns
- Reduced code duplication
- Improved readability

## Development

### Adding New Features

1. **New Detection Methods**: Add to `detection.py`
2. **Analysis Algorithms**: Extend `analysis.py`
3. **Visualization**: Add to `visualization.py`
4. **UI Components**: Extend `ui.py`

### Configuration

Modify `config.py` to adjust:
- Camera settings
- Detection parameters
- Color schemes
- CPR targets

## Dependencies

- **OpenCV**: Computer vision processing
- **MediaPipe**: Pose and hand detection
- **Kivy**: User interface framework
- **NumPy**: Numerical computations

## License

This project is for educational and training purposes.
