##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import json
from packaging import version

# Cubicweb import
import cubicweb
cw_version = version.parse(cubicweb.__version__)
if cw_version >= version.parse("3.21.0"):
    from cubicweb import _

from cubicweb.web import component
from cubicweb.view import EntityView
from cubicweb.predicates import is_instance
from cubicweb.predicates import nonempty_rset
from cubicweb.predicates import anonymous_user
from cubicweb.predicates import one_line_rset
from cubicweb.predicates import match_view
from cubicweb.predicates import match_kwargs
from cubicweb.predicates import authenticated_user
from cubicweb.web.views.basecomponents import AnonUserStatusLink
from cubicweb.web.views.basecomponents import ApplLogo
from cubicweb.web.views.basecomponents import HeaderComponent
from cubicweb.web.views.baseviews import MetaDataView
from cubicweb.web.views.ibreadcrumbs import BreadCrumbEntityVComponent
from cubicweb.web.views.ibreadcrumbs import BreadCrumbLinkToVComponent
from cubicweb.web.views.ibreadcrumbs import BreadCrumbAnyRSetVComponent
from cubicweb.web.views.ibreadcrumbs import BreadCrumbETypeVComponent
from logilab.common.decorators import monkeypatch

# Cubes import
from cubes.bootstrap.views.basecomponents import BSAuthenticatedUserStatus
from cubicweb.web.views.boxes import EditBox
from cubes.rql_upload.views.components import CWUploadBox
from cubes.rql_upload.views.utils import load_forms



##############################################################################
# Time left
##############################################################################


class TimeLeft(HeaderComponent):
    """ Build a time left before session expiration display in the header.
    """
    __regid__ = "time-left"
    __select__ = authenticated_user()
    context = u"header-right"
    order = 3

    def render(self, w):

        # Get the expiration delay
        expiration_delay = self._cw.vreg.config.get(
            "apache-cleanup-session-time")
        if expiration_delay is None:
            expiration_delay = self._cw.vreg.config.get(
                "cleanup-session-time")
        if expiration_delay is None:
            return

        # Define the expiration delay div
        w(u'<script>var cookie_name = "{0}clock";</script>'.format(
            self._cw.session.sessionid))
        w(u'<script>var expiration_time = {0};</script>'.format(
            expiration_delay * 1000))
        w(u'Auto logout in: <b id="timeh"></b>:<b id="timem"></b>:'
           '<b id="times"></b>')


###############################################################################
# Navigation Box
###############################################################################

class PIWSAuthenticatedUserStatus(BSAuthenticatedUserStatus):
    """
    Overrride bootstrap user-status component.
    In all-in-one.conf:
    If show_user_status=no : display nothing.
    If show_user_status=yes and enable-apache-logout=no: display the default
    bootstrap cube component.
    If show_user_status=yes and enable-apache-logout=yes: display a logout
    button next to the search field.
    If show_user_status=yes and enable-apache-logout=no and
    apache-cleanup-session-time is not empty: raise an error.
    """
    def render(self, w):
        config = self._cw.vreg.config
        if config.get("show_user_status"):
            if config.get("enable-apache-logout"):
                w(u"<a href='{0}' class='button'>Logout</a>".format(
                    self._cw.base_url() + 'logout'))
            else:
                super(PIWSAuthenticatedUserStatus, self).render(w)
        else:
            w(u"")


