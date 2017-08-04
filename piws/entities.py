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
from cubes.piws.config import ASSESSMENT_CONTAINER
from cubes.rql_upload.entities import EntityUploadFile


##############################################################################
# Define entities properties
##############################################################################

class FMRIData(AnyEntity):
    __regid__ = "FMRIData"

    def dc_title(self):
        """Define the FMRIData entity title.
        """
        return u"FMRI data"


class PETData(AnyEntity):
    __regid__ = "PETData"

    def dc_title(self):
        return u"PET data"


class MRIData(AnyEntity):
    __regid__ = "MRIData"

    def dc_title(self):
        return u"MRI data"


class DMRIData(AnyEntity):
    __regid__ = "DMRIData"

    def dc_title(self):
        return "DMRI data"


class SPECTROData(AnyEntity):
    __regid__ = "SPECTROData"

    def dc_title(self):
        return "SPECTRO data"


class EEGData(AnyEntity):
    __regid__ = "EEGData"

    def dc_title(self):
        return "EEG data"


class ETData(AnyEntity):
    __regid__ = "ETData"

    def dc_title(self):
        return "Eye Tracking data"


class PETData(AnyEntity):
    __regid__ = "PETData"

    def dc_title(self):
        return "PET data"


class Scan(AnyEntity):
    __regid__ = "Scan"

    def dc_title(self):
        return u"{0} ({1}): {2}".format(
            self.label, self.in_assessment[0].timepoint,
            self.subject[0].code_in_study)

    @property
    def symbol(self):
        dtype = self.has_data[0]
        if dtype.__class__.__name__ == "DMRIData":
            return "images/dmri.png"
        elif dtype.__class__.__name__ == "FMRIData":
            return "images/fmri.png"
        elif dtype.__class__.__name__ == "MRIData":
            return "images/mri.png"
        elif dtype.__class__.__name__ == "PETData":
            return "images/pet.png"
        elif dtype.__class__.__name__ == "EEGData":
            return "images/eeg.jpg"
        elif dtype.__class__.__name__ == "ETData":
            return "images/eye-tracking.jpg"
        elif dtype.__class__.__name__ == "SPECTROData":
            return "images/spectro.png"


class Assessment(AnyEntity):
    __regid__ = "Assessment"
    container_config = ASSESSMENT_CONTAINER

    def dc_title(self):
        relations = []
        if self.scans:
            relations.append("Scans")
        if self.questionnaire_runs:
            relations.append("QuestionnaireRun")
        if self.genomic_measures:
            relations.append("GenomicMeasure")
        return u"{0}: {1} {2}".format(
            self.timepoint, self.subjects[0].code_in_study,
            "..." if len(self.subjects) > 1 else "")

    @property
    def symbol(self):
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
        return self.code_in_study

    @property
    def symbol(self):
        if self.gender == "male":
            return "images/male.png"
        elif self.gender == "female":
            return "images/female.png"
        else:
            return "images/unknown.png"


class QuestionnaireRun(AnyEntity):
    __regid__ = "QuestionnaireRun"

    def dc_title(self):
        return u"{0} ({1}): {2}".format(
            self.questionnaire[0].name, self.in_assessment[0].timepoint,
            self.subject[0].code_in_study)

    @property
    def symbol(self):
        return "images/questionnaire.png"


class ProcessingRun(AnyEntity):
    __regid__ = "ProcessingRun"

    def dc_title(self):
        """Define the processing run entity title.
        """
        return u"{0} ({1}): {2} {3}".format(
            self.label, self.in_assessment[0].timepoint,
            self.subjects[0].code_in_study,
            "..." if len(self.subjects) > 1 else "")

    @property
    def symbol(self):
        if self.label in ["EDDY", "FA", "MD", "MO", "NODIFF BRAIN", "RD",
                         "RESTORE"]:
            return "images/dmri.png"
        elif self.label == "1KG_snps_indels_EUR":
            return "images/gchip.png"
        elif self.label.lower() == "morphologist":
            return "images/morphologist.png"
        elif self.label.lower() == "connectomist":
            return "images/tracto.png"
        elif self.label.lower() == "freesurfer":
            return "images/freesurfer.png"
        elif self.label in ["SPM preproc EPI_mid", "SPM preproc EPI_faces",
                            "SPM preproc EPI_stop_signal"]:
            return "images/fmri.png"
        return "images/processing.png"


