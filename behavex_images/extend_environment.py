# -*- coding: utf-8 -*-
import logging
import os
import shutil
import sys

from behave.runner import ModelRunner
from behavex import environment as bhx_benv
from behavex.outputs.report_utils import normalize_filename
from behavex.utils import try_operate_descriptor


# cStringIO has been changed to StringIO or io
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

FWK_PATH = os.getenv('BEHAVEX_PATH')

hooks_already_set = False


def extend_behave_hooks():
    """
    This function extends the Behave hooks with behavex-images hooks code.

    It modifies the run_hook method of the ModelRunner class to include additional hooks from the BehaveX environment.
    The hooks are only set once, and subsequent calls to this function will not modify the run_hook method again.

    Parameters:
    None

    Returns:
    None
    """
    global hooks_already_set
    behave_run_hook = ModelRunner.run_hook
    behavex_images_env = sys.modules[__name__]

    def run_hook(self, name, context, *args):
        if name == 'before_all':
            # noinspection PyUnresolvedReferences
            behavex_images_env.before_all(context)
            behave_run_hook(self, name, context, *args)
        elif name == 'before_feature':
            behave_run_hook(self, name, context, *args)
            # noinspection PyUnresolvedReferences
            behavex_images_env.before_feature(context, *args)
        elif name == 'before_scenario':
            behave_run_hook(self, name, context, *args)
            # noinspection PyUnresolvedReferences
            behavex_images_env.before_scenario(context, *args)
        elif name == 'after_step':
            behave_run_hook(self, name, context, *args)
            # noinspection PyUnresolvedReferences
            behavex_images_env.after_step(context, *args)
        elif name == 'after_scenario':
            behave_run_hook(self, name, context, *args)
            # noinspection PyUnresolvedReferences
            behavex_images_env.after_scenario(context, *args)
        elif name == 'after_feature':
            # noinspection PyUnresolvedReferences
            behavex_images_env.after_feature(context, *args)
            behave_run_hook(self, name, context, *args)
        elif name == 'after_all':
            # noinspection PyUnresolvedReferences
            behavex_images_env.after_all(context, *args)
            behave_run_hook(self, name, context, *args)
        else:
            behave_run_hook(self, name, context, *args)

    if not hooks_already_set:
        hooks_already_set = True
        ModelRunner.run_hook = run_hook


def before_all(context):
    """
    This function is executed before all features are run.

    It attempts to copy gallery utilities to the appropriate location. If an exception occurs during this process, it is logged and the execution continues.

    Parameters:
    context (object): The context object which contains various attributes used in the function.

    Returns:
    None
    """
    try:
        copy_gallery_utilities()
    except Exception as ex:
        bhx_benv._log_exception_and_continue('before_all (behavex-images)', exception=ex)


def before_feature(context, feature):
    """
    This function is executed before each feature is run.

    Currently, this function does not perform any operations. It can be used to set up any necessary state or perform any configuration that should be done before a feature is run.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    feature (object): The feature object that is about to be run.

    Returns:
    None
    """
    pass


def before_scenario(context, scenario):
    """
    This function is executed before each scenario is run.

    It sets up the initial configuration for capturing screenshots and logging. It also adds a new log handler to the logger.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    scenario (object): The scenario object that is about to be run.

    Returns:
    None
    """
    try:
        # Setup initial configuration for capturing screenshots
        context.capture_screens_after_step = False
        context.bhx_image_hash = None
        context.bhx_capture_screens_folder = context.log_path
        context.bhx_capture_screens_number = 0
        context.bhx_captured_screens = {}
        context.bhx_previous_steps = []
        context.bhx_image_stream = None
        context.bhx_log_stream = StringIO()
        context.bhx_step_log_handler = logging.StreamHandler(context.bhx_log_stream)

        # Adding a new log handler to logger
        context.bhx_step_log_handler.setFormatter(bhx_benv._get_log_formatter())
        logging.getLogger().addHandler(context.bhx_step_log_handler)
    except Exception as ex:
        bhx_benv._log_exception_and_continue(
            'before_scenario (behavex-images)', exception=ex
        )


