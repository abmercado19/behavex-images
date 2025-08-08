# -*- coding: utf-8 -*-

# Standard library imports
import logging
import os
import shutil
import sys
import types

# Python 2/3 compatibility imports
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

# Third-party imports
try:
    from filelock import FileLock
    HAS_FILELOCK = True
except ImportError:
    HAS_FILELOCK = False

import behave
from behave.runner import ModelRunner

# Local behavex imports
from behavex import environment as bhx_benv
from behavex.conf_mgr import get_param

# Local behavex-images imports
from behavex_images.image_attachments import AttachmentsCondition
from behavex_images.utils import report_utils

# Configure filelock logging to reduce verbosity
logging.getLogger("filelock").setLevel(logging.INFO)

hooks_already_set = False
bhx_original_hooks = {}


def extend_behave_hooks():
    """
    Extend Behave hooks with behavex-images hooks code.
    
    This function provides optimized compatibility with both behave 1.2.6 and 1.3.0+ by
    detecting the behave version and adapting the hook signature accordingly:
    - behave 1.2.6: run_hook(self, name, context, *args)
    - behave 1.3.0+: run_hook(self, name, hook_target, *args)
    
    The implementation automatically detects the behave version and handles
    the appropriate calling convention for maximum reliability.
    """
    global hooks_already_set
    
    # Don't proceed if hooks are already set
    if hooks_already_set:
        return
    
    # Detect behave version for optimal compatibility
    behave_version = getattr(behave, '__version__', '1.2.6')  # Default to 1.2.6 if version unavailable
    is_behave_130_or_later = tuple(map(int, behave_version.split('.')[:2])) >= (1, 3)
    
    original_run_hook = ModelRunner.run_hook
    behavex_images_env = sys.modules[__name__]
    is_dry_run = get_param('dry_run') if hasattr(sys.modules.get('behavex.conf_mgr', None), 'get_param') else False

    def run_hook(self, name, hook_context_or_target=None, *args):
        """
        Optimized hook wrapper that handles both behave 1.2.6 and 1.3.0+ calling conventions.
        """
        try:
            # Determine context and hook target based on behave version and hook name
            actual_context = None
            hook_target = None
            
            if name in ('before_all', 'after_all'):
                # Special handling for before_all/after_all hooks
                if is_behave_130_or_later:
                    # In behave 1.3.0+, context is passed as hook_context_or_target for before_all/after_all
                    actual_context = hook_context_or_target or getattr(self, 'context', None)
                else:
                    # In behave 1.2.6, context is always the second parameter
                    actual_context = hook_context_or_target or getattr(self, 'context', None)
            else:
                # For feature/scenario/step hooks
                if is_behave_130_or_later:
                    # In behave 1.3.0+, hook_context_or_target is the actual target object
                    hook_target = hook_context_or_target
                    actual_context = getattr(hook_target, 'context', None) if hook_target else getattr(self, 'context', None)
                else:
                    # In behave 1.2.6, hook_context_or_target is the context, target is in args
                    actual_context = hook_context_or_target
                    hook_target = args[0] if args else None

            # Call original behave hook first for before hooks
            if name.startswith('before_') or name in ['before_tag', 'after_tag']:
                if not is_dry_run:
                    try:
                        original_run_hook(self, name, hook_context_or_target, *args)
                    except Exception as e:
                        _log_exception_and_continue(f'original behave {name} hook', e)

            # Execute behavex-images hooks with proper error handling
            try:
                if name == 'before_all':
                    if hasattr(behavex_images_env, 'before_all'):
                        behavex_images_env.before_all(actual_context)
                elif name == 'before_feature':
                    if hook_target and actual_context and hasattr(behavex_images_env, 'before_feature'):
                        behavex_images_env.before_feature(actual_context, hook_target)
                elif name == 'before_scenario':
                    if hook_target and actual_context and hasattr(behavex_images_env, 'before_scenario'):
                        behavex_images_env.before_scenario(actual_context, hook_target)
                elif name == 'before_step':
                    if hook_target and actual_context and hasattr(behavex_images_env, 'before_step'):
                        behavex_images_env.before_step(actual_context, hook_target)
                elif name == 'before_tag':
                    if args and actual_context and hasattr(behavex_images_env, 'before_tag'):
                        behavex_images_env.before_tag(actual_context, args[0])
                elif name == 'after_tag':
                    if args and actual_context and hasattr(behavex_images_env, 'after_tag'):
                        behavex_images_env.after_tag(actual_context, args[0])
                elif name == 'after_step':
                    if hook_target and actual_context and hasattr(behavex_images_env, 'after_step'):
                        behavex_images_env.after_step(actual_context, hook_target)
                elif name == 'after_scenario':
                    if hook_target and actual_context and hasattr(behavex_images_env, 'after_scenario'):
                        behavex_images_env.after_scenario(actual_context, hook_target)
                elif name == 'after_feature':
                    if hook_target and actual_context and hasattr(behavex_images_env, 'after_feature'):
                        behavex_images_env.after_feature(actual_context, hook_target)
                elif name == 'after_all':
                    if hasattr(behavex_images_env, 'after_all'):
                        behavex_images_env.after_all(actual_context)
            except Exception as e:
                _log_exception_and_continue(f'behavex-images {name} hook', e)

            # Call original behave hook after for after hooks
            if name.startswith('after_') and name not in ['after_tag']:
                if not is_dry_run:
                    try:
                        original_run_hook(self, name, hook_context_or_target, *args)
                    except Exception as e:
                        _log_exception_and_continue(f'original behave {name} hook', e)
                        
        except Exception as e:
            _log_exception_and_continue(f'behavex-images hook wrapper for {name}', e)

    # Replace the original run_hook method
    if not hooks_already_set:
        hooks_already_set = True
        ModelRunner.run_hook = run_hook


