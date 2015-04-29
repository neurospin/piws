#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import nibabel
import os
import numpy
import json

# Cubicweb import
from cubicweb.view import View
from cubicweb.web.views.ajaxcontroller import ajaxfunc


###############################################################################
# BrainBrowser
###############################################################################

class ImageViewer(View):
    """ Create an image viewer.
    """
    __regid__ = "brainbrowser-image-viewer"
    paginable = False
    div_id = "brainbrowser-simple"

    def __init__(self, *args, **kwargs):
        """ Initialize the ImageViewer class.

        If you want to construct the viewer manually in your view pass the
        parent view in the 'parent_view' attribute.
        """
        super(ImageViewer, self).__init__(*args, **kwargs)
        if "parent_view" in kwargs:
            self._cw = kwargs["parent_view"]._cw
            self.w = kwargs["parent_view"].w

    def call(self, imagefile=None, ajaxcallback="get_brainbrowser_image",
             **kwargs):
        """ Method that will create a simple BrainBrowser image viewer.

        Parameters
        ----------
        imagefile: str (mandatory)
            the path to the path that will be rendered.
        ajaxcallback: @func (optional, default 'get_brainbrowser_image')
            a function that will be called by BrainBrowser to load
            the image data to display: do not foget the decorator @ajaxfunc.
        """
        # Get the parameters
        imagefile = imagefile or self._cw.form.get("imagefile", "")
        ajaxcallback = ajaxcallback or self._cw.form.get("ajaxcallback", "")

        # Get the path to the in progress resource
        wait_image_url = self._cw.data_url("images/please_wait.gif")

        # Add css resources
        self._cw.add_css("brainbrowser-2.3.0/css/ui-darkness/"
                         "jquery-ui-1.8.10.custom.css")
        self._cw.add_css("brainbrowser-2.3.0/css/common.css")
        self._cw.add_css("volume-viewer.css")

        # Add js resources
        self._cw.add_js("brainbrowser-2.3.0/src/jquery-1.6.4.min.js")
        self._cw.add_js("brainbrowser-2.3.0/src/"
                        "jquery-ui-1.8.10.custom.min.js")
        self._cw.add_js("brainbrowser-2.3.0/src/ui.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/"
                        "brainbrowser.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/core/"
                        "tree-store.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/lib/"
                        "config.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/lib/"
                        "utils.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/lib/"
                        "events.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/lib/"
                        "loader.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/lib/"
                        "color-map.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/"
                        "volume-viewer.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/"
                        "volume-viewer/lib/display.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/"
                        "volume-viewer/lib/panel.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/"
                        "volume-viewer/lib/utils.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/"
                        "volume-viewer/modules/loading.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/"
                        "volume-viewer/modules/rendering.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/"
                        "volume-viewer/volume-loaders/overlay.js")
        self._cw.add_js("brainbrowser-2.3.0/src/brainbrowser/"
                        "volume-viewer/volume-loaders/minc.js")
        self._cw.add_js("image_viewer.js")

        # Set the brainbrowser viewer navigation tools
        html = self.build_brainbrowser_tools()

        # Create a div for the in progress resource
        html += ("<div id='loading' style='display:none' align='center'>"
                 "<img src='{0}'/></div>".format(wait_image_url))

        # Build a brainborwser banner with tools
        html += self.build_brainbrowser_banner()

        # Set brainbrowser colormaps
        html += self.build_color_maps()

        # Set the cw brainbrowser image loader
        html += self.build_cw_loader(imagefile, ajaxcallback)

        # Creat the corresponding html page
        self.w(unicode(html))

    def build_cw_loader(self, imagefile, ajaxcallback):
        """ Define the script that will load the image in BrainBrowser
        using CubicWeb ajax callback.

        Parameters
        ----------
        imagefile: str (mandatory)
            the path to the path that will be rendered.
        ajaxcallback: @func (optional, default 'get_brainbrowser_image')
            a function that will be called by BrainBrowser to load
            the image data to display: do not foget the decorator @ajaxfunc.

        Returns
        -------
        html: str
            the loader definition.
        """
        # Add javascript
        html = "<script type='text/javascript'>"
        html += "$(document).ready(function() {"

        # Display wait message
        html += "$('#loading').show();"

        # Execute the ajax callback
        html += "var postData = {};"
        html += "postData.imagefile = '{0}';".format(imagefile)
        html += "var post = $.ajax({"
        html += "url: '{0}ajax?fname={1}',".format(self._cw.base_url(),
                                                   ajaxcallback)
        html += "type: 'POST',"
        html += "data: postData"
        html += "});"

        # The ajax callback is done, get the result set
        html += "post.done(function(p){"
        html += "$('#loading').hide();"
        html += "var data = p.data;"
        html += "var header_text = p.header;"

        # And create the appropriate viewer
        html += "var VolumeViewer = BrainBrowser.VolumeViewer;"
        html += ("VolumeViewer.volume_loaders.nifti = "
                 "function(description, callback) {")
        html += "var error_message;"
        html += "if (description.data_file) {"
        html += "BrainBrowser.parseHeader(header_text, function(header) {"
        html += "BrainBrowser.createMincVolume(header, data, callback);"
        html += "});"
        html += "error_message = header.xspace.name;"
        html += ("BrainBrowser.events.triggerEvent('error', "
                 "{ message: error_message });")
        html += "throw new Error(error_message);"
        html += "} else {"
        html += "error_message = 'Error';"
        html += ("BrainBrowser.events.triggerEvent('error', "
                 "{ message: error_message });")
        html += "throw new Error(error_message);"
        html += "}"
        html += "};"

        # Finally load the volume
        html += "var viewer = window.viewer;"
        html += "viewer.loadVolume({"
        html += "type: 'nifti',"
        html += "data_file: '{0}',".format(imagefile)
        html += "template: {"
        html += "element_id: 'volume-ui-template',"
        html += "viewer_insert_class: 'volume-viewer-display'"
        html += "}"
        html += "}, function() {"
        html += "$('.slice-display').css('display', 'inline');"
        html += "$('.volume-controls').css('width', 'auto');"
        html += "$('#loading').hide();"
        html += "$('#brainbrowser-wrapper').slideDown({duration: 600});"
        html += "});"

        # Close post
        html += "});"

        # Error when the loading failed
        html += "post.fail(function(){"
        html += "$('#loading').hide();"
        html += " alert('Error : Image buffering failed!');"
        html += "});"

        # Close function
        html += "});"

        # Close javascript
        html += "</script>"

        return html

    def build_color_maps(self):
        """ Define the BrainBrowser color-maps.

        Returns
        -------
        html: str
            the color-maps definition.
        """
        # Go through colormaps
        html = "<script>"
        html += "BrainBrowser.config.set('color_maps', ["
        baseurl = "brainbrowser-2.3.0/color-maps/"
        for name, color in [("Gray", "#FF0000"), ("Spectral", "#FFFFFF"),
                            ("Thermal", "#FFFFFF"), ("Blue", "#FFFFFF"),
                            ("Green", "#FF0000")]:
            resource = self._cw.data_url(
                os.path.join(baseurl, "{0}.txt".format(name.lower())))

            html += "{"
            html += "name: '{0}',".format(name)
            html += "url: '{0}',".format(resource)
            html += "cursor_color: '{0}'".format(color)
            html += "},"
        html += "]);"
        html += "</script>"

        return html

    def build_brainbrowser_tools(self, contrast=False, brightness=False):
        """ Define the default BrainBrowser tools.

        Parameters
        ----------
        contrast, brightness: bool (optional, default False)
            add extra controls (not recommended).

        Returns
        -------
        html: str
            the tools definition.
        """
        # Start javascript
        html = "<script id='volume-ui-template' type='x-volume-ui-template'>"

        # Define the image rendering location
        html += "<div class='volume-viewer-display'>"
        html += "</div>\n"

        # Define control tools
        html += "<div class='volume-viewer-controls volume-controls'>"

        # Define a tool to display the voxel and world coordinates
        html += "<div class='coords'>"
        html += "<div class='control-container'>"
        html += ("<div class='control-heading' "
                 "id='voxel-coordinates-heading-{{VOLID}}'>")
        html += "Voxel Coordinates:"
        html += "</div>"
        html += "<div class='voxel-coords' data-volume-id='{{VOLID}}'>"
        html += "I:<input id='voxel-i-{{VOLID}}' class='control-inputs'>"
        html += "J:<input id='voxel-j-{{VOLID}}' class='control-inputs'>"
        html += "K:<input id='voxel-k-{{VOLID}}' class='control-inputs'>"
        html += "</div>"
        html += ("<div class='control-heading' "
                 "id='world-coordinates-heading-{{VOLID}}'>")
        html += "World Coordinates:"
        html += "</div>"
        html += "<div class='world-coords' data-volume-id='{{VOLID}}'>"
        html += "X:<input id='world-x-{{VOLID}}' class='control-inputs'>"
        html += "Y:<input id='world-y-{{VOLID}}' class='control-inputs'>"
        html += "Z:<input id='world-z-{{VOLID}}' class='control-inputs'>"
        html += "</div>"
        html += "</div>"
        html += "</div>"

        # Define a tool to change the colormap
        html += "<div class='control-container'>"
        html += "<div id='color-map-{{VOLID}}'>"
        html += "<div class='control-heading'>"
        html += "<span id='color-map-heading-{{VOLID}}'>"
        html += "Color Map:"
        html += "</span>"
        html += "</div>"
        html += "</div>"

        # Define a tool to display the selected voxel intensity
        html += "<div id='intensity-value-div-{{VOLID}}'>"
        html += "<div class='control-heading'>"
        html += "<span data-volume-id='{{VOLID}}'>"
        html += "Value:"
        html += "</span>"
        html += "</div>"
        html += ("<span id='intensity-value-{{VOLID}}' "
                 "class='intensity-value'></span>")
        html += "</div>"
        html += "</div>"

        # Define a tool to threshold the image
        html += "<div class='control-container'>"
        html += "<div class='threshold-div' data-volume-id='{{VOLID}}'>"
        html += "<div class='control-heading'>"
        html += "Brightness/Contrast:"
        html += "</div>"
        html += "<div class='thresh-inputs'>"
        html += ("<input id='min-threshold-{{VOLID}}' "
                 "class='control-inputs thresh-input-left' value='0'/>")
        html += ("<input id='max-threshold-{{VOLID}}' "
                 "class='control-inputs thresh-input-right' value='65535'/>")
        html += "</div>"
        html += ("<div class='slider volume-viewer-threshold' "
                 "id='threshold-slider-{{VOLID}}'></div>")
        html += "</div>"

        # Define a complete slicer tool
        html += ("<div id='slice-series-{{VOLID}}' "
                 "class='slice-series-div' data-volume-id='{{VOLID}}'>")
        html += ("<div class='control-heading' "
                 "id='slice-series-heading-{{VOLID}}'>All slices: </div>")
        html += ("<span class='slice-series-button button' "
                 "data-axis='xspace'>Sagittal</span>")
        html += ("<span class='slice-series-button button' "
                 "data-axis='yspace'>Coronal</span>")
        html += ("<span class='slice-series-button button' "
                 "data-axis='zspace'>Transverse</span>")
        html += "</div>"
        html += "</div>"

        # Define a tool to control the image contrast
        if contrast:
            html += "<div class='control-container'>"
            html += "<div class='contrast-div' data-volume-id='{{VOLID}}'>"
            html += ("<span class='control-heading' "
                     "id='contrast-heading{{VOLID}}'>Contrast (0.0 to 2.0):"
                     "</span>")
            html += ("<input class='control-inputs' value='1.0' "
                     "id='contrast-val'/>")
            html += ("<div id='contrast-slider' "
                     "class='slider volume-viewer-contrast'></div>")
            html += "</div>"
            html += "</div>"

        # Define a tool to control the image brightness
        if brightness:
            html += "<div class='control-container'>"
            html += "<div class='brightness-div' data-volume-id='{{VOLID}}'>"
            html += ("<span class='control-heading' "
                     "id='brightness-heading{{VOLID}}'>Brightness (-1 to 1):"
                     "</span>")
            html += "<input class='control-inputs' value='0' id='brightness-val'/>"
            html += ("<div id='brightness-slider' "
                     "class='slider volume-viewer-brightness'></div>")
            html += "</div>"
            html += "</div>"

        # End controls
        html += "</div>"

        # End javascript
        html += "</script>"

        return html

    def build_brainbrowser_banner(self):
        """ Define the default BrainBrowser banner.

        Returns
        -------
        html: str
            the banner definition.
        """
        # Define a banner divs
        html = "<div id='brainbrowser-wrapper' style='display:none'>"
        html += "<div id='volume-viewer'>"
        html += "<div id='global-controls' class='volume-viewer-controls'>"

        # Define item to chang the panle size
        html += "<span class='control-heading'>Panel size:</span>"
        html += "<select id='panel-size'>"
        html += "<option value='128'>128</option>"
        html += "<option value='256' SELECTED>256</option>"
        html += "<option value='512'>512</option>"
        html += "</select>"

        # Define item to rest displayed views
        html += "<span id='sync-volumes-wrapper'>"
        html += ("<input type='checkbox' class='button' id='reset-volumes'>"
                 "<label for='reset-volumes'>Reset</label>")
        html += "</span>"

        # Define item to create a screenshot
        html += "<span id='screenshot' class='button'>Screenshot</span>"
        html += ("<div class='instructions'>Shift-click to drag. Hold ctrl "
                 "to measure distance.</div>")

        # End divs
        html += "</div>"
        html += "<div id='brainbrowser'></div>"
        html += "</div>"
        html += "</div>"

        return html


