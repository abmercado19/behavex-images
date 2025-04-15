/**
 * Lightbox v2.7.1
 * by Lokesh Dhakar - http://lokeshdhakar.com/projects/lightbox2/
 *
 * @license http://creativecommons.org/licenses/by/2.5/
 * - Free for use in both personal and commercial projects
 * - Attribution requires leaving author name, author link, and the license info intact
 */

(function() {
  // Use local alias
  var $ = jQuery;

  var LightboxOptions = (function() {
    function LightboxOptions() {
      this.fadeDuration                = 1;
      this.fitImagesInViewport         = true;
      this.resizeDuration              = 1;
      this.positionFromTop             = 5;
      this.showImageNumberLabel        = true;
      this.alwaysShowNavOnTouchDevices = false;
      this.wrapAround                  = true;
    }

    // Change to localize to non-english language
    LightboxOptions.prototype.albumLabel = function(curImageNum, albumSize) {
      return "Image " + curImageNum + " of " + albumSize;
    };

    return LightboxOptions;
  })();


  var Lightbox = (function() {
    function Lightbox(options) {
      this.options           = options;
      this.album             = [];
      this.currentImageIndex = void 0;
      this.init();
    }

    Lightbox.prototype.init = function() {
      this.enable();
      this.build();
    };

    // Loop through anchors and areamaps looking for either data-lightbox attributes or rel attributes
    // that contain 'lightbox'. When these are clicked, start lightbox.
    Lightbox.prototype.enable = function() {
      var self = this;
      $('body').on('click', 'a[rel^=lightbox], area[rel^=lightbox], a[data-lightbox], area[data-lightbox]', function(event) {
        self.start($(event.currentTarget));
        return false;
      });
    };

    // Build html for the lightbox and the overlay.
    // Attach event handlers to the new DOM elements. click click click
    Lightbox.prototype.build = function() {
      var self = this;
      $("<div id='lightboxOverlay' class='lightboxOverlay'></div><div id='lightbox' class='lightbox'><div class='lb-outerContainer'><div class='lb-container'><img class='lb-image' src='' /><div class='lb-nav'><a class='lb-prev' href='' ></a><div class='lb-middle'></div><a class='lb-next' href='' ></a></div><div class='lb-loader'><a class='lb-cancel'></a></div></div></div><div class='lb-dataContainer'><div class='lb-data'><div class='lb-details'><span class='lb-caption'></span><span class='lb-number'></span></div><div class='lb-closeContainer'><a class='lb-close'></a></div></div></div></div>").appendTo($('body'));

      // Cache jQuery objects
      this.$lightbox       = $('#lightbox');
      this.$overlay        = $('#lightboxOverlay');
      this.$outerContainer = this.$lightbox.find('.lb-outerContainer');
      this.$container      = this.$lightbox.find('.lb-container');

      // Store css values for future lookup
      this.containerTopPadding = parseInt(this.$container.css('padding-top'), 10);
      this.containerRightPadding = parseInt(this.$container.css('padding-right'), 10);
      this.containerBottomPadding = parseInt(this.$container.css('padding-bottom'), 10);
      this.containerLeftPadding = parseInt(this.$container.css('padding-left'), 10);

      // Attach event handlers to the newly minted DOM elements
      this.$overlay.hide().on('click', function() {
        self.end();
        return false;
      });

      this.$lightbox.hide().on('click', function(event) {
        if ($(event.target).attr('id') === 'lightbox') {
          self.end();
        }
        return false;
      });

      this.$outerContainer.on('click', function(event) {
        if ($(event.target).attr('id') === 'lightbox') {
          self.end();
        }
        return false;
      });

      // Add wheel event handler for scrolling in maximized view
      this.$lightbox.on('wheel', function(event) {
        if (self.isMaximized) {
          var container = self.$lightbox.find('.lb-container.lb-full-width')[0];
          if (container) {
            container.scrollTop += event.originalEvent.deltaY;
            event.preventDefault();
          }
        }
      });

      this.$lightbox.find('.lb-prev').on('click', function() {
        if (self.currentImageIndex === 0) {
          self.changeImage(self.album.length - 1);
        } else {
          self.changeImage(self.currentImageIndex - 1);
        }
        return false;
      });

      this.$lightbox.find('.lb-next').on('click', function() {
        if (self.currentImageIndex === self.album.length - 1) {
          self.changeImage(0);
        } else {
          self.changeImage(self.currentImageIndex + 1);
        }
        return false;
      });

      this.$lightbox.find('.lb-loader, .lb-close').on('click', function() {
        self.end();
        return false;
      });

      // Add back button handler
      this.$lightbox.find('.lb-back').on('click', function() {
        if (self.isMaximized) {
          // If maximized, just minimize
          self.toggleMaximize();
        } else {
          // If not maximized, close lightbox to return to list
          self.end();
        }
        return false;
      });

      // Update zoom button handlers
      this.$lightbox.find('.lb-zoom-in').on('click', function() {
        if (!self.isMaximized) {
          self.toggleMaximize();
        }
        return false;
      });

      this.$lightbox.find('.lb-zoom-out').on('click', function() {
        if (self.isMaximized) {
          self.toggleMaximize();
        }
        return false;
      });

      // Add middle area click handler
      this.$lightbox.find('.lb-middle').on('click', function() {
        self.toggleMaximize();
        return false;
      });
    };

    // Add maximize state tracking
    Lightbox.prototype.isMaximized = false;

    // Toggle maximize state
    Lightbox.prototype.toggleMaximize = function() {
      this.isMaximized = !this.isMaximized;
      this.$lightbox.toggleClass('maximized');
      
      var $image = this.$lightbox.find('.lb-image');
      var $container = this.$lightbox.find('.lb-container');
      var $outerContainer = this.$lightbox.find('.lb-outerContainer');
      
      var self = this;
      
      if (this.isMaximized) {
        // Add full-width class to relevant elements
        $outerContainer.addClass('lb-full-width');
        $container.addClass('lb-full-width');
        $image.addClass('lb-full-width');
        
        // Store original dimensions before maximizing
        $image.data('original-width', $image.width());
        $image.data('original-height', $image.height());
        
        // Calculate maximized dimensions
        var windowWidth = $(window).width();
        var windowHeight = $(window).height();
        var originalWidth = $image.width();
        var originalHeight = $image.height();
        var ratio = Math.min(windowWidth / originalWidth, windowHeight / originalHeight);
        var newWidth = originalWidth * ratio;
        var newHeight = originalHeight * ratio;
        
        $image.width(newWidth);
        $image.height(newHeight);
        
        this.$lightbox.find('.lb-dataContainer').slideUp(200);
        
        // Update button visibility
        this.$lightbox.find('.lb-zoom-in').hide();
        this.$lightbox.find('.lb-zoom-out').show();
      } else {
        // Remove full-width class from relevant elements
        $outerContainer.removeClass('lb-full-width');
        $container.removeClass('lb-full-width');
        $image.removeClass('lb-full-width');
        
        // Get the stored original dimensions
        var originalWidth = $image.data('original-width');
        var originalHeight = $image.data('original-height');
        
        // Calculate container width
        var containerWidth = $(window).width();
        
        // Calculate new dimensions to fit container while maintaining aspect ratio
        var maxWidth = containerWidth * 0.6; // Use 60% of container width for image
        var ratio = Math.min(maxWidth / originalWidth, 1);
        var newWidth = originalWidth * ratio;
        var newHeight = originalHeight * ratio;
        
        // Restore dimensions with container constraints
        $image.width(newWidth);
        $image.height(newHeight);
        
        this.$lightbox.find('.lb-dataContainer').slideDown(200);
        
        // Update button visibility
        this.$lightbox.find('.lb-zoom-in').show();
        this.$lightbox.find('.lb-zoom-out').hide();
      }
      
      this.sizeContainer($image.width(), $image.height());
    };

    // Show overlay and lightbox. If the image is part of a set, add siblings to album array.
    Lightbox.prototype.start = function($link) {
      var self    = this;
      var $window = $(window);

      $window.on('resize', $.proxy(this.sizeOverlay, this));

      $('select, object, embed').css({
        visibility: "hidden"
      });

      this.sizeOverlay();

      this.album = [];
      var imageNumber = 0;

      function addToAlbum($link) {
        self.album.push({
          link: $link.attr('href'),
          title: $link.attr('data-title') || $link.attr('title')
        });
      }

      // Support both data-lightbox attribute and rel attribute implementations
      var dataLightboxValue = $link.attr('data-lightbox');
      var $links;

      if (dataLightboxValue) {
        $links = $($link.prop("tagName") + '[data-lightbox="' + dataLightboxValue + '"]');
        for (var i = 0; i < $links.length; i = ++i) {
          addToAlbum($($links[i]));
          if ($links[i] === $link[0]) {
            imageNumber = i;
          }
        }
      } else {
        if ($link.attr('rel') === 'lightbox') {
          // If image is not part of a set
          addToAlbum($link);
        } else {
          // If image is part of a set
          $links = $($link.prop("tagName") + '[rel="' + $link.attr('rel') + '"]');
          for (var j = 0; j < $links.length; j = ++j) {
            addToAlbum($($links[j]));
            if ($links[j] === $link[0]) {
              imageNumber = j;
            }
          }
        }
      }

      // Position Lightbox
      var top  = $window.scrollTop() + this.options.positionFromTop;
      var left = $window.scrollLeft();
      this.$lightbox.css({
        top: top + 'px',
        left: left + 'px'
      }).fadeIn(this.options.fadeDuration);

      this.changeImage(imageNumber);
    };

    // Hide most UI elements in preparation for the animated resizing of the lightbox.
    Lightbox.prototype.changeImage = function(imageNumber) {
      var self = this;

      this.disableKeyboardNav();
      var $image = this.$lightbox.find('.lb-image');

      this.$overlay.fadeIn(this.options.fadeDuration);

      $('.lb-loader').fadeIn('slow');
      this.$lightbox.find('.lb-image, .lb-nav, .lb-prev, .lb-next, .lb-dataContainer, .lb-numbers, .lb-caption').hide();

      this.$outerContainer.addClass('animating');

      // When image to show is preloaded, we send the width and height to sizeContainer()
      var preloader = new Image();
      preloader.onload = function() {
        var $preloader, imageHeight, imageWidth, maxImageHeight, maxImageWidth, windowHeight, windowWidth;
        $image.attr('src', self.album[imageNumber].link);

        $preloader = $(preloader);

        // Store original dimensions
        var originalWidth = preloader.width;
        var originalHeight = preloader.height;

        if (self.isMaximized) {
          // In maximized mode, calculate dimensions to fit viewport
          windowWidth = $(window).width();
          windowHeight = $(window).height();
          
          // Calculate scaling ratio to fit viewport while maintaining aspect ratio
          var ratio = Math.min(windowWidth / originalWidth, windowHeight / originalHeight);
          imageWidth = originalWidth * ratio;
          imageHeight = originalHeight * ratio;
        } else {
          // Normal mode - use original dimensions
          imageWidth = originalWidth;
          imageHeight = originalHeight;

          if (self.options.fitImagesInViewport) {
            windowWidth = $(window).width();
            windowHeight = $(window).height();
            maxImageWidth = windowWidth - self.containerLeftPadding - self.containerRightPadding - 20;
            maxImageHeight = windowHeight - self.containerTopPadding - self.containerBottomPadding - 120;

            if ((originalWidth > maxImageWidth) || (originalHeight > maxImageHeight)) {
              if ((originalWidth / maxImageWidth) > (originalHeight / maxImageHeight)) {
                imageWidth = maxImageWidth;
                imageHeight = parseInt(originalHeight / (originalWidth / imageWidth), 10);
              } else {
                imageHeight = maxImageHeight;
                imageWidth = parseInt(originalWidth / (originalHeight / imageHeight), 10);
              }
            }
          }
        }

        $image.width(imageWidth);
        $image.height(imageHeight);
        self.sizeContainer(imageWidth, imageHeight);
      };

      preloader.src = this.album[imageNumber].link;
      this.currentImageIndex = imageNumber;
    };

    // Stretch overlay to fit the viewport
    Lightbox.prototype.sizeOverlay = function() {
      this.$overlay
        //.width($(window).width() * 2)
        .height($(document).height());
    };

    // Animate the size of the lightbox to fit the image we are showing
    Lightbox.prototype.sizeContainer = function(imageWidth, imageHeight) {
      var self = this;
      var containerWidth = $(window).width();

      var oldWidth = this.$outerContainer.outerWidth();
      var oldHeight = this.$outerContainer.outerHeight();
      var newWidth = imageWidth + this.containerLeftPadding + this.containerRightPadding;
      var newHeight = imageHeight + this.containerTopPadding + this.containerBottomPadding;

      function postResize() {
        if (self.isMaximized) {
          // When maximized, use full viewport
          self.$lightbox.find('.lb-container').width(imageWidth).height(imageHeight);
          self.$lightbox.find('.lb-outerContainer').width(imageWidth).height(imageHeight);
          
          // Hide UI elements
          self.$lightbox.find('.lb-dataContainer').hide();
          self.$lightbox.find('.lb-nav').hide();
          
          // Update overlay and lightbox dimensions
          self.$overlay.width(containerWidth);
          self.$lightbox.width(containerWidth);
        } else {
          // Normal mode - ensure width doesn't exceed container and utilize full width
          var imageContainerWidth = Math.min(newWidth, containerWidth * 0.6); // 60% for image
          var dataContainerWidth = containerWidth - imageContainerWidth - 40; // Remaining space minus padding
          
          self.$lightbox.find('.lb-outerContainer').width(imageContainerWidth);
          self.$lightbox.find('.lb-dataContainer')
            .width(dataContainerWidth)
            .css('float', 'right');
          
          self.$lightbox.find('.lb-prevLink').height(newHeight);
          self.$lightbox.find('.lb-nextLink').height(newHeight);

          // Set lightbox to full container width
          self.$overlay.width(containerWidth);
          self.$lightbox.width(containerWidth);
        }
        self.showImage();
      }

      this.$outerContainer.animate({
        width: newWidth,
        height: newHeight
      }, this.options.resizeDuration, 'swing', function() {
        postResize();
      });
    };

    // Display the image and it's details and begin preload neighboring images.
    Lightbox.prototype.showImage = function() {
      this.$lightbox.find('.lb-loader').hide();
      this.$lightbox.find('.lb-image').fadeIn('slow');

      this.updateNav();
      this.updateDetails();
      this.preloadNeighboringImages();
      this.enableKeyboardNav();
    };

    // Display previous and next navigation if appropriate.
    Lightbox.prototype.updateNav = function() {
      // Check to see if the browser supports touch events. If so, we take the conservative approach
      // and assume that mouse hover events are not supported and always show prev/next navigation
      // arrows in image sets.
      var alwaysShowNav = false;
      try {
        document.createEvent("TouchEvent");
        alwaysShowNav = (this.options.alwaysShowNavOnTouchDevices)? true: false;
      } catch (e) {}

      this.$lightbox.find('.lb-nav').show();

      if (this.album.length > 1) {
        if (this.options.wrapAround) {
          if (alwaysShowNav) {
            this.$lightbox.find('.lb-prev, .lb-next').css('opacity', '1');
          }
          this.$lightbox.find('.lb-prev, .lb-next').show();
        } else {
          if (this.currentImageIndex > 0) {
            this.$lightbox.find('.lb-prev').show();
            if (alwaysShowNav) {
              this.$lightbox.find('.lb-prev').css('opacity', '1');
            }
          }
          if (this.currentImageIndex < this.album.length - 1) {
            this.$lightbox.find('.lb-next').show();
            if (alwaysShowNav) {
              this.$lightbox.find('.lb-next').css('opacity', '1');
            }
          }
        }
      }
    };

    // Display caption, image number, and closing button.
    Lightbox.prototype.updateDetails = function() {
      var self = this;

      // Enable anchor clicks in the injected caption html.
      // Thanks Nate Wright for the fix. @https://github.com/NateWr
      //while(this.currentImageIndex == null);
      if(this.currentImageIndex != null)
      {
        if (typeof this.album[this.currentImageIndex].title !== 'undefined' && this.album[this.currentImageIndex].title !== "") {
          this.$lightbox.find('.lb-caption')
            .html(this.album[this.currentImageIndex].title)
            .fadeIn('fast')
            .find('a').on('click', function(event){
              location.href = $(this).attr('href');
            });
        }
      }
      if (this.album.length > 1 && this.options.showImageNumberLabel) {
        this.$lightbox.find('.lb-number').text(this.options.albumLabel(this.currentImageIndex + 1, this.album.length)).fadeIn('fast');
      } else {
        this.$lightbox.find('.lb-number').hide();
      }

      this.$outerContainer.removeClass('animating');

      this.$lightbox.find('.lb-dataContainer').fadeIn(this.options.resizeDuration, function() {
        return self.sizeOverlay();
      });
    };

    // Preload previous and next images in set.
    Lightbox.prototype.preloadNeighboringImages = function() {
      if (this.album.length > this.currentImageIndex + 1) {
        var preloadNext = new Image();
        preloadNext.src = this.album[this.currentImageIndex + 1].link;
      }
      if (this.currentImageIndex > 0) {
        var preloadPrev = new Image();
        preloadPrev.src = this.album[this.currentImageIndex - 1].link;
      }
    };

    Lightbox.prototype.enableKeyboardNav = function() {
      $(document).on('keyup.keyboard', $.proxy(this.keyboardAction, this));
    };

    Lightbox.prototype.disableKeyboardNav = function() {
      $(document).off('.keyboard');
    };

    Lightbox.prototype.keyboardAction = function(event) {
      var KEYCODE_ESC        = 27;
      var KEYCODE_LEFTARROW  = 37;
      var KEYCODE_RIGHTARROW = 39;

      var keycode = event.keyCode;
      var key     = String.fromCharCode(keycode).toLowerCase();
      if (keycode === KEYCODE_ESC || key.match(/x|o|c/)) {
        this.end();
      } else if (key === 'p' || keycode === KEYCODE_LEFTARROW) {
        if (this.currentImageIndex !== 0) {
          this.changeImage(this.currentImageIndex - 1);
        } else if (this.options.wrapAround && this.album.length > 1) {
          this.changeImage(this.album.length - 1);
        }
      } else if (key === 'n' || keycode === KEYCODE_RIGHTARROW) {
        if (this.currentImageIndex !== this.album.length - 1) {
          this.changeImage(this.currentImageIndex + 1);
        } else if (this.options.wrapAround && this.album.length > 1) {
          this.changeImage(0);
        }
      }
    };

    // Closing time. :-(
    Lightbox.prototype.end = function() {
      this.disableKeyboardNav();
      $(window).off("resize", this.sizeOverlay);
      this.$lightbox.fadeOut(this.options.fadeDuration);
      this.$overlay.fadeOut(this.options.fadeDuration);
      $('select, object, embed').css({
        visibility: "visible"
      });
    };

    return Lightbox;

  })();

  $(function() {
    var options  = new LightboxOptions();
    var lightbox = new Lightbox(options);
  });

}).call(this);

if(window.addEventListener){
  window.addEventListener("keydown", function(e){
    // space and arrow keys
    if([32, 37, 38, 39, 40].indexOf(e.keyCode) > -1) {
        e.preventDefault();
    }
}, false);}
