def is_png(data):
    # PNG file signature
    return data[:8] == b'\x89PNG\r\n\x1a\n'


def is_jpeg(data):
    # JPEG file signature
    return data[:2] == b'\xFF\xD8' and data[2:4] == b'\xFF\xE0'


def is_gif(data):
    # GIF file signature
    return data[:6] in (b'GIF87a', b'GIF89a')


def get_image_format(data):
    if is_png(data):
        return 'PNG'
    elif is_jpeg(data):
        return 'JPEG'
    elif is_gif(data):
        return 'GIF'
    else:
        return 'Unknown'