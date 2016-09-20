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
from cubicweb.predicates import one_line_rset
from cubicweb.predicates import match_view
from cubicweb.predicates import match_kwargs
from cubicweb.web.views.basecomponents import AnonUserStatusLink
from cubicweb.web.views.basecomponents import ApplLogo
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
        if config.get("show_user_status", "no") == "yes":
            if config.get("enable-apache-logout", "no") == "yes":
                w(u"<a href='{0}' class='button'>Logout</a>".format(
                    self._cw.base_url() + 'logout'))
            else:
                if config.get("apache-cleanup-session-time", None) is not None:
                    raise NotImplementedError(
                        "Session expiration with Apache is not yet available "
                        "due to cross browsers compatibility issues.")
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
    """
    __regid__ = "nav_box"
    context = "left"
    title = _("Navigation")
    order = 0
    display_assessment = True

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

        # Assessments
        if self.display_assessment:
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            href = self._cw.build_url(rql="Any A Where A is Assessment")
            w(u'<a class="btn btn-primary" href="{0}">'.format(href))
            w(u'Assessments</a>')
            w(u'</div></div><br/>')

        # Scan
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        href = self._cw.build_url(rql="Any S Where S is Scan")
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Scans</a>')
        w(u'</div></div><br/>')

        # QuestionnaireRun
        ajaxcallback = "get_questionnaires_data"
        rql_labels = ("DISTINCT Any T ORDERBY T WHERE A is Assessment, "
                      "A timepoint T")
        rql_types = ("DISTINCT Any T ORDERBY T WHERE Q is Questionnaire, "
                      "Q type T")
        rset = self._cw.execute(rql_types)
        types = [line[0] for line in rset.rows]
        if len(types) > 0:
            # > main button
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            w(u'<a class="btn btn-info"'
               'data-toggle="collapse" data-target="#questionnaires">')
            w(u'Tables</a>')
            w(u'</div></div>')
            # > typed buttons container
            w(u'<div id="questionnaires" class="collapse">')
            w(u'<div class="panel-body">')
            w(u'<hr>')
            # > typed buttons
            for qtype in types:
                href = self._cw.build_url(
                    "view", vid="jtable-table",
                    rql_labels=rql_labels, ajaxcallback=ajaxcallback,
                    title="All Questionnaires", elts_to_sort=["ID"],
                    tooltip_name="All Questionnaires", qtype=qtype)
                w(u'<div class="btn-toolbar">')
                w(u'<div class="btn-group-vertical btn-block">')
                w(u'<a class="btn btn-primary" href="{0}">'.format(href))
                w(u'{0}</a>'.format(qtype.title()))
                w(u'</div></div><br/>')
            w(u'<hr>')
            w(u'</div></div><br/>')

        # ProcessingRun
        rql_types = ("DISTINCT Any T ORDERBY T WHERE P is ProcessingRun, "
                      "P type T")
        rset = self._cw.execute(rql_types)
        types = [line[0] for line in rset.rows]
        if len(types) > 0:
            # > main button
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            w(u'<a class="btn btn-info"'
               'data-toggle="collapse" data-target="#processings">')
            w(u'Processed data</a>')
            w(u'</div></div>')
            # > typed buttons container
            w(u'<div id="processings" class="collapse">')
            w(u'<div class="panel-body">')
            w(u'<hr>')
            # > typed buttons
            for ptype in types:
                href = self._cw.build_url(rql="Any P Where P is ProcessingRun, "
                                              "P type '{0}'".format(ptype))
                w(u'<div class="btn-toolbar">')
                w(u'<div class="btn-group-vertical btn-block">')
                w(u'<a class="btn btn-primary" href="{0}">'.format(href))
                w(u'{0}</a>'.format(ptype.title()))
                w(u'</div></div><br/>')
            w(u'<hr>')
            w(u'</div></div><br/>')

        # GenomicMeasures
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        href = self._cw.build_url(rql="Any GM Where GM is GenomicMeasure")
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Genomic measures</a>')
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

        # CWUpload
        config = load_forms(self._cw.vreg.config)
        if config > 0:
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            href = self._cw.build_url(rql="Any U Where U is CWUpload")
            w(u'<a class="btn btn-primary" href="{0}">'.format(href))
            w(u'<span class="glyphicon glyphicon glyphicon-cloud-upload">'
                '</span> My uploads</a>')
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
            rql="Any A WHERE A is Assessment", title="Insertion status",
            relations="subjects", subject_attr="timepoint",
            object_attr="identifier")
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Insertion status</a>')
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
        efentries = self.cw_rset.get_entity(0, 0).filesets[0].external_files
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
# Registry
###############################################################################

def registration_callback(vreg):
    vreg.register_and_replace(
        PIWSAuthenticatedUserStatus, BSAuthenticatedUserStatus)
    vreg.register(RelationBox)
    vreg.register(PIWSNavigationtBox)
    vreg.register(PIWSSubjectStatistics)
    vreg.register(PIWSAssessmentStatistics)
    vreg.register(PIWSImageViewers)
    vreg.unregister(EditBox)
    vreg.unregister(BreadCrumbEntityVComponent)
    vreg.unregister(BreadCrumbAnyRSetVComponent)
    vreg.unregister(BreadCrumbETypeVComponent)
    vreg.unregister(BreadCrumbLinkToVComponent)
    vreg.unregister(AnonUserStatusLink)
    config = load_forms(vreg.config)
    if config < 0:
        vreg.unregister(CWUploadBox)