class PIWSNavigationtBox(component.CtxComponent):
    """ Display a box containing navigation shortcuts.

    To add documentation to the 'All Questionnaires' documentation main button,
    add a 'All Questionnaires.rst' file in instance all-in-one
    'documentation_folder' parameter configuration file.

    Set the 'display_assessment' to False to remove the 'Assessments'
    button.

    Set the 'display_metagen' to False to remove the 'MetaGen' button.

    Set the 'display_scan' to False to remove the 'Scans' button.

    Set the 'display_genomic' to False to remove the 'Genomic' button.

    Set the 'display_score' to False to remove the 'Quality Scores' button.

    Set the 'display_study' to True to display the 'Study' tab.
    """
    __regid__ = "nav_box"
    context = "left"
    title = _("Navigation")
    order = 0
    display_assessment = True
    display_metagen = True
    display_scan = True
    display_genomic = True
    display_study = False
    display_score = True
    display_history = True
    auto_disable_qc = False

    def render_body(self, w):
        """ Create the different item of the navigation box.
        """
        # Study
        studies = []
        if self.display_study:

            # Request all the available studies
            studies = [row[0] for row in self._cw.execute(
                "DISTINCT Any SN ORDERBY SN Where S is Study, S name SN")]

            # Display a study selection tab bar
            w(u'<ul class="nav nav-tabs piws-nav">')
            w(u'<li class="active"><a href="#studytab1">ALL</a></li>')
            for i, study in enumerate(studies, start=2):
              w(u'<li><a href="#studytab{0}">{1}</a></li>'.format(i, study))
            w(u'</ul>')

            # Add a script to manage the tab bar selection
            w(u'<script>')
            w(u'if (!("name" in window)) {')
            w(u'window.name = "studytab1";')
            w(u'}')
            w(u'$(document).ready(function(){')
            w(u'$(".piws-nav a").each(function(){')
            w(u'if ($(this).attr("href") == window.name) {')
            w(u'$(this).tab("show");')
            w(u'}')
            w(u'});')
            w(u'$(".piws-nav a").click(function(){')
            w(u'$(this).tab("show");')
            w(u'window.name = $(this).attr("href");')
            w(u'});')
            w(u'});')
            w(u'</script>')

        # Study navigation
        w(u'<div class="tab-content">')
        w(u'<div id="studytab1" class="tab-pane fade in active">')
        self.study_nav(w, study=None)
        w(u'</div>')
        for i, study in enumerate(studies, start=2):
            w(u'<div id="studytab{0}" class="tab-pane fade">'.format(i))
            self.study_nav(w, study=study)
            w(u'</div>')
        w(u'</div>')

    def study_nav(self, w, study=None):
        """ Create the different item of the study navigation box.
        """

        # Subjects
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        rql = "Any S Where S is Subject"
        if study is not None:
            rql += ", S study ST, ST name '{0}'".format(study)
        href = self._cw.build_url(rql=rql)
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Subjects</a>')
        w(u'</div></div><br/>')

        # Assessments
        if self.display_assessment:
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            rql = "Any A Where A is Assessment"
            if study is not None:
                rql += ", A study ST, ST name '{0}'".format(study)
            href = self._cw.build_url(rql=rql)
            w(u'<a class="btn btn-primary" href="{0}">'.format(href))
            w(u'Assessments</a>')
            w(u'</div></div><br/>')

        # Scan
        if self.display_scan:
            rql = "Any S Where S is Scan"
            if study is not None:
                rql += ", S study ST, ST name '{0}'".format(study)
            # > disable QC buttons
            if self.auto_disable_qc:
                rql_scores = ("DISTINCT Any T " + rql[5:] +
                              ", S type T, S score_values V")
                rset = self._cw.execute(rql_scores)
                active_types = set(row[0] for row in rset)
            # > build navigation
            href = self._cw.build_url(rql=rql)
            rql_types = "DISTINCT Any T ORDERBY T " + rql[5:] + ", S type T"
            rset = self._cw.execute(rql_types)
            types = [line[0] for line in rset.rows]
            if len(types) > 0:
                # > main button
                w(u'<div class="btn-toolbar">')
                w(u'<div class="btn-group btn-group-justified">')
                w(u'<a class="btn btn-info"'
                   'data-toggle="collapse" data-target="#scans{0}" '
                   'style="width:90%">'.format(study))
                w(u'Scans</a>')
                w(u'<a class="btn btn-primary" href="{0}" '
                   'style="width:10%">'.format(href))
                w(u'&#9735;</a>')
                w(u'</div></div>')
                # > typed buttons container
                w(u'<div id="scans{0}" class="collapse">'.format(study))
                w(u'<div class="panel-body">')
                w(u'<hr>')
                # > typed buttons
                for ptype in types:
                    typed_rql = rql + ", S type '{0}'".format(ptype)
                    href = self._cw.build_url(rql=typed_rql)
                    w(u'<div class="btn-toolbar">')
                    w(u'<div class="btn-group btn-group-justified">')
                    w(u'<a class="btn btn-primary" href="{0}" '
                       'style="width:80%">'.format(href))
                    w(u'{0}</a>'.format(ptype))
                    href = self._cw.build_url(
                        "view", vid="score-value-table-secondary",
                        study=study or "", etype="Scan", rtype=ptype,
                        rsubject="subject", pname="description",
                        title="QC Scores", elts_to_sort=["ID"],
                        tooltip_name="QC")
                    btn_status = "active"
                    if self.auto_disable_qc and ptype not in active_types:
                        btn_status = "disabled"
                    w(u'<a class="btn btn-success {0}" href="{1}" '
                       'style="width:15%">'.format(btn_status, href))
                    w(u'QC</a>')
                    w(u'</div></div><br/>')
                w(u'<hr>')
                w(u'</div></div><br/>')

        # QuestionnaireRun
        ajaxcallback = "get_questionnaires_data"
        rql_labels = ("DISTINCT Any T ORDERBY T WHERE A is Assessment, "
                      "A timepoint T")
        rql = "Any QR Where QR is QuestionnaireRun"
        if study is not None:
            rql += ", QR study ST, ST name '{0}'".format(study)
            rql_labels += ", A study ST, ST name '{0}'".format(study)
        href = self._cw.build_url(rql=rql)
        rql_types = ("DISTINCT Any T ORDERBY T " + rql[6:] +
                     ", QR questionnaire Q, Q type T")
        rset = self._cw.execute(rql_types)
        types = [line[0] for line in rset.rows]
        if len(types) > 0:
            # > main button
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group btn-group-justified">')
            w(u'<a class="btn btn-info"'
               'data-toggle="collapse" data-target="#questionnaires{0}" '
               'style="width:90%">'.format(study))
            w(u'Tables</a>')
            w(u'<a class="btn btn-primary" href="{0}" '
               'style="width:10%">'.format(href))
            w(u'&#9735;</a>')
            w(u'</div></div>')
            # > typed buttons container
            w(u'<div id="questionnaires{0}" class="collapse">'.format(study))
            w(u'<div class="panel-body">')
            w(u'<hr>')
            # > typed buttons
            for qtype in types:
                href = self._cw.build_url(
                    "view", vid="jtable-table",
                    rql_labels=rql_labels, ajaxcallback=ajaxcallback,
                    title="All Questionnaires", elts_to_sort=["ID"],
                    tooltip_name="All Questionnaires", qtype=qtype,
                    study=study or "")
                w(u'<div class="btn-toolbar">')
                w(u'<div class="btn-group-vertical btn-block">')
                w(u'<a class="btn btn-primary" href="{0}">'.format(href))
                w(u'{0}</a>'.format(qtype))
                w(u'</div></div><br/>')
            w(u'<hr>')
            w(u'</div></div><br/>')

        # ProcessingRun
        rql = "Any P Where P is ProcessingRun"
        if study is not None:
            rql += ", P study ST, ST name '{0}'".format(study)
        # > disable QC buttons
        if self.auto_disable_qc:
            rql_scores = ("DISTINCT Any T " + rql[5:] +
                          ", P type T, P score_values V")
            rset = self._cw.execute(rql_scores)
            active_types = set(row[0] for row in rset)
        # > build navigation
        href = self._cw.build_url(rql=rql)
        rql_types = "DISTINCT Any T ORDERBY T " + rql[5:] + ", P type T"
        rset = self._cw.execute(rql_types)
        types = [line[0] for line in rset.rows]
        if len(types) > 0:
            # > main button
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group btn-group-justified">')
            w(u'<a class="btn btn-info"'
               'data-toggle="collapse" data-target="#processings{0}" '
               'style="width:90%">'.format(study))
            w(u'Processed data</a>')
            w(u'<a class="btn btn-primary" href="{0}" '
               'style="width:10%">'.format(href))
            w(u'&#9735;</a>')
            w(u'</div></div>')
            # > typed buttons container
            w(u'<div id="processings{0}" class="collapse">'.format(study))
            w(u'<div class="panel-body">')
            w(u'<hr>')
            # > typed buttons
            for ptype in types:
                typed_rql = rql + ", P type '{0}'".format(ptype)
                href = self._cw.build_url(rql=typed_rql)
                w(u'<div class="btn-toolbar">')
                w(u'<div class="btn-group btn-group-justified">')
                w(u'<a class="btn btn-primary" href="{0}" style="width:80%">'.format(href))
                w(u'{0}</a>'.format(ptype))
                href = self._cw.build_url(
                    "view", vid="score-value-table-secondary", study=study or "",
                    etype="ProcessingRun", rtype=ptype, pname="parameters",
                    rsubject="subjects", title="QC Scores",
                    elts_to_sort=["ID"], tooltip_name="QC")
                btn_status = "active"
                if self.auto_disable_qc and ptype not in active_types:
                    btn_status = "disabled"
                w(u'<a class="btn btn-success {0}" href="{1}" '
                   'style="width:15%">'.format(btn_status, href))
                w(u'QC</a>')
                w(u'</div></div><br/>')
            w(u'<hr>')
            w(u'</div></div><br/>')

        # GenomicMeasures
        if self.display_genomic:
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            rql = "Any GM Where GM is GenomicMeasure"
            if study is not None:
                rql += ", GM study ST, ST name '{0}'".format(study)
            href = self._cw.build_url(rql=rql)
            w(u'<a class="btn btn-primary" href="{0}">'.format(href))
            w(u'Genomic measures</a>')
            w(u'</div></div><br/>')

        # MetaGen
        if self.display_metagen:
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            href = self._cw.build_url(rql="Any C Where C is Chromosome")
            w(u'<a class="btn btn-primary" href="{0}">'.format(href))
            w(u'MetaGen (hg38 dbsnp149)</a>')
            w(u'</div></div><br/>')

        # CWSearch
        w(u'<hr>')
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        href = self._cw.build_url(rql="Any S Where S is CWSearch")
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'<span class="glyphicon glyphicon-shopping-cart"></span> '
          u'My cart</a>')
        w(u'</div></div><br/>')

        # History
        if self.display_history:
            w(u'<hr>')
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            href = self._cw.build_url(vid="piws-history")
            w(u'<a class="btn btn-primary" href="{0}" target=_blank>'.format(href))
            w(u'<span class="glyphicon glyphicon-pushpin"></span> '
              u'History</a>')
            w(u'</div></div><br/>')


