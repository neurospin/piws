#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.web import component
from cubicweb.predicates import is_instance
from cubicweb.predicates import nonempty_rset
from cubicweb.predicates import anonymous_user

# Cubes import
from cubes.brainomics.views.components import BrainomicsLinksCenters
from cubes.brainomics.views.components import BrainomicsEditBox
from cubes.brainomics.views.components import BrainomicsDownloadBox


###############################################################################
# Navigation Box
###############################################################################

class NSNavigationtBox(component.CtxComponent):
    """ Display a box containing navigation shortcuts.
    """
    __regid__ = "nav_box"
    context = "left"
    title = _("Navigation")
    order = 0

    def render_body(self, w):
        """ Create the diifferent item of the navigation box
        """
        # Subjects
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        href = self._cw.build_url(rql="Any S Where S is Subject")
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Subjects</a>')
        w(u'</div></div><br/>')

        # Exams
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        href = self._cw.build_url(rql="Any A Where A is Assessment")
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Exams</a>')
        w(u'</div></div><br/>')

        # Scan
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        href = self._cw.build_url(rql="Any S Where S is Scan")
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Images</a>')
        w(u'</div></div><br/>')

        # ProcessingRun
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        href = self._cw.build_url(rql="Any PR Where PR is ProcessingRun")
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Processings</a>')
        w(u'</div></div><br/>')

        # QuestionnaireRun
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        ajaxcallback = "get_questionnaires_data"
        rql_labels = ("DISTINCT Any T ORDERBY T WHERE A is Assessment, "
                      "A timepoint T")
        href = self._cw.build_url(
            "view", vid="jtable-table",
            rql_labels=rql_labels, ajaxcallback=ajaxcallback,
            title="All Questionnaires", elts_to_sort=["ID"])
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Questionaires</a>')
        w(u'</div></div><br/>')

        # GenomicMeasures
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        href = self._cw.build_url(rql="Any GM Where GM is GenomicMeasure")
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Genomic measures</a>')
        w(u'</div></div><br/>')


###############################################################################
# Statistic boxes
###############################################################################

class NSSubjectStatistics(component.CtxComponent):
    """ Display a box containing links to statistics on the cw entities.
    """
    __regid__ = "subject_statistics"
    context = "left"
    title = _("Statistics")
    order = 1
    __select__ = is_instance("Subject")

    def render_body(self, w, **kwargs):
        """ Method to create the statistic box content.
        """
        # Create a view to see the subject gender repartition in the db
        href = self._cw.build_url("view", vid="highcharts-basic-pie",
                                  rql="Any G WHERE S is Subject, S gender G",
                                  title="Subject genders")
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Subject gender repartition</a>')
        w(u'</div></div><br/>')

        # Create a view to see the subject handedness repartition in the db
        href = self._cw.build_url(
            "view", vid="highcharts-basic-pie",
            rql="Any H WHERE S is Subject, S handedness H",
            title="Subject handednesses")
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Subject handedness repartition</a>')
        w(u'</div></div><br/>')

        # Create a view to see the db subject status
        href = self._cw.build_url(
            "view", vid="highcharts-relation-summary-view",
            rql="Any S WHERE S is Subject", title="Insertion status",
            relation="concerned_by", subject_attr="identifier",
            object_attr="timepoint")
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Insertion status</a>')
        w(u'</div></div><br/>')


class NSAssessmentStatistics(component.CtxComponent):
    """ Display a box containing links to statistics on the cw entities.
    """
    __regid__ = "assessment_statistics"
    context = "left"
    title = _("Statistics")
    order = 1
    __select__ = is_instance("Assessment")

    def render_body(self, w, **kwargs):
        """ Method to create the statistic box content.
        """
        # Create a view to see the db acquistion status
        href = self._cw.build_url(
            "view", vid="highcharts-relation-summary-view",
            rql="Any A WHERE A is Assessment", title="Acquisition status",
            relation="uses", subject_attr="timepoint", object_attr="label")
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Acquisition status</a>')
        w(u'</div></div><br/>')

        # Create a view to see the db processing status
        href = self._cw.build_url(
            "view", vid="highcharts-relation-summary-view",
            rql="Any A WHERE A is Assessment", title="Processing status",
            relation="related_processing", subject_attr="timepoint",
            object_attr="tool")
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Processing status</a>')
        w(u'</div></div><br/>')

        # Create a view to see the db subject age distribution
        href = self._cw.build_url(
            "view", vid="highcharts-basic-plot",
            rql="Any A WHERE X is Assessment, X age_of_subject A",
            title="Age distribution", is_hist=True)
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Age distribution</a>')
        w(u'</div></div><br/>')


def registration_callback(vreg):

    # Update components
    vreg.register(NSNavigationtBox)
    vreg.register(NSSubjectStatistics)
    vreg.register(NSAssessmentStatistics)
    vreg.unregister(BrainomicsLinksCenters)
    vreg.unregister(BrainomicsEditBox)
    vreg.unregister(BrainomicsDownloadBox)
