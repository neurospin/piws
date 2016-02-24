# -*- coding: utf-8 -*-
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.predicates import is_instance
from cubicweb.entities import AnyEntity

# Cubes import
from cubes.medicalexp.config import ASSESSMENT_CONTAINER


##############################################################################
# Define entities properties
##############################################################################

class FMRIData(AnyEntity):
    __regid__ = "FMRIData"

    def dc_title(self):
        """Define the FMRIData entity title.
        """
        return "FMRI data"


class PETData(AnyEntity):
    __regid__ = "PETData"

    def dc_title(self):
        """Define the PETData entity title.
        """
        return "PET data"

class MRIData(AnyEntity):
    __regid__ = "MRIData"

    def dc_title(self):
        """Define the MRIData entity title.
        """
        return "MRI data"


class DMRIData(AnyEntity):
    __regid__ = "DMRIData"

    def dc_title(self):
        """Define the DMRIData entity title.
        """
        return "DMRI data"


class Scan(AnyEntity):
    __regid__ = "Scan"

    def dc_title(self):
        """Define the scan entity title.
        """
        return "{0} of {1} (time {2})".format(
            self.label, self.subject[0].code_in_study,
            self.in_assessment[0].timepoint)

    @property
    def symbol(self):
        """Return a symbol corresponding to the scan type.
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
        """Define the assessment entity title.
        """
        relations = []
        if self.scans:
            relations.append("Scans")
        if self.questionnaire_runs:
            relations.append("QuestionnaireRun")
        if self.genomic_measures:
            relations.append("GenomicMeasure")
        return "Assessment of {0} (time {1} - type {2})".format(
            self.subjects[0].code_in_study, self.timepoint,
            "/".join(relations))

    @property
    def symbol(self):
        """Return a symbol corresponding to the assessment type.
        """
        if self.scans or self.questionnaire_runs:
            return "images/questionnaire.png"
        elif self.processing_runs:
            return "images/processing.png"
        elif self.genomic_measures:
            return "images/samples.png"
        else:
            raise Exception("Unknown assessment.")


class Subject(AnyEntity):
    __regid__ = "Subject"

    def dc_title(self):
        """Define the subject entity title.
        """
        return "Subject {0}".format(self.code_in_study)

    @property
    def symbol(self):
        """Return a symbol corresponding to the subject gender.
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
        """Define the questionnaire run entity title.
        """
        return "QuestionnaireRun of {0}".format(
            self.subject[0].code_in_study.replace("_", " - "))

    @property
    def symbol(self):
        """Return a symbol corresponding to the questionnaire run type.
        """
        return "images/questionnaire.png"


class ProcessingRun(AnyEntity):
    __regid__ = "ProcessingRun"

    def dc_title(self):
        """Define the processing run entity title.
        """
        return ("ProcessingRun {0} (time {1})".format(self.name,
                self.in_assessment[0].timepoint))

    @property
    def symbol(self):
        """Return a symbol corresponding to the processing run type.
        """
        fset = self.results_files[0]
        if fset.name in ["EDDY", "FA", "MD", "MO", "NODIFF BRAIN", "RD",
                         "RESTORE"]:
            return "images/dmri.png"
        elif fset.name == "1KG_snps_indels_EUR":
            return "images/gchip.png"
        elif fset.name == "freesurfer":
            return "images/mri.jpg"
        elif fset.name in ["SPM preproc EPI_mid", "SPM preproc EPI_faces",
                           "SPM preproc EPI_stop_signal"]:
            return "images/fmri.jpg"
        return "images/processing.png"


class GenomicMeasure(AnyEntity):
    __regid__ = "GenomicMeasure"

    def dc_title(self):
        """Define the genomic measure run entity title.
        """
        return ("{0} (time {1})".format(self.label,
                self.in_assessment[0].timepoint))

    @property
    def symbol(self):
        """Return a symbol corresponding to the genomic measure type.
        """
        return "images/gchip.png"
