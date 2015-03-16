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
        related_subject = self.reverse_concerned_by
        if len(related_subject) > 0:
            subject = related_subject[0]
            return "{0}".format(subject.code_in_study)
        else:
            return "genomic measure"

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

