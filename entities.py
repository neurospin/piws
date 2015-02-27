# -*- coding: utf-8 -*-
# copyright 2014 nsap, all rights reserved.
# contact http://www.logilab.fr -- mailto:antoine.grigis@cea.fr
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from cubicweb.predicates import is_instance
# from cubes.rsetftp.entities import BaseIFilePathAdapter
from cubicweb.entities import AnyEntity

from cubes.medicalexp.config import ASSESSMENT_CONTAINER


##############################################################################
# Define entities properties
##############################################################################

class Scan(AnyEntity):
    __regid__ = "Scan"

    def dc_title(self):
        """ Method the defined the scan entity title
        """
        dtype = self.has_data[0]
        return "{0} ({1})".format(self.label, dtype.__class__.__name__)

    @property
    def symbol(self):
        """ This property will return a symbol cooresponding to the scan
        type
        """
        dtype = self.has_data[0]
        if dtype.__class__.__name__ == "DMRIData":
            return "images/dmri.png"
        elif dtype.__class__.__name__ == "FMRIData":
            return "images/fmri.jpg"
        elif dtype.__class__.__name__ == "MRIData":
            return "images/mri.jpg"


class Assessment(AnyEntity):
    __regid__ = "Assessment"
    container_config = ASSESSMENT_CONTAINER

    def dc_title(self):
        """ Method the defined the assessment entity title
        """
        subject = self.reverse_concerned_by[0]
        return "{0}".format(subject.code_in_study)

    @property
    def symbol(self):
        """ This property will return a symbol cooresponding to the scan
        type
        """
        if self.uses:
            run_item = self.uses[0]
        elif self.related_processing:
            run_item = self.related_processing[0]
        else:
            run_item = type("Dummy", (object, ), {})

        if run_item.__class__.__name__ == "QuestionnaireRun":
            return "images/questionnaire.png"
        elif run_item.__class__.__name__ == "Scan":
            field = run_item.has_data[0].field
            if field == "3T":
                return "images/irm3t.png"
            elif field == "7T":
                return "images/irm7t.png"
            else:
                return "images/unknown.png"
        elif run_item.__class__.__name__ == "ProcessingRun":
            return "images/processing.png"
        else:
            return "images/unknown.png"


class Subject(AnyEntity):
    __regid__ = "Subject"

    def dc_title(self):
        """ Method the defined the subject entity title
        """
        return "{0}".format(self.code_in_study)

    @property
    def symbol(self):
        """ This property will return a symbol cooresponding to the subject
        gender
        """
        if self.gender == "male":
            return "images/male.png"
        elif self.gender == "female":
            return "images/female.png"
        else:
            return "images/unknown.png"


class QuestionnaireRun(AnyEntity):
    __regid__ = "QuestionnaireRun"

    def dc_title(self):
        """ Method the defined the questionnaire run entity title
        """
        return "{0}".format(self.user_ident.replace("_", " - "))

    @property
    def symbol(self):
        """ This property will return a symbol cooresponding to the questionnaire
        run type
        """
        return "images/questionnaire.png"


class ProcessingRun(AnyEntity):
    __regid__ = "ProcessingRun"

    def dc_title(self):
        """ Method the defined the processing run entity title
        """
        return "{0}-{1}".format(self.name, self.tool)

    @property
    def symbol(self):
        """ This property will return a symbol cooresponding to the processing
        run type
        """
        return "images/processing.png"


class BioSample(AnyEntity):
    __regid__ = "BioSample"

    def dc_title(self):
        """ Method the defined the bio sample entity title
        """
        return "{0}-{1}".format(self.label, self.sample_creation_date)

    @property
    def symbol(self):
        """ This property will return a symbol cooresponding to the bio
        sample type
        """
        return "images/samples.png"


##############################################################################
# Define adaptors for the CWSearch entity
##############################################################################


#class ScanIFilePathAdapter(BaseIFilePathAdapter):
#    __select__ = (BaseIFilePathAdapter.__select__ &
#                  is_instance("Scan", "QuestionnaireRun","GenomicMeasure"))

#    def get_paths(self):
#        rset = self._cw.execute("Any F, ABS, S, FP, DF WHERE "
#                                "X eid %(eid)s, X results_files RF, "
#                                "RF file_entries F, "
#                                "F absolute_path ABS, F study_path S, "
#                                "S data_filepath DF, F filepath FP",
#                                {"eid": self.entity.eid})
        #for f in rset.entities():
            #fp = f.cw_adapt_to("IFilePath")
            #for p in fp.get_paths():
            #    yield p
#        for row in rset.rows:
#            yield row[3]


#class ScanIFilePathAdapter(BaseIFilePathAdapter):
#    __select__ = (BaseIFilePathAdapter.__select__ &
#                  is_instance("Scan", "QuestionnaireRun", "GenomicMeasure"))

#    def get_paths(self):
#        for f in self.entity.results_files:
#            fp = f.cw_adapt_to("IFilePath")
#            for p in fp.get_paths():
#                yield p


#class FileIFilePathAdapter(BaseIFilePathAdapter):
#    __select__ = BaseIFilePathAdapter.__select__ & is_instance("File")

#    def get_paths(self):
#        try:
#            storage = self._cw.repo.system_source.storage('File', 'data')
#            yield storage.current_fs_path(self.entity, "data")
#        except:
            # if there is no storage for attribute data of entity File
            # this mean file is stored in db (not in filesystem)
#            pass
#        yield osp.join("/", "%s_%s" % (self.entity.data_name, self.entity.eid))


#class ExternalIFilePathAdapter(BaseIFilePathAdapter):
#    __select__ = BaseIFilePathAdapter.__select__ & is_instance("ExternalFile")
#
#    def get_paths(self):
#        p = self.entity.filepath
#        if not self.entity.absolute_path:
#            p = osp.join(self.entity.study_path[0].data_filepath, p)
#        yield p


#class FileSetIFilePathAdapter(BaseIFilePathAdapter):
#    __select__ = BaseIFilePathAdapter.__select__ & is_instance("FileSet")
#
#    def get_paths(self):
#        for f in self.entity.file_entries:
#            for p in f.cw_adapt_to("IFilePath").get_paths():
#                yield p
