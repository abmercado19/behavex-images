# -*- coding: utf-8 -*-
"""
BehaveX - BDD testing library based on Behave
"""
# pylint: disable=W0403, W0102

# __future__ has been added in order to maintain compatibility
from __future__ import absolute_import, print_function

import os
import re
from enum import Enum
import xml.etree.ElementTree as ET


def create_gallery(folder, title='BehaveX', captions={}):
    """
    This function creates an HTML gallery of images from a specified folder.

    Parameters:
    folder (str): The path to the folder containing the images.
    title (str, optional): The title of the gallery. Defaults to 'BehaveX'.
    captions (dict, optional): A dictionary where the keys are the image filenames (without extension) and the values are the captions for the images. Defaults to an empty dictionary.

    Returns:
    None
    """
    root = ET.Element('html', {'class': 'gallery-html'})
    head = ET.SubElement(root, 'head')
    script = ET.SubElement(
        head, 'script', {'type': 'text/javascript', 'charset': 'utf-8'}
    )
    script.text = ' '
    script = ET.SubElement(
        head,
        'script',
        {
            'src': '../image_attachments_utils/jquery-1.11.0.' 'min.js',
            'type': 'text/javascript',
        },
    )
    script.text = ' '
    script = ET.SubElement(
        head,
        'script',
        {'src': '../image_attachments_utils/lightbox.js', 'type': 'text/javascript'},
    )
    script.text = ' '
    ET.SubElement(
        head, 'link', {'rel': 'stylesheet', 'href': '../image_attachments_utils/lightbox.css'}
    )
    ET.SubElement(
        head, 'link', {'href': '../../bootstrap/css/bootstrap.min.css', 'rel': 'stylesheet'}
    )
    # Add custom CSS for lightbox
    ET.SubElement(
        head, 'link', {'href': '../image_attachments_utils/behavex.css', 'rel': 'stylesheet'}
    )
    head_title = ET.SubElement(head, 'title')
    head_title.text = title
    body = ET.SubElement(root, 'body', {'class': 'gallery-body'})
    body_title = ET.SubElement(
        body,
        'h1',
        {'class': 'gallery-title'}
    )
    body_title.text = title
    folder = os.path.abspath(folder)

    container = ET.SubElement(body, 'div', {'class': 'gallery-container'})
    create_gallery_html_file(captions, container, folder, root)


def create_gallery_html_file(captions, container, folder, root):
    """
    This function creates an HTML file that contains all the images in a specified folder.

    Parameters:
    captions (dict): A dictionary where the keys are the image filenames (without extension) and the values are the captions for the images.
    container (Element): The parent element in the HTML structure where the images will be added.
    folder (str): The path to the folder containing the images.
    root (Element): The root element of the HTML structure.

    Returns:
    None
    """
    pictures_found = False
    for file_ in sorted(os.listdir(folder)):
        if file_.endswith('.png'):
            file_name = os.path.splitext(file_)[0]
            img_caption = u''
            if file_name in captions:
                for caption in captions[file_name]:
                    # Try and except structure to maintain compatibility decode cant be used with a string on python3
                    # noinspection PyBroadException
                    try:
                        img_caption = img_caption + caption.decode('utf8')
                    except:
                        img_caption = img_caption + str(caption)
            link = ET.SubElement(
                container,
                'a',
                {
                    'href': file_,
                    'data-lightbox': 'lightbox-test-results',
                    'data-title': img_caption,
                },
            )
            ET.SubElement(
                link,
                'img',
                {
                    'src': file_,
                    'class': 'gallery-image'
                },
            )
            pictures_found = True
    if pictures_found:
        tree = ET.ElementTree(root)
        # unicode has been changed to binary
        with open(os.path.join(os.path.abspath(folder), 'images.html'), 'wb') as html_gallery:
            html_gallery.write(b'<!DOCTYPE html>')
            tree.write(html_gallery)


def dump_images_to_disk(context):
    """
    This function dumps all the images stored in the context object to the disk.

    Parameters:
    context (object): The context object which contains the images to be dumped.

    Returns:
    None
    """
    if not context.bhximgs_attached_images:
        return
    for key in context.bhximgs_attached_images:
        write_image_binary_to_file(
            context.bhximgs_attached_images[key]['name'],
            context.bhximgs_attached_images[key]['img_stream'],
        )


def get_captions(context):
    """
    This function retrieves the captions for the images stored in the context object.

    Parameters:
    context (object): The context object which contains the images and their corresponding captions.

    Returns:
    dict: A dictionary where the keys are the image filenames (without extension) and the values are the captions for the images.
    """
    captions = {}
    for key in context.bhximgs_attached_images:
        captions[key] = context.bhximgs_attached_images[key]['steps']
    return captions


def normalize_log(log_line, line_breaks=1):
    """
    This function normalizes a log line by removing null characters and extracting the step from the line.

    Parameters:
    log_line (str): The log line to be normalized.

    Returns:
    str: The normalized log line.
    """
    log_line = log_line.replace('\0', '')
    pattern = re.compile(r'(given|when|then) \"(?P<step>.*)\"', re.MULTILINE)
    line = pattern.search(log_line)
    if line is not None:
        step = line.group('step')
    else:
        step = log_line
    step = step.replace('<', '').replace('>', '')
    for _ in range(line_breaks):
        step += '<br>'
    return step


def add_image_to_report_story(context):
    """
    This function adds an image to the report story.

    Parameters:
    context (object): The context object which contains various attributes used in the function, including the image stream.
    
    Returns:
    None
    """
    if context.bhximgs_image_stream:
        step_line = getattr(context, 'bhximgs_current_step_line', 0)
        key = f"{str(step_line).zfill(5)}{str(context.bhximgs_attached_images_idx).zfill(5)}"
        
        # Check if formatter is specified in context
        formatter = getattr(context, 'bhximgs_formatter', None)
        if formatter:
            # Extract scenario hash from the log_path (which is the scenario directory)
            scenario_hash = os.path.basename(context.bhximgs_attached_images_folder)
            name = os.path.join(os.getenv('LOGS'), f"{scenario_hash}_{key}.png")
        else:
            # Original behavior - save in scenario folder
            name = os.path.join(context.bhximgs_attached_images_folder, key) + '.png'
            
        context.bhximgs_attached_images[key] = {
            'img_stream': context.bhximgs_image_stream,
            'name': name,
            'steps': context.bhximgs_previous_steps[:],
        }


def write_image_binary_to_file(output_filename, image_binary):
    """
    This function writes an image binary to a file.

    Parameters:
    output_filename (str): The name of the output file where the image binary will be written.
    image_binary (bytes): The image binary to be written to the file.

    Returns:
    bool: True if the image binary was successfully written to the file, False otherwise.
    """
    try:
        with open(output_filename, 'wb') as image_file:
            image_file.write(image_binary)
    except IOError:
        return False
    return True
