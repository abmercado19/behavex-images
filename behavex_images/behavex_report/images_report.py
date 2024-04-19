# -*- coding: utf-8 -*-
"""
BehaveX - BDD testing library based on Behave
"""
# pylint: disable=W0403, W0102

# __future__ has been added in order to maintain compatibility
from __future__ import absolute_import, print_function

import logging
import os
import re
import xml.etree.ElementTree as ET
import magic
from io import BytesIO

import selenium
from PIL import Image

from behavex_images.images import attach_image_from_binary
from behavex_images.utils import image_hash


def create_gallery(folder, title='BehaveX', captions={}):
    """generate_gallery from already provided images"""
    # Create HTML
    root = ET.Element('html', {'style': 'height: 100%'})
    head = ET.SubElement(root, 'head')
    script = ET.SubElement(
        head, 'script', {'type': 'text/javascript', 'charset': 'utf-8'}
    )
    script.text = ' '
    script = ET.SubElement(
        head,
        'script',
        {
            'src': '../screenshots_utils/jquery-1.11.0.' 'min.js',
            'type': 'text/javascript',
        },
    )
    script.text = ' '
    script = ET.SubElement(
        head,
        'script',
        {'src': '../screenshots_utils/lightbox.js', 'type': 'text/javascript'},
    )
    script.text = ' '
    ET.SubElement(
        head, 'link', {'rel': 'stylesheet', 'href': '../screenshots_utils/lightbox.css'}
    )
    head_title = ET.SubElement(head, 'title')
    head_title.text = title
    body = ET.SubElement(root, 'body', {'style': 'height: 100%'})
    body_title = ET.SubElement(
        body,
        'h1',
        {
            'style': 'width: 100%;float:left;'
            'text-align:center;'
            'font-size:18px;'
            'font-family:Helvetica'
        },
    )
    body_title.text = title
    folder = os.path.abspath(folder)

    container = ET.SubElement(body, 'div', {'style': 'height: 100%'})
    _create_image_html(captions, container, folder, root)


def _create_image_html(captions, container, folder, root):
    """Create image for html"""
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
                    'style': 'max-height: 250px; max-width: 250px; pa'
                    'dding: 30px;border: 1px solid silver',
                },
            )
            pictures_found = True
    if pictures_found:
        tree = ET.ElementTree(root)
        # unicode has been changed to binary
        with open(
            os.path.join(os.path.abspath(folder), 'images.html'), 'wb'
        ) as screenshots_gallery:
            screenshots_gallery.write(b'<!DOCTYPE html>')
            tree.write(screenshots_gallery)


def dump_images_to_disk(context):
    """Dump screens"""
    if not context.bhx_captured_screens:
        return
    for key in context.bhx_captured_screens:
        write_image_binary_to_file(
            context.bhx_captured_screens[key]['name'],
            context.bhx_captured_screens[key]['img_stream'],
        )


def get_captions(context):
    """Get captions"""
    captions = {}
    for key in context.bhx_captured_screens:
        captions[key] = context.bhx_captured_screens[key]['steps']
    return captions


def capture_browser_image(context, step=''):
    """Capture image of browser"""
    image_stream = get_browser_image(context)
    if image_stream:
        try:
            image_stream_hash = image_hash.dhash(Image.open(BytesIO(image_stream)))
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
        context.bhx_image_stream = image_stream
        if not context.bhx_log_stream.closed:
            for log_line in context.bhx_log_stream.getvalue().splitlines(True):
                step = _normalize_log(log_line)
                context.bhx_previous_steps.append(step)
            context.bhx_log_stream.truncate(0)
        add_image_to_report_story(context)
        del image_stream


def _normalize_log(log_line):
    """Normalize log"""
    log_line = log_line.replace('\0', '')
    pattern = re.compile(r'(given|when|then) \"(?P<step>.*)\"', re.MULTILINE)
    line = pattern.search(log_line)
    if line is not None:
        step = line.group('step')
    else:
        step = log_line
    step = step.replace('<', '').replace('>', '')
    step += '<br>'
    return step


def add_image_to_report_story(context):
    """Add image"""
    if context.bhx_image_stream:
        key = str(context.bhx_capture_screens_number).zfill(4)
        name = os.path.join(context.bhx_capture_screens_folder, key) + '.png'
        context.bhx_captured_screens[key] = {
            'img_stream': context.bhx_image_stream,
            'name': name,
            'steps': context.bhx_previous_steps,
        }


def get_browser_image(context):
    """Get browser image"""
    image_stream = None
    for browser in context.browsers.values():
        try:
            image_stream = browser.driver.get_screenshot_as_png()
        except selenium.common.exceptions.WebDriverException as exception:
            print(exception)
            logging.error('could not save_screenshot')
            # pickle.dump(
            # browser.driver.page_source.encode(encoding='UTF-8'), log)
    return image_stream


def write_image_binary_to_file(output_filename, image_binary):
    """Save image"""
    try:
        with open(output_filename, 'wb') as image_file:
            image_file.write(image_binary)
    except IOError:
        return False
    return True