###############################################################################
# Statistic boxes
###############################################################################

class PIWSSubjectStatistics(component.CtxComponent):
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
        w(u'Gender repartition</a>')
        w(u'</div></div><br/>')

        # Create a view to see the subject handedness repartition in the db
        href = self._cw.build_url(
            "view", vid="highcharts-basic-pie",
            rql="Any H WHERE S is Subject, S handedness H",
            title="Subject handednesses")
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Handedness repartition</a>')
        w(u'</div></div><br/>')


class PIWSAssessmentStatistics(component.CtxComponent):
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
            relations=["scans", "questionnaire_runs", "genomic_measures"],
            subject_attr="timepoint", object_attr="label")
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Acquisition status</a>')
        w(u'</div></div><br/>')

        # Create a view to see the db processing status
        href = self._cw.build_url(
            "view", vid="highcharts-relation-summary-view",
            rql="Any A WHERE A is Assessment", title="Processing status",
            relations="processing_runs", subject_attr="timepoint",
            object_attr="label")
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


class PIWSSummary(component.CtxComponent):
    """ Display a summary table of all the available datasets.
    """
    __regid__ = "stat_box"
    contextual = True
    context = "right"
    title = ("Database content")
    order = 0
    __select__ = match_view("index")
    categories = ["Scan", "QuestionnaireRun", "ProcessingRun"]
    nb_types = None
    categories_mapping = {
        "Timepoint": "",
        "Scan": "Scans",
        "QuestionnaireRun": "Tables",
        "ProcessingRun": "Processed data"}
    rql_subjects = "Any S WHERE S is Subject, S study ST, ST name '{0}'"

    def render_body(self, w):
        """ Method to create the summary table for each study.
        """
        # Get an admin connection
        with self._cw.session.repo.internal_cnx() as session:

            # Go through each study
            studies = [row[0] for row in session.execute(
                "DISTINCT Any SN ORDERBY SN Where S is Study, S name SN")]
            for study in studies:

                # Display the study name
                w(u"<strong>Study:</strong> {0}<br/><br/>".format(study))

                # Get all the subjects attached to the current study
                rql = self.rql_subjects.format(study)
                nb_subjects = session.execute(rql).rowcount

                # Create the table
                w(u"<table class='table' style='font-size: 10px;'>")
                w(u"<tr>")
                for header in ["Timepoint"] + self.categories:
                    w(u"<th>{0}</th>".format(self.categories_mapping[header]))
                w(u"</tr>")

                # Go through each timepoint (one row per timepoint in the tab)
                timepoints = [row[0] for row in session.execute(
                    ("DISTINCT Any T ORDERBY T WHERE A is Assessment, "
                     "A timepoint T, A study ST, ST name '{0}'".format(study)))]
                for timepoint in timepoints:

                    # Go through each category (one column per category in
                    # the tab)
                    w(u"<tr>")
                    w(u"<td>{0}</td>".format(timepoint))
                    for category in self.categories:

                        # Deal with questionnaire special case
                        if category == "QuestionnaireRun":
                            type_name = "label"
                        else:
                            type_name = "type"

                        # Compute the fill ratio
                        try:
                            nb_types = self.nb_types[study][category]
                        except:
                            rql = ("DISTINCT Any T WHERE X is {0}, X {1} T, "
                                   "X study ST, ST name '{2}'".format(
                                        category, type_name, study))
                            nb_types = session.execute(rql).rowcount
                        rql = (
                            "Any X WHERE X is {0}, X study ST, ST name "
                            "'{1}', X in_assessment A, A timepoint "
                            "'{2}'".format(category, study, timepoint))
                        nb_items = session.execute(rql).rowcount
                        ratio = 0.
                        if nb_types != 0 and nb_subjects != 0:
                            ratio = (float(nb_items)  /
                                     float(nb_types * nb_subjects))

                        # Display the fill ratio
                        w(u"<td>")
                        w(u"<progress value='{0}' max='100' style='width:100%;'>"
                           "</progress>".format(ratio * 100.))
                        w(u"</td>")

                    w(u"</tr>")

                w(u"</table>")


