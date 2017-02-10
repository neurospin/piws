##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


# Add again rql_upload style sheet since the boostrap cube reset everything
STYLESHEETS += [
    data('fullcalendar-2.0.1/fullcalendar.css'),
    data('cubes.piws.css'),
    data('cubes.rql_upload.css'),
]

STYLESHEETS_PRINT += [
    data('fullcalendar-2.0.1/fullcalendar.print.css')
]


JAVASCRIPTS += [
    data('cubes.piws.js'),
    data('time_left.js'),
    data('fullcalendar-2.0.1/lib/moment.min.js'),
    data('fullcalendar-2.0.1/lib/jquery-ui.custom.min.js'),
    data('fullcalendar-2.0.1/fullcalendar.min.js'),
]
