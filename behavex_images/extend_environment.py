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
    Extend Behave hooks with BehaveX hooks code.
    """

    global hooks_already_set
    
    # Detect behave version
    behave_version = getattr(behave, '__version__', '1.2.6')
    BEHAVE_VERSION = tuple(map(int, behave_version.split('.')[:2]))
    
    behave_run_hook = ModelRunner.run_hook
    behavex_images_env = sys.modules[__name__]
    is_dry_run = get_param('dry_run')

    def run_hook(self, name, context=None, *args):

        # Behave version compatibility: handle different hook signatures
        # Behave 1.2.6: run_hook(name, context, *args) where context is the actual context
        # Behave 1.3.0: run_hook(name, hook_target, *args) where hook_target is Scenario/Step/Feature/etc.

        actual_context = None
        hook_target = None

        try:
            if BEHAVE_VERSION >= (1, 3):
                # Behave 1.3.0+ behavior: context parameter is actually the hook target
                if name in ('before_all', 'after_all'):
                    # For before_all/after_all: context=None, get context from self
                    actual_context = getattr(self, 'context', None) or context
                else:
                    # For other hooks: context parameter is the hook target
                    hook_target = context
                    actual_context = getattr(self, 'context', None)

                    # If we can't get context from self, try to find it in args
                    if actual_context is None:
                        if args and hasattr(args[0], 'config'):
                            actual_context = args[0]
                        else:
                            # Last resort fallback
                            actual_context = context
            else:
                # Behave 1.2.6 behavior: context parameter is the actual context
                actual_context = context
                # For hooks other than before_all/after_all, hook_target is in args
                if name not in ('before_all', 'after_all') and args:
                    hook_target = args[0]
                elif name in ('before_all', 'after_all'):
                    # For before_all/after_all in 1.2.6, there might not be additional args
                    hook_target = None

                # Additional validation for Behave 1.2.6
                if actual_context is None and args:
                    # Sometimes context might be None, try to find it in args
                    for arg in args:
                        if hasattr(arg, 'config') or hasattr(arg, 'feature'):
                            actual_context = arg
                            break

            # Call the original behave hook first (except for after hooks)
            if name.startswith('before_') or name in ['before_tag', 'after_tag']:
                # noinspection PyUnresolvedReferences
                if not is_dry_run:
                    try:
                        behave_run_hook(self, name, context, *args)
                    except Exception as hook_error:
                        # Log but don't fail - some hooks might not be implemented in all versions
                        _log_exception_and_continue(f'behave_run_hook({name}) - before/tag', hook_error)

            # Call BehavEx hooks with proper arguments based on hook type
            # Only proceed if we have a valid context
            # NOTE: before_tag and after_tag hooks are not implemented in behavex-images
            if actual_context is not None:
                if name == 'before_all':
                    behavex_images_env.before_all(actual_context)
                elif name == 'before_feature':
                    feature = hook_target
                    # Validate feature object has expected attributes
                    if feature and (hasattr(feature, 'name') or hasattr(feature, 'filename')):
                        behavex_images_env.before_feature(actual_context, feature)
                elif name == 'before_scenario':
                    scenario = hook_target
                    # Validate scenario object has expected attributes
                    if scenario and hasattr(scenario, 'name'):
                        behavex_images_env.before_scenario(actual_context, scenario)
                elif name == 'before_step':
                    step = hook_target
                    # Validate step object has expected attributes
                    if step and (hasattr(step, 'name') or hasattr(step, 'step_type')):
                        behavex_images_env.before_step(actual_context, step)
                # elif name == 'before_tag':
                #     # NOT IMPLEMENTED: before_tag hook is not implemented in behavex-images
                #     pass
                # elif name == 'after_tag':
                #     # NOT IMPLEMENTED: after_tag hook is not implemented in behavex-images
                #     pass
                elif name == 'after_step':
                    step = hook_target
                    # Validate step object has expected attributes
                    if step and (hasattr(step, 'name') or hasattr(step, 'step_type')):
                        behavex_images_env.after_step(actual_context, step)
                elif name == 'after_scenario':
                    scenario = hook_target
                    # Validate scenario object has expected attributes
                    if scenario and hasattr(scenario, 'name') and hasattr(scenario, 'status'):
                        behavex_images_env.after_scenario(actual_context, scenario)
                elif name == 'after_feature':
                    feature = hook_target
                    # More lenient validation for after_feature
                    if feature and (hasattr(feature, 'name') or hasattr(feature, 'filename')):
                        behavex_images_env.after_feature(actual_context, feature)
                elif name == 'after_all':
                    behavex_images_env.after_all(actual_context)

            # Call the original behave hook after for after hooks
            if name.startswith('after_') and name not in ['after_tag']:
                # noinspection PyUnresolvedReferences
                if not is_dry_run:
                    try:
                        behave_run_hook(self, name, context, *args)
                    except Exception as hook_error:
                        # Log but don't fail - some hooks might not be implemented in all versions
                        _log_exception_and_continue(f'behave_run_hook({name}) - after', hook_error)

        except Exception as exception:
            # Log hook errors but don't break execution
            _log_exception_and_continue(f'run_hook({name})', exception)
            # Still call the original behave hook as fallback, but only if not in dry run
            if not is_dry_run:
                try:
                    behave_run_hook(self, name, context, *args)
                except Exception:
                    pass  # Avoid infinite recursion

    if not hooks_already_set:
        hooks_already_set = True
        ModelRunner.run_hook = run_hook

        # BEHAVE 1.3.0 COMPATIBILITY: Also override run_hook_with_capture
        # since all hooks are called via run_hook_with_capture in 1.3.0
        if BEHAVE_VERSION >= (1, 3):
            def run_hook_with_capture(self, hook_name, *args, **kwargs):
                # BEHAVE 1.3.0 COMPATIBILITY: Route ALL hooks through BehaveX run_hook
                # In behave 1.3.0, all hooks go through run_hook_with_capture first,
                # but we need them to go through BehaveX's run_hook for proper error handling
                # and consistent behavior across all hook types

                # For before_all/after_all: no hook target, context should be None
                # For other hooks: first arg is the hook target (feature, scenario, step)
                if hook_name in ('before_all', 'after_all'):
                    return run_hook(self, hook_name, None, *args)
                else:
                    # Pass the first argument as the hook target
                    hook_target = args[0] if args else None
                    remaining_args = args[1:] if len(args) > 1 else ()
                    return run_hook(self, hook_name, hook_target, *remaining_args)

            ModelRunner.run_hook_with_capture = run_hook_with_capture


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
                 (attachments_condition == AttachmentsCondition.ONLY_ON_FAILURE and getattr(scenario, 'status', None) in ['failed', 'error']))
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