###############################################################################
# Image viewers
###############################################################################

AUTHORIZED_IMAGE_EXT = [".nii", ".nii.gz"]


class PIWSImageViewers(component.CtxComponent):
    """ Display a box containing links to image viewers.
    """
    __regid__ = "image_viewers"
    context = "left"
    title = _("Image viewers")
    order = 1
    __select__ = is_instance("Scan") & one_line_rset

    def render_body(self, w, **kwargs):
        """ Method to create the image box content.
        """
        # 3D image viewer
        scan = self.cw_rset.get_entity(0, 0)
        if len(scan.filesets) > 0:
            efentries = scan.filesets[0].external_files
        else:
            efentries = []
        imagefiles = [e.filepath for e in efentries
                      if e.filepath.endswith(tuple(AUTHORIZED_IMAGE_EXT))]
        limagefiles = len(imagefiles)
        if limagefiles > 0:
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            href = self._cw.build_url(
                "view", vid="brainbrowser-image-viewer", imagefiles=imagefiles,
                __message=(u"Found '{0}' image(s) that can be "
                            "displayed.".format(limagefiles)))
            w(u'<a class="btn btn-primary" href="{0}" target=_blank>'.format(
                href))
            w(u'Triplanar</a>')
            w(u'</div></div><br/>')


