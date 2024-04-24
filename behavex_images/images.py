import selenium

from behavex_images.report.images_report import normalize_log, add_image_to_report_story
from behavex_images.utils import image_hash, image_format


def attach_image_binary_to_report(context, image_binary):
    """
    This function attaches an image from binary data to the test execution report.

    It first checks if the binary data is not None. If it is None, it does nothing.

    If the binary data is not None, it checks the format of the image. If the format is not PNG or JPEG, it raises an exception.

    If the image is in JPEG format, it converts the image to PNG format and updates the binary data.

    If the image is in PNG format, it calculates the hash of the image and updates the context with the hash and the binary data. It also updates the context with the log stream and the previous steps.

    If the image is not in PNG format and could not be converted to PNG, it raises an exception.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    image_binary (bytes): The binary data of the image to be attached.

    Returns:
    None
    """
    if image_binary:
        image_binary_format = image_format.get_image_format(image_binary)
        if image_binary_format not in ['PNG', 'JPEG']:
            raise Exception('The provided binary data is not a valid PNG or JPG image.')
        if image_binary_format == 'JPEG':
            png_binary_data = BytesIO()
            image.save(image_binary, format='PNG')
            png_binary_data.seek(0)
            image_binary = png_binary_data.read()
        if image_binary_format == 'PNG':
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
            add_image_to_report_story(context)
            del image_binary
        else:
            raise Exception('The provided binary data is not a valid PNG image, or could not be converted to PNG.')


def attach_image_file_to_report(context, file_path):
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
            attach_image_binary_to_report(context, png_binary_data)
    else:
        raise Exception('The provided file cannot be found at the specified path:  %s' % file_path)


def get_browser_image(context):
    """
    This function retrieves an image from the browser.

    Parameters:
    context (object): The context object which contains the browser from which the image will be retrieved.

    Returns:
    bytes: The image retrieved from the browser in the form of a byte stream. If the image cannot be retrieved, None is returned.
    """
    image_stream = None
    for browser in context.browsers.values():
        try:
            image_stream = browser.driver.get_screenshot_as_png()
            attach_image_from_binary(context, image_stream)
        except selenium.common.exceptions.WebDriverException as exception:
            print(exception)
            logging.error('could not save_screenshot')
            # pickle.dump(
            # browser.driver.page_source.encode(encoding='UTF-8'), log)
    return image_stream
