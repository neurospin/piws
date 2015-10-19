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

# Cubes import
from cubes.brainomics.views.components import BrainomicsLinksCenters
from cubes.brainomics.views.components import BrainomicsEditBox
from cubes.brainomics.views.components import BrainomicsDownloadBox
from cubes.bootstrap.views.basecomponents import BSAuthenticatedUserStatus

###############################################################################
# Navigation Box
###############################################################################


class PiwsAuthenticatedUserStatus(BSAuthenticatedUserStatus):
    """
    Overrride bootstrap user-status component.
    In all-in-one.conf:
    If show-user-status=1 : activated (default: bootstrap component).
    If show-user-status=0 : deactivated.
    If show-user-status=1 and apache-cleanup-session-time is specified:
    diplay a logout button next to the search field.
    """
    def render(self, w):
        config = self._cw.vreg.config
        if config.get("show_user_status", None) == 'no':
            w(u'')
        elif config.get('apache-cleanup-session-time', None) is not None:
            w(u'<button type="button">Logout</button>')
        else:
            super(PiwsAuthenticatedUserStatus, self).render(w)


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
        # Test
        if 0:
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            imagefiles = [
                "/home/ag239446/git/brainbrowser/examples/models/nifti.nii.gz",
                "/home/ag239446/git/brainbrowser/examples/models/nifti2.nii.gz"
            ]
            href = self._cw.build_url(
                "view", vid="brainbrowser-image-viewer",
                imagefiles=imagefiles)
            w(u'<a class="btn btn-primary" href="{0}">'.format(href))
            w(u'Test 3D</a>')
            w(u'</div></div><br/>')
            w(u'<div class="btn-toolbar">')
            w(u'<div class="btn-group-vertical btn-block">')
            imagefiles = ["/home/ag239446/git/brainbrowser/examples/models/nifti2.nii.gz"]
            href = self._cw.build_url(
                "view", vid="brainbrowser-image-viewer", imagefiles=imagefiles)
            w(u'<a class="btn btn-primary" href="{0}">'.format(href))
            w(u'Test 4D</a>')
            w(u'</div></div><br/>')

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
            title="All Questionnaires", elts_to_sort=["ID"],
            tooltip_name="Questionnaire_general_doc")
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'Questionnaires</a>')
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
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        href = self._cw.build_url(rql="Any U Where U is CWUpload")
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
        w(u'My uploads</a>')
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
            rql="Any A WHERE A is Assessment", title="Insertion status",
            relations="subjects", subject_attr="timepoint",
            object_attr="identifier")
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
            relations="related_processing", subject_attr="timepoint",
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


###############################################################################
# Image viewers
###############################################################################

AUTHORIZED_IMAGE_EXT = [".nii", ".nii.gz"]


class NSImageViewers(component.CtxComponent):
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
        w(u'<div class="btn-toolbar">')
        w(u'<div class="btn-group-vertical btn-block">')
        efentries = self.cw_rset.get_entity(0, 0).results_files[0].file_entries
        imagefiles = [e.filepath for e in efentries
                      if e.filepath.endswith(tuple(AUTHORIZED_IMAGE_EXT))]
        limagefiles = len(imagefiles)
        if limagefiles > 0:
            href = self._cw.build_url(
                "view", vid="brainbrowser-image-viewer", imagefiles=imagefiles,
                __message=(u"Found '{0}' image(s) that can be "
                            "displayed.".format(limagefiles)))
        w(u'<a class="btn btn-primary" href="{0}">'.format(href))
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
            rset = self.cw_rset[0]
        for entity in rset[:(defaultlimit - 1)]:
            w(u"<div>&bull; " + entity.view(self.context) + u"</div>")
        # if len(rset) == defaultlimit:
        rql = self.cw_extra_kwargs["rql"]
        href = self._cw.build_url(rql=rql)
        w(u"<br/><div><a href='{0}'>&#8634; see more</a></div>".format(href))


def registration_callback(vreg):

    # Update components
    vreg.register_and_replace(PiwsAuthenticatedUserStatus,
                              BSAuthenticatedUserStatus)
    vreg.register(RelationBox)
    vreg.register(NSNavigationtBox)
    vreg.register(NSSubjectStatistics)
    vreg.register(NSAssessmentStatistics)
    vreg.register(NSImageViewers)
    vreg.unregister(BrainomicsLinksCenters)
    vreg.unregister(BrainomicsEditBox)
    vreg.unregister(BrainomicsDownloadBox)
