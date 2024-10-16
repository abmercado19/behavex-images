[![Downloads](https://static.pepy.tech/badge/behavex-images)](https://pepy.tech/project/behavex-images)
[![PyPI version](https://badge.fury.io/py/behavex-images.svg)](https://badge.fury.io/py/behavex-images)
[![Dependency Status](https://img.shields.io/librariesio/github/abmercado19/behavex-images)](https://libraries.io/github/abmercado19/behavex-images)
[![License](https://img.shields.io/github/license/abmercado19/behavex-images.svg)](https://github.com/abmercado19/behavex-images/blob/main/LICENSE)
[![GitHub last commit](https://img.shields.io/github/last-commit/abmercado19/behavex-images.svg)](https://github.com/abmercado19/behavex-images/commits/main)

# behavex-images

An extension for the BehaveX library that enables attaching images to the generated HTML report.

## Installation

```bash
pip install behavex-images
```

## Features

- Attach images to BehaveX HTML reports
- Support for both binary image data and image files
- Flexible attachment conditions (always, only on failure, or never)
- Easy integration with existing BehaveX projects

## Usage

The `behavex-images` library provides four main methods for managing image attachments in BehaveX HTML reports:

### 1. Attach Image from Binary Data

```python
from behavex_images import image_attachments

image_attachments.attach_image_binary(context, image_binary)
```

- `context`: The BehaveX context object
- `image_binary`: Binary data of the image (JPG or PNG)

### 2. Attach Image from File

```python
from behavex_images import image_attachments

image_attachments.attach_image_file(context, file_path)
```

- `context`: The BehaveX context object
- `file_path`: Absolute path to the image file (JPG or PNG)

### 3. Set Attachment Condition

```python
from behavex_images import image_attachments
from behavex_images.image_attachments import AttachmentsCondition

image_attachments.set_attachments_condition(context, condition)
```

- `context`: The BehaveX context object
- `condition`: One of the following `AttachmentsCondition` values:
  - `ALWAYS`: Attach images to every report
  - `ONLY_ON_FAILURE`: Attach images only when a test fails (default)
  - `NEVER`: Do not attach any images

### 4. Clean All Attached Images

```python
from behavex_images import image_attachments

image_attachments.clean_all_attached_images(context)
```

- `context`: The BehaveX context object

## Examples

### Attaching an Image in a Step Definition

```python
from behavex_images import image_attachments

@given('I take a screenshot of the current page')
def step_impl(context):
    image_attachments.attach_image_file(context, 'path/to/screenshot.png')
```

### Using Hooks in environment.py

```python
from behavex_images import image_attachments
from behavex_images.image_attachments import AttachmentsCondition

def before_all(context):
    image_attachments.set_attachments_condition(context, AttachmentsCondition.ONLY_ON_FAILURE)

def after_step(context, step):
    # Assuming you're using Selenium WebDriver
    image_attachments.attach_image_binary(context, context.driver.get_screenshot_as_png())
```

## Sample Report Output

![Test Execution Report](https://github.com/abmercado19/behavex-images/blob/master/behavex_images/img/html_test_report.png?raw=true)

![Test Execution Report with Images](https://github.com/abmercado19/behavex-images/blob/master/behavex_images/img/html_test_report_2.png?raw=true)

![Test Execution Report Details](https://github.com/abmercado19/behavex-images/blob/master/behavex_images/img/html_test_report_3.png?raw=true)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the [MIT License](https://github.com/abmercado19/behavex-images/blob/main/LICENSE).