# -*- coding: utf-8 -*-
# copyright 2014 nsap, all rights reserved.
# contact http://www.logilab.fr -- mailto:antoine.grigis@cea.fr
#
#! /usr/bin/env python
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

class Scan(AnyEntity):
    __regid__ = "Scan"

    def dc_title(self):
        """ Method the defined the scan entity title
        """
        dtype = self.has_data[0]
        return "{0} ({1}-{2}-{3})".format(
            self.label, self.in_assessment[0].timepoint,
            dtype.__class__.__name__, self.subject[0].code_in_study)

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
        if self.scans and self.questionnaire_runs:
            return "Scans - Questionnaire Run ({0}-{1})".format(
                self.timepoint, self.subjects[0].code_in_study)
        elif self.scans:
            return "Scans ({0}-{1})".format(
                self.timepoint, self.subjects[0].code_in_study)
        elif self.questionnaire_runs:
            return "Questionnaire Run ({0}-{1})".format(
                self.timepoint, self.subjects[0].code_in_study)
        else:
            return "Genomic Measure ({0})".format(self.timepoint)

    @property
    def symbol(self):
        """ This property will return a symbol cooresponding to the scan
        type
        """
        if self.scans or self.questionnaire_runs:
            return "images/questionnaire.png"
        elif self.related_processing:
            return "images/processing.png"
        elif self.genomic_measures:
            return "images/samples.png"


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


class GenomicMeasure(AnyEntity):
    __regid__ = "GenomicMeasure"

    def dc_title(self):
        """ Method the defined the processing run entity title
        """
        return "Genomic Measure ({0}-{1})".format(
            self.in_assessment[0].timepoint, self.type)

    @property
    def symbol(self):
        """ This property will return a symbol cooresponding to the processing
        run type
        """
        return "images/samples.png"

