from dataclasses import dataclass

@dataclass
class Coordinates:
    x: float
    y: float
    z: float # Airsim coordinates
    
    lon: float
    lat: float # Geographic coordinates
    
@dataclass
class GeoCoordinate:
    lon: float
    lat: float