def before_step(context, step):
    """
    This function is executed before each step in a scenario is run.

    Currently, this function does not perform any operations. It can be used to set up any necessary state or perform any configuration that should be done before a step is run.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    step (object): The step object that is about to be run.

    Returns:
    None
    """
    pass


def after_step(context, step):
    """
    This function is executed after each step in a scenario is run.

    If the context indicates that the scenario is running, it captures a browser image for the current step.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    step (object): The step object that has just been run.

    Returns:
    None
    """
    try:
        if context.bhx_inside_scenario:
            from report import images_report

            images_report.capture_browser_image(
                context, step=normalize_filename(step.name)
            )
    except Exception as ex:
        bhx_benv._log_exception_and_continue('after_step (behavex-images)', exception=ex)


def after_scenario(context, scenario):
    """
    This function is executed after each scenario is run.

    If the context indicates that screenshots should be captured after each step, or if the scenario has failed, it dumps the captured images to disk and creates a gallery of these images.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    scenario (object): The scenario object that has just been run.

    Returns:
    None
    """
    try:
        if (
            hasattr(context, 'capture_screens_after_step')
            and context.capture_screens_after_step is True
            or scenario.status == 'failed'
        ):
            from report import images_report

            images_report.dump_images_to_disk(context)
            captions = images_report.get_captions(context)
            images_report.create_gallery(
                context.bhx_capture_screens_folder,
                title=scenario.name,
                captions=captions,
            )
        close_log_handler(context.bhx_step_log_handler)
    except Exception as ex:
        bhx_benv._log_exception_and_continue(
            'after_scenario (behavex-images)', exception=ex
        )


def after_feature(context, feature):
    """
    This function is executed after each feature is run.

    Currently, this function does not perform any operations. It can be used to set up any necessary state or perform any configuration that should be done after a feature is run.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    feature (object): The feature object that has just been run.

    Returns:
    None
    """
    pass


def after_all(context):
    """
    This function is executed after all features are run.

    Currently, this function does not perform any operations. It can be used to set up any necessary state or perform any configuration that should be done after all features are run.

    Parameters:
    context (object): The context object which contains various attributes used in the function.

    Returns:
    None
    """
    pass

def copy_gallery_utilities():
    """
    This function copies the gallery utilities to the appropriate location.

    It checks if the destination path exists. If it does not, it creates the path and copies the gallery utilities from the source path to the destination path. If the destination path already exists, it removes the existing files before copying the new ones.

    Parameters:
    None

    Returns:
    None
    """
    destination_path = os.path.join(os.getenv('LOGS'), 'screenshots_utils')
    if not os.path.exists(destination_path):
        current_path = os.path.dirname(os.path.abspath(__file__))
        screenshots_path = [current_path, 'utils', 'support_files']
        screenshots_path = os.path.join(*screenshots_path)
        if os.path.exists(destination_path):
            try_operate_descriptor(
                destination_path, lambda: shutil.rmtree(destination_path)
            )

        def execution():
            return shutil.copytree(screenshots_path, destination_path)

        try_operate_descriptor(destination_path, execution)


def close_log_handler(handler):
    """
    This function closes the current log handler and removes it from the logger.

    If the handler has a stream attribute and the stream has a close method, it calls the close method on the stream. Then it removes the handler from the logger.

    Parameters:
    handler (object): The log handler to be closed and removed.

    Returns:
    None
    """
    if handler is not None:
        if hasattr(handler, 'stream') and hasattr(handler.stream, 'close'):
            handler.stream.close()
        logging.getLogger().removeHandler(handler)


# This line of code calls the function 'extend_behave_hooks'.
# The 'extend_behave_hooks' function extends the Behave hooks with behavex-images hooks code.
# It modifies the run_hook method of the ModelRunner class to include additional hooks from the BehaveX environment.
# The hooks are only set once, and subsequent calls to this function will not modify the run_hook method again.
extend_behave_hooks()
