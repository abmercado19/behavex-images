# behavex-images
This implementation extends the BehaveX library to attach images to the generated HTML report

## Installation
pip install behavex-images

## Basic Usage

Two methods are provided to attach images to the BehaveX HTML report:
1. `attach_image_from_binary(context, image_binary)`
    - This function attaches an image from binary data to the test execution report. It takes two parameters:
        - `context`: The context object which contains various attributes used in the function.
        - `image_binary`: The binary data of the image to be attached.
    - The function first checks if the binary data is not empty. If it is, it uses the magic library to determine the format of the image. If the format is not JPG or PNG, it raises an exception.
    - If the format is JPG, it converts the image to PNG format and updates the binary data.
    - If the format is PNG, it calculates the hash of the image and compares it with the hash of the previous image. If the hashes are different, it increments the counter of captured screens and resets the list of previous steps.
    - It then updates the hash and binary data of the image in the context, and if the log stream is not closed, it appends the normalized log lines to the list of previous steps and truncates the log stream.
    - Finally, it adds the image to the context and deletes the binary data.

2. `attach_image_from_file(context, file_path)`
    - This function attaches an image from a file to the test execution report. It takes two parameters:
        - `context`: The context object which contains various attributes used in the function.
        - `file_path`: The absolute path to the image file to be attached.
    - The function first checks if the file exists at the given path. If it does not, it raises an exception.
    - If the file exists, it checks the file extension. If the extension is not JPG or PNG, it raises an exception.
    - It then opens the file in binary mode. If the file is a JPG, it converts the image to PNG format and updates the binary data. If the file is a PNG, it reads the binary data from the file.
    - Finally, it calls the function 'attach_image_from_binary' with the context and the binary data as arguments.


These methods can be used from the hooks provided in the environment.py file, or from step definitions to attach images to the HTML report. For example:

```python
from behave import *
from behavex_images import attach_image_from_file

@given('I take a screenshot from current page')
def step_impl(context):
    ...
    attach_image_from_file(context, 'path/to/image.png')
``` 
