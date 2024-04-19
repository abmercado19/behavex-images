from __future__ import absolute_import, print_function

from report.behavex_images.images_report import _normalize_log, add_image
from behavex_images.utils import image_hash


def attach_image_from_binary(context, image_binary):
    """Attach image from binary data to test execution report
    image_binary: binary data of the image to be attached
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
    """Attach image from a file to test execution report
    file_path: absolute path to the image file to be attached
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