class GenomicMeasure(AnyEntity):
    __regid__ = "GenomicMeasure"

    def dc_title(self):
        return u"{0} ({1}): {2} {3}".format(
            self.label, self.in_assessment[0].timepoint,
            self.subjects[0].code_in_study,
            "..." if len(self.subjects) > 1 else "")

    @property
    def symbol(self):
        return "images/gchip.png"


class Question(AnyEntity):
    __regid__ = "Question"
    __bootstap_glyph__ = True

    def dc_title(self):
        return unicode(self.questionnaire[0].name + ": " + self.text)

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-question-sign'></span>"


class Questionnaire(AnyEntity):
    __regid__ = "Questionnaire"
    __bootstap_glyph__ = True

    def dc_title(self):
        return self.name

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-question-sign'></span>"


class TextAnswer(AnyEntity):
    __regid__ = "TextAnswer"
    __bootstap_glyph__ = True

    def dc_title(self):
        return unicode(self.question[0].dc_title() + ": " + self.value)

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-plus-sign'></span>"


class IntAnswer(AnyEntity):
    __regid__ = "IntAnswer"
    __bootstap_glyph__ = True

    def dc_title(self):
        return unicode(
            self.question[0].dc_title() + ": {0}".format(self.value))

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-plus-sign'></span>"


class FloatAnswer(AnyEntity):
    __regid__ = "FloatAnswer"
    __bootstap_glyph__ = True

    def dc_title(self):
        return unicode(
            self.question[0].dc_title() + ": {0}".format(self.value))

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-plus-sign'></span>"


class Snp(AnyEntity):
    __regid__ = "Snp"

    def dc_title(self):
        return self.rs_id

    @property
    def symbol(self):
        return "images/snps.png"


class Chromosome(AnyEntity):
    __regid__ = "Chromosome"

    def dc_title(self):
        return self.name

    @property
    def symbol(self):
        return "images/chromosome.png"


class Gene(AnyEntity):
    __regid__ = "Gene"

    def dc_title(self):
        return self.gene_id

    @property
    def symbol(self):
        return "images/gene.png"


class CpG(AnyEntity):
    __regid__ = "CpG"

    def dc_title(self):
        return self.cg_id

    @property
    def symbol(self):
        return "images/cpg.png"


class CpGIsland(AnyEntity):
    __regid__ = "CpGIsland"

    def dc_title(self):
        return self.cpg_island_id

    @property
    def symbol(self):
        return "images/cpgisland.png"


class Pathway(AnyEntity):
    __regid__ = "Pathway"

    def dc_title(self):
        return self.name

    @property
    def symbol(self):
        return "images/pathway.png"


class GenomicPlatform(AnyEntity):
    __regid__ = "GenomicPlatform"
    __bootstap_glyph__ = True

    def dc_title(self):
        return self.name

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-filter'></span>"


class FileSet(AnyEntity):
    __regid__ = "FileSet"
    __bootstap_glyph__ = True

    def dc_title(self):
        return self.name

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-folder-open'></span>"


class ExternalFile(AnyEntity):
    __regid__ = "ExternalFile"
    __bootstap_glyph__ = True

    def dc_title(self):
        return self.name

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-file'></span>"


class File(AnyEntity):
    __regid__ = "File"
    __bootstap_glyph__ = True

    def dc_title(self):
        return self.data_format

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-file'></span>"


class RestrictedFile(AnyEntity):
    __regid__ = "RestrictedFile"
    __bootstap_glyph__ = True

    def dc_title(self):
        return self.title

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-file'></span>"


class CWSearch(AnyEntity):
    __regid__ = "CWSearch"
    __bootstap_glyph__ = True

    def dc_title(self):
        return self.title

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-shopping-cart'></span>"


class Center(AnyEntity):
    __regid__ = "Center"

    def dc_title(self):
        return self.name


class Study(AnyEntity):
    __regid__ = "Study"

    def dc_title(self):
        return self.name


class Device(AnyEntity):
    __regid__ = "Device"
    __bootstap_glyph__ = True

    def dc_title(self):
        return u"{0} ({1})".format(self.manufacturer, self.center[0].name)

    @property
    def symbol(self):
        return "<span class='glyphicon glyphicon-facetime-video'></span>"