def before_all(context):
    """
    This function is executed before all features are run.

    It initializes the screenshot utilities flag and copies gallery utilities only if needed.
    If an exception occurs during this process, it is logged and the execution continues.

    Parameters:
    context (object): The context object which contains various attributes used in the function.

    Returns:
    None
    """
    try:
        # Context should not be None in normal behave execution
        if context is None:
            _log_exception_and_continue('before_all (behavex-images)', 
                                       Exception("Context is None - this may indicate a behave version compatibility issue or test setup problem"))
            return
            
        # Initialize the flag - by default we need screenshot utils unless a formatter is specified
        context.bhximgs_needs_screenshot_utils = not bool(get_param('formatter', None))
        if getattr(context, 'bhximgs_needs_screenshot_utils', False):
            copy_gallery_utilities()
    except Exception as ex:
        _log_exception_and_continue('before_all (behavex-images)', ex)


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

    It sets up the initial configuration for attaching images to the report. It also adds a new log handler to the logger.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    scenario (object): The scenario object that is about to be run.

    Returns:
    None
    """
    try:
        # Context should not be None in normal behave execution
        if context is None:
            _log_exception_and_continue('before_scenario (behavex-images)', 
                                       Exception("Context is None - this may indicate a behave version compatibility issue or test setup problem"))
            return
            
        # Check for formatter in command line arguments
        context.bhximgs_formatter = get_param('formatter', None)
        # Note: bhximgs_needs_screenshot_utils is already set in before_all()
        # Setup initial configuration for attaching images and logging
        context.bhximgs_image_hash = None
        context.bhximgs_attached_images_idx = 0
        context.bhximgs_attached_images = {}
        context.bhximgs_previous_steps = []
        context.bhximgs_image_stream = None
        context.bhximgs_log_stream = StringIO()
        context.bhximgs_step_log_handler = logging.StreamHandler(context.bhximgs_log_stream)
        # Initialize the last feature line number
        context.bhximgs_last_feature_line = 0
        # Adding a new log handler to logger
        context.bhximgs_step_log_handler.setFormatter(bhx_benv._get_log_formatter())
        logging.getLogger().addHandler(context.bhximgs_step_log_handler)
        # Set the attached images folder to the scenario log path
        context.bhximgs_attached_images_folder = getattr(context, 'log_path', None)
    except Exception as ex:
        _log_exception_and_continue('before_scenario (behavex-images)', ex)


def before_step(context, step):
    """
    This function is executed before each step in a scenario is run.

    It stores the current step's line number in the context for use in image naming.
    If the step is not from a feature file, it uses the last known feature file line number.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    step (object): The step object that is about to be run.

    Returns:
    None
    """
    try:
        # Context and step should not be None in normal behave execution
        if context is None:
            _log_exception_and_continue('before_step (behavex-images)', 
                                       Exception("Context is None - this may indicate a behave version compatibility issue or test setup problem"))
            return
        if step is None:
            _log_exception_and_continue('before_step (behavex-images)', 
                                       Exception("Step is None - this may indicate a behave version compatibility issue or test setup problem"))
            return
            
        if hasattr(step, 'filename') and '.feature' in step.filename:
            context.bhximgs_last_feature_line = step.line if hasattr(step, 'line') else 0
            context.bhximgs_current_step_line = context.bhximgs_last_feature_line
        else:
            context.bhximgs_current_step_line = getattr(context, 'bhximgs_last_feature_line', 0)
    except Exception as ex:
        _log_exception_and_continue('before_step (behavex-images)', ex)


def after_step(context, step):
    """
    This function is executed after each step in a scenario is run.

    Currently, this function does not perform any operations. It can be used to set up any necessary state or perform any configuration that should be done after a step is run.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    step (object): The step object that has just been run.

    Returns:
    None
    """
    pass


def after_scenario(context, scenario):
    """
    This function is executed after each scenario is run.

    If the context indicates that images should be attached to the report:
    - Always dumps the captured images to disk
    - Creates a gallery of these images only if screenshot utilities are needed (i.e. no formatter specified)

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    scenario (object): The scenario object that has just been run.

    Returns:
    None
    """
    try:
        # Context should not be None in normal behave execution
        if context is None:
            _log_exception_and_continue('after_scenario (behavex-images)', 
                                       Exception("Context is None - this may indicate a behave version compatibility issue or test setup problem"))
            return
            
        attachments_condition = getattr(context, 'bhximgs_attachments_condition', None)
        if (attachments_condition and
                ((attachments_condition == AttachmentsCondition.ALWAYS) or
                 (attachments_condition == AttachmentsCondition.ONLY_ON_FAILURE and getattr(scenario, 'status', None) == 'failed'))
        ):
            # Always dump images to disk - they may be needed by the formatter
            report_utils.dump_images_to_disk(context)
            
            # Only create gallery if screenshot utilities are needed
            if getattr(context, 'bhximgs_needs_screenshot_utils', False):
                captions = report_utils.get_captions(context)
                attached_images_folder = getattr(context, 'bhximgs_attached_images_folder', None)
                if attached_images_folder:
                    report_utils.create_gallery(
                        attached_images_folder,
                        title=getattr(scenario, 'name', 'Scenario'),
                        captions=captions
                    )
    except Exception as ex:
        _log_exception_and_continue('after_scenario (behavex-images)', ex)
    finally:
        # Safe cleanup - this should always run even if context was None
        if context is not None:
            log_handler = getattr(context, 'bhximgs_step_log_handler', None)
            if log_handler:
                close_log_handler(log_handler)


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
    Copies gallery utilities to the output directory in a multiprocess-safe manner.

    It uses a file lock to ensure that only one process performs the copy. A
    completion marker file is used to signal that the copy is finished, which
    avoids unnecessary locking and copying in subsequent runs.

    If the `filelock` library is not available, it falls back to a non-locking
    mechanism that is less safe but still attempts to prevent duplicate work by
    checking for the completion marker.
    """
    logs_env = os.getenv('LOGS')
    if not logs_env:
        return

    destination_path = os.path.join(logs_env, 'image_attachments_utils')
    completion_marker = os.path.join(destination_path, '.copy_complete')

    if os.path.exists(completion_marker):
        return

    if HAS_FILELOCK:
        lock_file_path = destination_path + '.lock'
        try:
            with FileLock(lock_file_path, timeout=10):
                # Re-check after acquiring the lock to handle race conditions
                if os.path.exists(completion_marker):
                    return
                _perform_copy(destination_path, completion_marker)
        except Exception: # pylint: disable=broad-exception-caught
            # If locking fails (e.g., timeout), assume another process is handling it.
            pass
    else:
        # Fallback for when filelock is not installed. This is not fully
        # race-proof, but _perform_copy is idempotent.
        try:
            _perform_copy(destination_path, completion_marker)
        except OSError: # pylint: disable=broad-exception-caught
            # Silently ignore errors, as another process might be copying.
            pass


