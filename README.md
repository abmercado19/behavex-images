# behavex-images
This implementation extends the BehaveX library to enable attaching images to the generated HTML report

## Installation
pip install behavex-images

## Basic Usage

The following methods are provided to manage image attachments in the BehaveX HTML report:
1. `attach_image_binary(context, image_binary)`
    - This function attaches an image from binary data to the test execution report. It takes two parameters:
        - `context`: The context object which contains various attributes used in the function.
        - `image_binary`: The binary data of the image to be attached.
    - The function determines the binary format to ensure it maps to a JPG or PNG image. Otherwise, it raises an exception.
    - Then, it converts the image to PNG format (if it is not already in that format) to add it to the gallery.

2. `attach_image_file(context, file_path)`
    - This function attaches an image from a file to the test execution report. It takes two parameters:
        - `context`: The context object which contains various attributes used in the function.
        - `file_path`: The absolute path to the image file to be attached.
    - The function first checks if the file exists at the given path. If it does not, it raises an exception.
    - If the file exists, it checks the file extension. If the extension is not JPG or PNG, it raises an exception.
    - Then, it converts the image to PNG format (if it is not already in that format) to add it to the gallery.

3. `set_attachments_condition(context, condition)`
    - This function sets the condition to attach images to the HTML report. It takes two parameters:
        - `context`: The context object which contains various attributes used in the function.
        - `condition`: The condition to attach images to the HTML report. Possible values:
          - AttachmentsCondition.ALWAYS: Attach images to the HTML report always.
          - AttachmentsCondition.ONLY_ON_FAILURE: Attach images to the HTML report only when the test fails. This is the default value.
          - AttachmentsCondition.NEVER: Do not attach images to the HTML report, no matter the test result.

4. `clean_all_attached_images`
    - This function removes all images already attached to the HTML report for the current test scenario.

## Examples
The provided methods can be used from the hooks available in the environment.py file, or directly from step definitions to attach images to the HTML report. For example:

* **Example 1**: Attaching an image file from a step definition
```python
...
from behavex_images import image_attachments

@given('I take a screenshot from current page')
def step_impl(context):
    image_attachments.attach_image_file(context, 'path/to/image.png')
``` 

* **Example 2**: Attaching an image binary from the `after_step` hook in environment.py
```python
...
from behavex_images import image_attachments
from behavex_images.image_attachments import AttachmentsCondition

def before_all(context):
    image_attachements.set_attachments_condition(context, AttachmentsCondition.ONLY_ON_FAILURE)

def after_step(context, step):
    image_attachements.attach_image_binary(context, selenium_driver.get_screenshot_as_png())
```


![test execution report](https://github.com/abmercado19/behavex-images/blob/master/behavex_images/img/html_test_report.png?raw=true)

![test execution report](https://github.com/abmercado19/behavex-images/blob/master/behavex_images/img/html_test_report_2.png?raw=true)

![test execution report](https://github.com/abmercado19/behavex-images/blob/master/behavex_images/img/html_test_report_3.png?raw=true)
