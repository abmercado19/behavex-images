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
    Extend Behave hooks with BehaveX hooks code.
    """
    global hooks_already_set
    behave_run_hook = ModelRunner.run_hook
    behavex_env = sys.modules[__name__]

    def run_hook(self, name, context, *args):
        if name == 'before_all':
            # noinspection PyUnresolvedReferences
            behavex_env.before_all(context)
            behave_run_hook(self, name, context, *args)
        elif name == 'before_feature':
            behave_run_hook(self, name, context, *args)
            # noinspection PyUnresolvedReferences
            behavex_env.before_feature(context, *args)
        elif name == 'before_scenario':
            behave_run_hook(self, name, context, *args)
            # noinspection PyUnresolvedReferences
            behavex_env.before_scenario(context, *args)
        elif name == 'after_step':
            behave_run_hook(self, name, context, *args)
            # noinspection PyUnresolvedReferences
            behavex_env.after_step(context, *args)
        elif name == 'after_scenario':
            behave_run_hook(self, name, context, *args)
            # noinspection PyUnresolvedReferences
            behavex_env.after_scenario(context, *args)
        elif name == 'after_feature':
            # noinspection PyUnresolvedReferences
            behavex_env.after_feature(context, *args)
            behave_run_hook(self, name, context, *args)
        elif name == 'after_all':
            # noinspection PyUnresolvedReferences
            behavex_env.after_all(context, *args)
            behave_run_hook(self, name, context, *args)
        else:
            behave_run_hook(self, name, context, *args)

    if not hooks_already_set:
        hooks_already_set = True
        ModelRunner.run_hook = run_hook


def before_all(context):
    try:
        _copy_screenshot_utilities()
    except Exception as ex:
        bhx_benv._log_exception_and_continue('before_all (behavex-web)', exception=ex)


def before_feature(context, feature):
    pass


def before_scenario(context, scenario):
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
    pass


def after_step(context, step):
    try:
        if context.bhx_inside_scenario:
            from report.behavex_images import images_report

            images_report.capture_browser_image(
                context, step=normalize_filename(step.name)
            )
    except Exception as ex:
        bhx_benv._log_exception_and_continue('after_step (behavex-images)', exception=ex)


def after_scenario(context, scenario):
    try:
        if (
            hasattr(context, 'capture_screens_after_step')
            and context.capture_screens_after_step is True
            or scenario.status == 'failed'
        ):
            from report.behavex_images import images_report

            images_report.dump_images_to_disk(context)
            captions = images_report.get_captions(context)
            images_report.create_gallery(
                context.bhx_capture_screens_folder,
                title=scenario.name,
                captions=captions,
            )
        _close_log_handler(context.bhx_step_log_handler)
    except Exception as ex:
        bhx_benv._log_exception_and_continue(
            'after_scenario (behavex-images)', exception=ex
        )


def after_feature(context, feature):
    pass


def after_all(context):
    pass


def _copy_screenshot_utilities():
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


def _close_log_handler(handler):
    """Closing current log handlers and removing them from logger"""
    if handler is not None:
        if hasattr(handler, 'stream') and hasattr(handler.stream, 'close'):
            handler.stream.close()
        logging.getLogger().removeHandler(handler)


extend_behave_hooks()
