Version History
===============================================================================

Version: 3.3.0
-------------------------------------------------------------------------------

ENHANCEMENTS:

* Added compatibility with latest behave0 versions while maintaining backward compatibility with behave 1.2.6.
* Improved ModelRunner.run_hook wrapper to handle the signature change in behave 1.3.0 where hook_target parameter replaced context parameter.
* Enhanced error handling throughout the library:
  
  - User-facing functions now raise ValueError with descriptive messages instead of silently failing when called with None context
  - Hook functions log detailed error messages to help diagnose behave version compatibility issues
  - Internal utility functions log warnings for better debugging while gracefully handling edge cases

* Implemented safe context attribute access using getattr() to prevent AttributeError exceptions.
* Added comprehensive context extraction logic to properly handle both behave 1.2.6 and 1.3.0 hook signatures.

Version: 3.2.2
-------------------------------------------------------------------------------

ENHANCEMENTS:

* Added comprehensive testing workflow to validate library installation across all supported Python versions (3.8-3.13) on Ubuntu, Windows, and macOS.

Version: 3.2.1
-------------------------------------------------------------------------------

ENHANCEMENTS:

* Improvement done in the way the gallery files are copied to the output directory.
* Improvement done in before_scenario hook add robustness on the execution logic.
* Removing dependency on numpy library.


Version: 3.2.0
-------------------------------------------------------------------------------

ENHANCEMENTS:

* Improvement done to determine the step line number associated with each image in gallery.
* Improvement done in the way hooks are executed, to properly handle the case where BehaveX hooks are not initialized yet.
* Adding support for BehaveX report formatters.

Version: 3.1.1
-------------------------------------------------------------------------------

ENHANCEMENTS:

* Enabling maximizing an image, making it full screen and hiding the logs associated with the image.
* Enabling zoom in and zoom out by clicking on the image.

Version: 3.0.10
-------------------------------------------------------------------------------

FIXES:

* Fixing issue when querying for the DRY_RUN environment variable.

Version: 3.0.9
-------------------------------------------------------------------------------

FIXES:

* Avoid executing environment.py hooks when a dry run is performed.


Version: 3.0.8
-------------------------------------------------------------------------------

FIXES:

* Fixed numpy library compatibility issue related to numpy.float type.

Version: 3.0.7
-------------------------------------------------------------------------------

FIXES:

* Fixed issue related to the image attachments conditions, as ON_FAILURE option was replaced by ONLY_ON_FAILURE.

Version: 3.0.6
-------------------------------------------------------------------------------

* Updating license information

Version: 3.0.5
-------------------------------------------------------------------------------

* First public version of behavex-images library
