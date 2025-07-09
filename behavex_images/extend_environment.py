# -*- coding: utf-8 -*-
import logging
import os
import shutil
import sys
import types

# Configure filelock logging to reduce verbosity
logging.getLogger("filelock").setLevel(logging.INFO)

try:
    from filelock import FileLock
    HAS_FILELOCK = True
except ImportError:
    HAS_FILELOCK = False

from behave.runner import ModelRunner
from behavex import environment as bhx_benv
from behavex.outputs.report_utils import normalize_filename
from behavex.conf_mgr import get_param
from behavex_images.image_attachments import AttachmentsCondition
from behavex_images.utils import report_utils

# cStringIO has been changed to StringIO or io
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

hooks_already_set = False
bhx_original_hooks = {}


def extend_behave_hooks():
    """
    This function integrates behavex-images hooks with BehaveX's hook system.
    
    It uses a two-phase approach to ensure compatibility regardless of initialization order:
    1. First stores references to BehaveX hooks (or sets up to capture them later)
    2. Then creates wrapper functions that safely call both sets of hooks in the proper order
    
    This approach handles cases where BehaveX hasn't initialized its hooks yet and
    prevents double execution of hooks.

    Parameters:
    None

    Returns:
    None
    """
    global hooks_already_set, bhx_original_hooks
    
    # Don't proceed if hooks are already set
    if hooks_already_set:
        return
        
    # Get reference to this module for calling hooks
    behavex_images_env = sys.modules[__name__]
    is_dry_run = True if os.environ.get('DRY_RUN', "false").lower() == "true" else False
    
    # Function to create a hook wrapper that will safely call both hooks in the right order
    def create_hook_wrapper(hook_name, bhx_first=True):
        """Create a wrapper for the specified hook type
        
        Args:
            hook_name: The name of the hook (e.g., 'before_all')
            bhx_first: Whether to call BehaveX's hook first (True) or behavex-images hook first (False)
            
        Returns:
            A wrapper function that handles the proper hook execution order
        """
        # Get the behavex-images hook function
        img_hook = getattr(behavex_images_env, hook_name, lambda *args: None)
        
        def wrapper(*args):
            # Get the current BehaveX hook (which might have been set after our initialization)
            orig_hook = bhx_original_hooks.get(hook_name)
            if orig_hook is None:
                # If we don't have a reference to the original, get it now
                orig_hook = getattr(bhx_benv, hook_name, lambda *args: None)
                bhx_original_hooks[hook_name] = orig_hook
            
            result = None
            
            try:
                if bhx_first:
                    # Call BehaveX hook first
                    result = orig_hook(*args)
                    
                    # Then call behavex-images hook
                    if not is_dry_run:
                        img_hook(*args)
                else:
                    # Call behavex-images hook first
                    if not is_dry_run:
                        img_hook(*args)
                        
                    # Then call BehaveX hook
                    result = orig_hook(*args)
            except Exception as ex:
                bhx_benv._log_exception_and_continue(f'{hook_name} (behavex-images)', exception=ex)
                
                # If exception occurred before calling BehaveX hook, call it now
                if not bhx_first and result is None:
                    result = orig_hook(*args)
                
            return result
            
        return wrapper
        
    # Create wrappers for all hook types with the right execution order
    hooks_to_wrap = {
        # BehaveX hook first
        'before_feature': True,
        'before_scenario': True,
        'before_step': True,
        'after_step': True,
        'after_scenario': True,
        
        # behavex-images hook first
        'before_all': False,
        'after_feature': False,
        'after_all': False
    }
    
    # Create and register all hook wrappers
    for hook_name, bhx_first in hooks_to_wrap.items():
        # Create wrapper function
        wrapper = create_hook_wrapper(hook_name, bhx_first)
        
        # Save reference to current BehaveX hook function if it exists
        if hasattr(bhx_benv, hook_name) and isinstance(getattr(bhx_benv, hook_name), types.FunctionType):
            bhx_original_hooks[hook_name] = getattr(bhx_benv, hook_name)
            
        # Replace the BehaveX hook with our wrapper
        setattr(bhx_benv, hook_name, wrapper)
    
    hooks_already_set = True


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
        # Initialize the flag - by default we need screenshot utils unless a formatter is specified
        context.bhximgs_needs_screenshot_utils = not bool(get_param('formatter', None))
        if context.bhximgs_needs_screenshot_utils:
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

    It sets up the initial configuration for attaching images to the report. It also adds a new log handler to the logger.

    Parameters:
    context (object): The context object which contains various attributes used in the function.
    scenario (object): The scenario object that is about to be run.

    Returns:
    None
    """
    try:
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
        context.bhximgs_attached_images_folder = context.log_path
    except Exception as ex:
        bhx_benv._log_exception_and_continue('before_scenario (behavex-images)', exception=ex)


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
        if hasattr(step, 'filename') and '.feature' in step.filename:
            context.bhximgs_last_feature_line = step.line if hasattr(step, 'line') else 0
            context.bhximgs_current_step_line = context.bhximgs_last_feature_line
        else:
            context.bhximgs_current_step_line = context.bhximgs_last_feature_line
    except Exception as ex:
        bhx_benv._log_exception_and_continue('before_step (behavex-images)', exception=ex)


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
        if ("bhximgs_attachments_condition" in context and
                ((context.bhximgs_attachments_condition == AttachmentsCondition.ALWAYS) or
                 (context.bhximgs_attachments_condition == AttachmentsCondition.ONLY_ON_FAILURE and scenario.status == 'failed'))
        ):
            # Always dump images to disk - they may be needed by the formatter
            report_utils.dump_images_to_disk(context)
            
            # Only create gallery if screenshot utilities are needed
            if context.bhximgs_needs_screenshot_utils:
                captions = report_utils.get_captions(context)
                report_utils.create_gallery(
                    context.bhximgs_attached_images_folder,
                    title=scenario.name,
                    captions=captions
                )
        close_log_handler(context.bhximgs_step_log_handler)
    except Exception as ex:
        bhx_benv._log_exception_and_continue('after_scenario (behavex-images)', exception=ex)


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
        if hasattr(handler, 'stream') and hasattr(handler.stream, 'close'):
            handler.stream.close()
        logging.getLogger().removeHandler(handler)


# This line of code calls the function 'extend_behave_hooks'.
# The 'extend_behave_hooks' function extends the BehaveX hooks with behavex-images hooks code.
# It saves the original BehaveX environment hooks and replaces them with
# functions that call both the original BehaveX hook and the behavex-images hook.
# The hooks are only set once, and subsequent calls to this function will not modify hooks again.
extend_behave_hooks()
