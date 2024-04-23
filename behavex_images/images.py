from __future__ import absolute_import, print_function

from report.images_report import _normalize_log, add_image
from behavex_images.utils import image_hash


def attach_image_from_binary(context, image_binary):
    """
    This function attaches an image from binary data to the test execution report.

    It first checks if the binary data is not empty. If it is, it uses the magic library to determine the format of the image.
    If the format is not JPG or PNG, it raises an exception.

    If the format is JPG, it converts the image to PNG format and updates the binary data.

    If the format is PNG, it calculates the hash of the image and compares it with the hash of the previous image.
    If the hashes are different, it increments the counter of captured screens and resets the list of previous steps.

    It then updates the hash and binary data of the image in the context, and if the log stream is not closed,
    it appends the normalized log lines to the list of previous steps and truncates the log stream.

    Finally, it adds the image to the context and deletes the binary data.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    image_binary (bytes): The binary data of the image to be attached.

    Returns:
    None
    """
    if image_binary:
        mime = magic.Magic(mime=True)
        image_binary_format = mime.from_buffer(image_binary)
        if image_binary_format not in ['image/jpg', 'image/png']:
            raise Exception('The provided binary data is not a valid PNG or JPG image.')
        if image_binary_format == 'image/jpg':
            png_binary_data = BytesIO()
            image.save(image_binary, format='PNG')
            png_binary_data.seek(0)
            image_binary = png_binary_data.read()
        if image_binary_format == 'image/png':
            try:
                image_stream_hash = image_hash.dhash(Image.open(BytesIO(image_binary)))
                if (
                    not context.bhx_image_hash
                    or image_stream_hash != context.bhx_image_hash
                ):
                    context.bhx_capture_screens_number += 1
                    context.bhx_previous_steps = []
            except Exception as exception:
                image_stream_hash = None
                print(str(exception))
            context.bhx_image_hash = image_stream_hash
            context.bhx_image_stream = image_binary
            if not context.bhx_log_stream.closed:
                for log_line in context.bhx_log_stream.getvalue().splitlines(True):
                    step = _normalize_log(log_line)
                    context.bhx_previous_steps.append(step)
                context.bhx_log_stream.truncate(0)
            add_image(context)
            del image_binary
        else:
            raise Exception('The provided binary data is not a valid PNG image, or could not be converted to PNG.')


def attach_image_from_file(context, file_path):
    """
    This function attaches an image from a file to the test execution report.

    It first checks if the file exists at the given path. If it does not, it raises an exception.

    If the file exists, it checks the file extension. If the extension is not JPG or PNG, it raises an exception.

    It then opens the file in binary mode. If the file is a JPG, it converts the image to PNG format and updates the binary data. If the file is a PNG, it reads the binary data from the file.

    Finally, it calls the function 'attach_image_from_binary' with the context and the binary data as arguments.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    file_path (str): The absolute path to the image file to be attached.

    Returns:
    None
    """
    if os.path.isfile(file_path):
        file_extension = os.path.splitext(file_path)[1]
        if file_extension.lower() not in ['.jpg', '.png']:
            raise Exception('The provided file format is not supported. Only PNG and JPG files can be attached.')
        with open(file_path, 'rb') as image_file:
            if file_extension.lower() == '.jpg':
                png_binary_data = BytesIO()
                image.save(image_file, format='PNG')
                png_binary_data.seek(0)
            else:
                png_binary_data = image_file.read()
            attach_image_from_binary(context, png_binary_data)
    else:
        raise Exception('The provided file cannot be found at the specified path:  %s' % file_path)