def _perform_copy(destination_path, completion_marker):
    """
    Executes the file copy operation and creates a completion marker.

    It uses the most efficient and safe method available to copy the directory tree.
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(current_path, 'utils', 'support_files')

    # The calling function `copy_gallery_utilities` already handles exceptions
    # that might occur during the copy operation. For Python 3.8+,
    # copytree has dirs_exist_ok. For older versions, we use a custom implementation.
    if sys.version_info >= (3, 8):
        shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
    else:
        # Custom implementation for older Python versions
        _copy_tree_custom(source_path, destination_path)
    # Create a marker to indicate that the copy is complete.
    with open(completion_marker, 'w') as f:
        f.write('complete')


def _copy_tree_custom(src, dst):
    """
    Custom implementation of copy_tree that works across all Python versions.
    Recursively copies files and directories from src to dst, creating
    directories as needed and overwriting existing files.
    """
    if not os.path.exists(dst):
        os.makedirs(dst)
    
    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        dst_item = os.path.join(dst, item)
        
        if os.path.isdir(src_item):
            _copy_tree_custom(src_item, dst_item)
        else:
            shutil.copy2(src_item, dst_item)


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
        try:
            if hasattr(handler, 'stream') and hasattr(handler.stream, 'close'):
                handler.stream.close()
            logging.getLogger().removeHandler(handler)
        except Exception as ex:
            _log_exception_and_continue('close_log_handler (behavex-images)', ex)


def _log_exception_and_continue(module, exception):
    """Logs any exception that occurs without raising it"""
    error_message = f"Unexpected error in '{module}' function:"
    logging.error(error_message)
    logging.error(exception)


# This line of code calls the function 'extend_behave_hooks'.
# The 'extend_behave_hooks' function extends the BehaveX hooks with behavex-images hooks code.
# It saves the original BehaveX environment hooks and replaces them with
# functions that call both the original BehaveX hook and the behavex-images hook.
# The hooks are only set once, and subsequent calls to this function will not modify hooks again.
extend_behave_hooks()
