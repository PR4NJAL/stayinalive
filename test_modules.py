#!/usr/bin/env python3
"""
Simple test script to verify all modules can be imported correctly.
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports() -> bool:
    """Test that all modules can be imported"""
    try:
        print("Testing module imports...")
        
        # Test enums
        from enums import CameraAngle, CPRMode
        print("✓ enums.py imported successfully")
        
        # Test config
        from config import COLORS, TARGET_COMPRESSION_RATE
        print("✓ config.py imported successfully")
        
        # Test detection (may fail if OpenCV/MediaPipe not installed)
        try:
            from detection import PoseDetector, HandDetector, CameraManager
            print("✓ detection.py imported successfully")
        except ImportError as e:
            print(f"⚠ detection.py import failed (expected if dependencies missing): {e}")
        
        # Test analysis
        from analysis import CPRAnalyzer
        print("✓ analysis.py imported successfully")
        
        # Test visualization (may fail if OpenCV not installed)
        try:
            from visualization import CPRVisualizer
            print("✓ visualization.py imported successfully")
        except ImportError as e:
            print(f"⚠ visualization.py import failed (expected if dependencies missing): {e}")
        
        # Test main CPR assistant (may fail if dependencies missing)
        try:
            from cpr_assistant import AdvancedCPRAssistant
            print("✓ cpr_assistant.py imported successfully")
        except ImportError as e:
            print(f"⚠ cpr_assistant.py import failed (expected if dependencies missing): {e}")
        
        print("\n✅ All core modules imported successfully!")
        print("Note: Some modules may show warnings if optional dependencies are missing.")
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False
    
    return True

def test_basic_functionality() -> bool:
    """Test basic functionality of imported modules"""
    try:
        print("\nTesting basic functionality...")
        
        # Test enums
        from enums import CameraAngle, CPRMode
        overhead = CameraAngle.OVERHEAD
        positioning = CPRMode.POSITIONING
        print(f"✓ Enum values work: {overhead.value}, {positioning.value}")
        
        # Test config
        from config import COLORS, TARGET_COMPRESSION_RATE
        print(f"✓ Config values work: {TARGET_COMPRESSION_RATE}, colors: {len(COLORS)}")
        
        # Test analysis
        from analysis import CPRAnalyzer
        analyzer = CPRAnalyzer()
        analyzer.reset_counters()
        print("✓ CPRAnalyzer can be instantiated and reset")
        
        print("✅ Basic functionality tests passed!")
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False
    
    return True

def main() -> None:
    """Run all tests"""
    print("🧪 CPR Assistant - Module Tests")
    print("=" * 40)
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test basic functionality
    if not test_basic_functionality():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed! The modular structure is working correctly.")
    else:
        print("❌ Some tests failed. Check the error messages above.")
    
    print("\nTo install missing dependencies, run:")
    print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()
