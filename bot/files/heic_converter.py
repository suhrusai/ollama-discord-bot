from PIL import Image
import pillow_heif

# Register the HEIF opener plugin with Pillow
pillow_heif.register_heif_opener()

def convert_heic_to_jpg(heic_path, jpg_path, max_size=(1024, 1024), quality=70):
    """
    Converts a single HEIC file to JPG format, resizing and compressing
    it for LLM processing.

    Args:
        heic_path (str): Path to the input HEIC file.
        jpg_path (str): Path to save the output JPG file.
        max_size (tuple): Maximum width and height to resize the image (preserves aspect ratio).
        quality (int): JPEG quality (1-100, lower means smaller file size).
    """
    try:
        # Open the HEIC image
        image = Image.open(heic_path)

        # Resize image if larger than max_size
        image.thumbnail(max_size)

        # Save the image in JPEG format with compression
        image.save(jpg_path, "JPEG", quality=quality)
        print(f"Converted and resized: {heic_path} -> {jpg_path}")

    except Exception as e:
        print(f"Error converting {heic_path}: {e}")

# Example usage:
# convert_heic_to_jpg("example.heic", "example_small.jpg")