###############################################################################
# Interact with jtable js
###############################################################################

@ajaxfunc(output_type="json")
def get_brainbrowser_image(self):
    """ Get image information and buffer: formated for BrainBrowser.

    Returns
    -------
    im_info: dict
        the image infirmation and buffer.
    """
    # Get post parameters
    imagefile = self._cw.form["imagefile"]

    # Load the image
    im = nibabel.load(imagefile)
    data = im.get_data()
    header = im.get_header()

    # Change the dynamic of the image intensities
    data = numpy.cast[numpy.uint16]((data - data.min()) * 65535. / (data.max() - data.min()))

    # Format the output
    dim = header["dim"]
    order = ["xspace", "yspace", "zspace", "time"]
    if dim[0] == 3:
        header = {
            "order": order[:3],
            "xspace": {
                "start": float(header["qoffset_x"]),
                "space_length": int(dim[1]),
                "step": float(header["pixdim"][1]),
                "direction_cosines": [float(x) for x in header["srow_x"][:3]]},
            "yspace": {
                "start": float(header["qoffset_y"]),
                "space_length": int(dim[2]),
                "step": float(header["pixdim"][2]),
                "direction_cosines": [float(x) for x in header["srow_y"][:3]]},
            "zspace": {
                "start": float(header["qoffset_z"]),
                "space_length": int(dim[3]),
                "step": float(header["pixdim"][3]),
                "direction_cosines": [float(x) for x in header["srow_z"][:3]]}
        }
    else:
        raise Exception("Only 3D images are currently supported!")

    # Format the output
    im_info = {
        "header": json.dumps(header),
        "data": data.flatten().tolist()
    }

    print data.min(), data.max()

    return im_info


###############################################################################
# Update CW registery
###############################################################################

def registration_callback(vreg):
    vreg.register(get_brainbrowser_image)
    vreg.register(ImageViewer)