###############################################################################
# Add a box to display entity relations
###############################################################################

class RelationBox(component.CtxComponent):
    """ Helper view class to display a relation rset in a sidebox.
    """
    __select__ = nonempty_rset() & match_kwargs("title", "rql")
    __regid__ = "relationbox"
    cw_property_defs = {}
    context = "incontext"

    @property
    def domid(self):
        return (super(RelationBox, self).domid + unicode(abs(id(self))) +
                unicode(abs(id(self.cw_rset))))

    def render_title(self, w):
        w(self.cw_extra_kwargs["title"])

    def render_body(self, w):
        defaultlimit = self._cw.property_value("navigation.related-limit")
        if not isinstance(self.cw_rset, list):
            rset = list(self.cw_rset.entities())
        else:
            rset = self.cw_rset
        for entity in rset[:(defaultlimit - 1)]:
            w(u"<div>&bull; " + entity.view(self.context) + u"</div>")
        # if len(rset) == defaultlimit:
        rql = self.cw_extra_kwargs["rql"]
        href = self._cw.build_url(rql=rql)
        w(u"<br/><div><a href='{0}'>&#8634; see more</a></div>".format(href))


###############################################################################
# Change logo
###############################################################################

@monkeypatch(ApplLogo)
def render(self, w):
    w(u'<a class="navbar-brand" href="%s"><img id="logo" src="%s" '
      'alt="logo"/></a>' % (
            self._cw.base_url(),
            self._cw.data_url(self._cw.vreg.config.get("logo"))))


