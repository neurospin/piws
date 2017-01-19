# coding: utf-8
##########################################################################
# NSAp - Copyright (C) CEA, 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from collections import OrderedDict, defaultdict
import json
import re
import time
import os
import numpy

# Cubicweb import
from cubicweb.view import View
from cubicweb.web.views.json import JsonMixIn

# Package import
from cubes.piws.metagen.genotype import genotype_measure


class MetaGenSearchView(View):
    """ View to display the genomic measures store in PLINK format: bef/bim/fam
    files.

    The view id is 'metagen-search': .../view?vid=metagen-search&... . This
    view accpets four parameters:
    - measure (mandatory): specify the GenomicMeasure entity 'label' that
      contains the PLINK file to be analysed: ...&measure=Chip1&...
    - gene (manadatory): in order to filter the genomic dataset specify at
      least one gene 'hgnc_id': ...&gene=CAMTA1&gene=EVI5...
    - subject (optional, default all subjects): used to acces the data of
      specific subjects only: ....&subject=iid1&subject=iid2...
    - export (optional, default 'data'): the data export type: 'data' will
      export the measured genomic data from the selected filtering options,
      'metagen' will export the genomic metadata reference from the selected
      genes only, 'ref'  will export the genomic metadata reference from the
      selected filtering options: ...&export=ref&...
    """
    __regid__ = "metagen-search"
    title = _("MetaGen Search")
    div_id = "metagen-search"
    _display = True

    def call(self):
        """ Generate/display the genomic dataset of insterest.
        """
        # Display header
        if self._display:
            self.w(u"<h1>MetaGen Search</h1>")
            self.w(u"<hr>")

        # Retrieve form parameters from the url
        genes = self._cw.form.get("gene", None)
        if genes is not None and not isinstance(genes, list):
            genes = [genes]
        measure = self._cw.form.get("measure", None)
        subjects = self._cw.form.get("subject", None)
        if subjects is not None and not isinstance(subjects, list):
            subjects = [subjects]
        export_type = self._cw.form.get("export", "data")

        # Display search parameters
        if self._display:
            self.w(u"<b>Gene Names</b>: {0}<br/>".format("; ".join(genes)))
            self.w(u"<b>Genomic Measure</b>: {0}<br/>".format(measure))
            self.w(u"<b>Subject</b>: {0}<br/>".format(
                "; ".join(subjects) if subjects is not None else "all"))
            self.w(u"<b>Export Type</b>: {0}<br/>".format(export_type))

        # Check input parameters
        if genes is None or measure is None:
            msg = ("Need a gene name to perform a search and a valid "
                   "genomic measure name.")
            if self._display:
                self.error(msg)
            else:
                self.w(unicode(json.dumps({"error": msg})))
            return
        if export_type not in ("data", "metagen", "ref"):
            msg = ("'{0}' export type not recognize. Supported format are "
                   "'data', 'metagen' and 'ref'.".format(export_type))
            if self._display:
                self.error(msg)
            else:
                self.w(unicode(json.dumps({"error": msg})))
            return       
        
        # Get the genomic measure associated plink files
        rset = self._cw.execute(
            "Any G Where G is GenomicMeasure, G label '{0}'".format(measure))
        if rset.rowcount != 1:
            msg = u"'{0}' genomic measure(s) detected, one expected.".format(
                rset.rowcount)
            if self._display:
                self.error(msg)
            else:
                self.w(unicode(json.dumps({"error": msg})))
            return
        egmeasure = rset.get_entity(0, 0)
        plinkfiles = []
        for efset in egmeasure.filesets:
            for efile in efset.external_files:
                plinkfiles.append(efile.filepath)
        if self._display:
            self.w(u"<b>Plink Files</b>: {0}<br/>".format(
                "; ".join(plinkfiles)))
            self.w(u"<br/>")
        roots = []
        for path in plinkfiles:
            root, ext = os.path.splitext(path)
            if ext not in [".bed", ".bim", ".fam"]:
                msg = u"'{0}' plink extension not supported.".format(ext)
                if self._display:
                    self.error(msg)
                else:
                    self.w(unicode(json.dumps({"error": msg})))
                return
            roots.append(root)
        if len(roots) != 3 or len(set(roots)) != 1:
            msg = u"Three plink bed/bim/fam files expected in the same folder."
            if self._display:
                self.error(msg)
            else:
                self.w(unicode(json.dumps({"error": msg})))
            return  

        # Load the plink and the
        try:
            snp_data, metagen_snps_of_gene = genotype_measure(
                path_dataset=root,
                snp_ids=None,
                gene_names=genes,
                subject_ids=subjects,
                count_A1=True,
                path_log=None,
                timeout=10,
                nb_tries=3,
                metagen_url=self._cw.vreg.config["metagen_url"])
        except Exception as e:
            msg = u"Can't acces the required genotype measure: {0}".format(
                e)
            if self._display:
                self.error(msg)
            else:
                self.w(unicode(json.dumps({"error": msg})))
            return

        # Display result in a table view

        # > export the measured genomic data from the selected filtering
        # options
        if export_type == "data":
            labels = ["family_id"] + snp_data.sid.tolist()
            records = numpy.concatenate((snp_data.iid, snp_data.val),
                                        axis=1).tolist()
            if self._display:
                self.wview("jtable-hugetable-clientside", None, "null",
                           labels=labels, records=records, csv_export=True,
                           title="Genotypes", timepoint="",
                           elts_to_sort=["ID", "family_id"],
                           tooltip_name=None, use_scroller=False, index=0)
            else:
                labels = ["subject_id"] + labels
                self.w(unicode(json.dumps({"labels": labels,
                                           "records": records})))

        # > export the genomic metadata reference from the selected filtering
        # options
        elif export_type == "ref":
            labels = ["chromosome", "cM_position", "bp_position"]
            snp_data.sid.shape += (1, )
            records = numpy.concatenate((snp_data.sid, snp_data.pos),
                                        axis=1).tolist()
            if self._display:
                self.wview("jtable-hugetable-clientside", None, "null",
                           labels=labels, records=records, csv_export=True,
                           title="Genotypes", timepoint="", elts_to_sort=[],
                           tooltip_name=None, use_scroller=False, index=1)
            else:
                labels = ["rs_id"] + labels
                self.w(unicode(json.dumps({"labels": labels,
                                           "records": records})))

        # > export the genomic metadata reference from the selected genes
        # only
        elif export_type == "metagen":
            if metagen_snps_of_gene is not None:
                labels = ["rs_id", "chromosome", "bp_position"]
                records = []
                for gname, snps in metagen_snps_of_gene.items():
                    for snp in snps:
                        records.append([
                            gname, snp.rs_id, snp.chromosome, snp.bp_pos])
                if self._display:
                    self.wview("jtable-hugetable-clientside", None, "null",
                               labels=labels, records=records, csv_export=True,
                               title="Genotypes", timepoint="",
                               elts_to_sort=["ID", "rs_id", "chromosome"],
                               tooltip_name=None, use_scroller=False, index=2)
                else:
                    labels = ["hgnc_id"] + labels
                    self.w(unicode(json.dumps({"labels": labels,
                                               "records": records})))
            else:
                msg = (u"No genomic metadata found, please contact the "
                        "service administrator.")
                if self._display:
                    self.error(msg)
                else:
                    self.w(unicode(json.dumps({"error": msg})))
                return

    def error(self, msg):
        """ Display an error message.
        """
        self.w(u"<div class='panel panel-danger'>")
        self.w(u"<div class='panel-heading'>")
        self.w(u"<h2 class='panel-title'>ERROR</h2>")
        self.w(u"</div>")
        self.w(u"<div class='panel-body'>")
        self.w(u"<h3>{0}</h3>".format(msg))
        self.w(u"</div>")
        self.w(u"</div>")
        

class MetaGenSearchJson(MetaGenSearchView):
    """ JSON view to display the genomic measures store in PLINK format:
    bef/bim/fam files.

    See the 'MetaGenSearchView' documentation for a description of the view
    parameters.
    """
    __regid__ = "metagen-search-json"
    title = _("MetaGen Search")
    div_id = "metagen-search"
    templatable = False
    _display = False


def registration_callback(vreg):
    vreg.register(MetaGenSearchView)
    vreg.register(MetaGenSearchJson)

