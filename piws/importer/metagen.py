##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import sys
import hashlib

# Piws import
from .base import Base


class MetaGen(Base):
    """ This class enables us to construct a bioresource with CW.
    """
    # Define the relations involved
    relations = (
        ("Chromosme", "chromosome_genes", "Gene"),
        ("Chromosme", "chromosome_snps", "Snp"),
        ("Chromosme", "chromosome_cpgs", "CpG"),
        ("CpG", "cpg_chromosome", "Chromosme"),
        ("CpG", "cpg_genes", "Gene"),
        ("Snp", "snp_chromosome", "Chromosme"),
        ("Snp", "snp_genes", "Gene"),
        ("Gene", "gene_chromosome", "Chromosme"),
        ("Gene", "gene_cpgs", "CpG"),
        ("Gene", "gene_snps", "Snp")
    )

    def __init__(self, session, use_store=True):
        """ Initialize the MetaGen class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        can_read: bool (optional, default True)
            set the read permission to the imported data.
        can_update: bool (optional, default True)
            set the update permission to the imported data.
        use_store: bool (optional, default True)
            if True use an SQLGenObjectStore, otherwise the session.
        piws_security_model: bool (optional, default True)
            if True apply the PIWS security model.

        """
        # Inheritance
        super(MetaGen, self).__init__(
            session=session,
            can_read=True,
            can_update=True,
            use_store=use_store,
            piws_security_model=False)

        # Speed up parameters
        self.inserted_genes = {}

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self, chromosome_name, genes, cpgs, snps):
        """ Method that import one chromsome bioresource data in the db.

        Parameters
        ----------
        chromosome_name: str
            the chromosome name that will be inserted.
        genes: list of list
            each element is composed of [[id, related_chromosome, start, end,
            hgnc_id, type], ...].
        cpgs: list of list
            each element is composed of [[cg_id, related_chromosome, position,
            related_genes], ...].
        snps: list of list
            each element is composed of [[rs_id, related_chromsome, start, end,
            maf, related_genes], ...].

        .. note::

            Below the schema used to insert the bioresource data:

            |

            .. image:: ../schemas/bioresource.png
                :width: 600px
                :align: center
                :alt: schema
        """

        #######################################################################
        # Insert the chromosome
        #######################################################################

        if not isinstance(chromosome_name, basestring):
            chromosome_name = str(chromosome_name)
        chromosome_entity, _ = self._get_or_create_unique_entity(
            rql=("Any X Where X is Chromosome, X name '{0}'".format(
                chromosome_name)),
            entity_name="Chromosome",
            identifier=unicode(self._md5_sum(chromosome_name)),
            name=unicode(chromosome_name))
        chromosome_eid = chromosome_entity.eid

        #######################################################################
        # Insert all the genes
        #######################################################################

        nb_genes = float(len(genes))
        for cnt, gene_struct in enumerate(genes, start=1):

            # Unpack
            gid, related_chromosome, start, end, hgnc_id, gtype = gene_struct

            # Progress
            self._progress_bar(
                cnt / nb_genes,
                title="{0}(genes)".format(hgnc_id),
                bar_length=40)

            # Create entity
            gene_entity, is_created = self._get_or_create_unique_entity(
                rql=("Any X Where X is Gene, X gene_id '{0}'".format(gid)),
                entity_name="Gene",
                hgnc_id=unicode(hgnc_id),
                gene_id=unicode(gid),
                start_position=start,
                end_position=end,
                type=unicode(gtype))
            gene_eid = gene_entity.eid
            self.inserted_genes[gid] = gene_eid

            # Create relations
            if is_created:
                self._set_unique_relation(
                    gene_eid, "gene_chromosome", chromosome_eid,
                    check_unicity=False)
                self._set_unique_relation(
                    chromosome_eid, "chromosome_genes", gene_eid,
                    check_unicity=False)

        print  # new line after last progress bar update

        #######################################################################
        # Insert CpGs (methylation loci)
        #######################################################################

        nb_cpgs = float(len(cpgs))
        for cnt, cpg_struct in enumerate(cpgs, start=1):

            # Unpack
            cg_id, related_chromosome, position, related_genes = cpg_struct

            # Progress
            self._progress_bar(
                cnt / nb_cpgs,
                title="{0}(spgs)".format(cg_id),
                bar_length=40)

            # Create entity
            cpg_entity, is_created = self._get_or_create_unique_entity(
                rql=("Any X Where X is CpG, X cg_id '{0}'".format(cg_id)),
                entity_name="CpG",
                cg_id=unicode(cg_id),
                position=position)
            cpg_eid = cpg_entity.eid

            # Create relations
            if is_created:
                self._set_unique_relation(
                    cpg_eid, "cpg_chromosome", chromosome_eid,
                    check_unicity=False)
                self._set_unique_relation(
                    chromosome_eid, "chromosome_cpgs", cpg_eid,
                    check_unicity=False)
                for gene_id in related_genes:
                    gene_eid = self.inserted_genes[gene_id]
                    self._set_unique_relation(
                        gene_eid, "gene_cpgs", cpg_eid,
                        check_unicity=False)
                    self._set_unique_relation(
                        cpg_eid, "cpg_genes", gene_eid,
                        check_unicity=False)

        print  # new line after last progress bar update

        #######################################################################
        # Insert all the SNPs
        #######################################################################

        nb_snps = float(len(snps))
        for cnt, snp_struct in enumerate(snps, start=1):

            # Unpack
            rs_id, related_chromosome, start, end, maf, related_genes = snp_struct

            # Progress
            self._progress_bar(
                cnt / nb_snps,
                title="{0}(snps)".format(rs_id),
                bar_length=40)

            # Create entity
            snp_entity, is_created = self._get_or_create_unique_entity(
                rql=("Any X Where X is Snp, X rs_id '{0}'".format(rs_id)),
                entity_name="Snp",
                rs_id=unicode(rs_id),
                start_position=start,
                end_position=end,
                maf=maf)
            snp_eid = snp_entity.eid

            # Create relations
            if is_created:
                self._set_unique_relation(
                    snp_eid, "snp_chromosome", chromosome_eid,
                    check_unicity=False)
                self._set_unique_relation(
                    chromosome_eid, "chromosome_snps", snp_eid,
                    check_unicity=False)
                for gene_id in related_genes:
                    gene_eid = self.inserted_genes[gene_id]
                    self._set_unique_relation(
                        gene_eid, "gene_snps", snp_eid,
                        check_unicity=False)
                    self._set_unique_relation(
                        snp_eid, "snp_genes", gene_eid,
                        check_unicity=False)

        print  # new line after last progress bar update

