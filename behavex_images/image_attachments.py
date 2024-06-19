import os
import logging
from PIL import Image
from io import BytesIO
from behavex_images.utils.report_utils import normalize_log, add_image_to_report_story, AttachmentsCondition
from behavex_images.utils import image_hash, image_format


def attach_image_binary(context, image_binary, header_text=None):
    """
    This function is used to attach an image binary to the execution report.

    Parameters:
    context (dict): A dictionary that holds the context of the current test execution.
    image_binary (bytes): The binary data of the image to be attached to the report.
    header_text (str, optional): The header text associated to the image. Defaults to None.

    Returns:
    None

    Raises:
    Exception: If the provided binary data is not a valid PNG or JPG image.
    Exception: If it was not possible to add the image to the report.
    """
    if "bhximgs_attachments_condition" not in context:
        context.bhximgs_attachments_condition = AttachmentsCondition.ALWAYS
    try:
        image_binary_format = image_format.get_image_format(image_binary)
        if image_binary_format not in ['PNG', 'JPEG']:
            raise Exception('The provided binary data is not a valid PNG or JPG image.')
        if image_binary_format == 'JPEG':
            with BytesIO(image_binary) as f:
                img = Image.open(f)
                png_binary_data = BytesIO()
                img.save(png_binary_data, format='PNG')
                png_binary_data.seek(0)
                image_binary = png_binary_data.read()
        image_stream_hash = image_hash.dhash(Image.open(BytesIO(image_binary)))
    except Exception as exception:
        logging.error('The provided binary is not a valid image, or could not be converted to PNG: %s' % str(exception))
    try:
        if not context.bhximgs_image_hash or image_stream_hash != context.bhximgs_image_hash:
            context.bhximgs_attached_images_idx += 1
            context.bhximgs_previous_steps = []
        context.bhximgs_image_hash = image_stream_hash
        context.bhximgs_image_stream = image_binary

        if not context.bhximgs_log_stream.closed:
            if header_text:
                context.bhximgs_previous_steps.append(normalize_log(header_text, line_breaks=2))
            for log_line in context.bhximgs_log_stream.getvalue().splitlines(True):
                step = normalize_log(log_line)
                context.bhximgs_previous_steps.append(step)
            context.bhximgs_log_stream.truncate(0)
        add_image_to_report_story(context)
    except Exception as exception:
        logging.error('It was not possible to add the image to the report: %s' % str(exception))


def attach_image_file(context, file_path, header_text=None):
    """
    This function is used to attach an image file to the execution report.

    Parameters:
    context (dict): A dictionary that holds the context of the current test execution.
    file_path (str): The path to the image file to be added to the report.
    header_text (str, optional): The header text associated to the image. Defaults to None.

    Returns:
    None

    Raises:
    Exception: If the provided file format is not supported. Only PNG and JPG files can be attached.
    Exception: If the provided file cannot be found at the specified path.
    """
    if os.path.isfile(file_path):
        file_extension = os.path.splitext(file_path)[1]
        if file_extension.lower() not in ['.jpg', '.png']:
            raise Exception('The provided file format is not supported. Only PNG and JPG files can be attached.')
        with open(file_path, 'rb') as image_file:
            binary_data = image_file.read()
            attach_image_binary(context, binary_data, header_text)
    else:
        logging.error('The provided file cannot be found at the specified path:  %s' % file_path)


def clean_all_attached_images(context):
    """
    This function is used to clean all the images associated to the test scenario being executed.

    Parameters:
    context (dict): A dictionary that holds the context of the current test execution.

    Returns:
    None
    """
    context.bhximgs_attached_images = {}
    context.bhximgs_attached_images_idx = 0
    context.bhximgs_previous_steps = []
    context.bhximgs_log_stream.truncate(0)


def set_attachments_condition(context, attachments_condition: AttachmentsCondition):
    """
    This function is used to set the condition for attaching the captured images to the execution report.

    Parameters:
    context (dict): A dictionary that holds the context of the current test execution
    condition (AttachmentsCondition): The condition under which the images should be attached to the report (AttachmentsCondition.ALWAYS, AttachmentsCondition.ON_FAILURE, AttachmentsCondition.NEVER).

    Returns:
    None
    """
    context.bhximgs_attachments_condition = attachments_condition