###############################################################################
# Change footer
###############################################################################

class FooterView(EntityView):
    """ Footer content when an entity is displayed"""
    __regid__ = "metadata"
    show_eid = True

    def cell_call(self, row, col):
        _ = self._cw._
        entity = self.cw_rset.get_entity(row, col)
        self.w(u"<p class='text-right'><small>")
        if self.show_eid:
            self.w(u"{0} #{1} - ".format(entity.dc_type(), entity.eid))
        if entity.creation_date:
            self.w(u"<span>created on </span>")
            self.w(u"<span class='value'>{0}</span>".format(
                self._cw.format_date(entity.creation_date)))
        self.w(u"</small></p>")


###############################################################################
# Registry
###############################################################################

def registration_callback(vreg):
    vreg.register_and_replace(
        PIWSAuthenticatedUserStatus, BSAuthenticatedUserStatus)
    vreg.register(RelationBox)
    vreg.register(TimeLeft)
    vreg.register(PIWSNavigationtBox)
    vreg.register(PIWSSubjectStatistics)
    vreg.register(PIWSAssessmentStatistics)
    vreg.register(PIWSImageViewers)
    vreg.register(PIWSSummary)
    vreg.unregister(EditBox)
    vreg.unregister(BreadCrumbEntityVComponent)
    vreg.unregister(BreadCrumbAnyRSetVComponent)
    vreg.unregister(BreadCrumbETypeVComponent)
    vreg.unregister(BreadCrumbLinkToVComponent)
    vreg.unregister(AnonUserStatusLink)
    vreg.register_and_replace(FooterView, MetaDataView)
    config = load_forms(vreg.config)
    if not isinstance(config, dict):
        vreg.unregister(CWUploadBox)
