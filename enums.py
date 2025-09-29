from enum import Enum

class CameraAngle(Enum):
    OVERHEAD = "overhead"  # Camera above CPR recipient, hands positioning
    SIDE_VIEW = "side_view"  # Camera from side, compression monitoring

class CPRMode(Enum):
    POSITIONING = "positioning"  # Hand placement guidance
    COMPRESSION = "compression"  # Compression rate/depth monitoring
