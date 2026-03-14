import rasterio

def get_bound(file_path):
    with rasterio.open(file_path) as src:
        bounds = src.bounds
    return bounds