##########################################################################
# NSAp - Copyright (C) CEA, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

from __future__ import print_function

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
        ("Chromosome", "chromosome_cpg_islands", "CpGIsland"),
        ("Gene", "gene_chromosome", "Chromosome"),
        ("Gene", "gene_cpgs", "CpG"),
        ("Gene", "gene_snps", "Snp"),
        ("Gene", "gene_cpg_islands", "CpGIsland"),
        ("Gene", "gene_pathways", "Pathway"),
        ("CpG", "cpg_chromosome", "Chromosme"),
        ("CpG", "cpg_genes", "Gene"),
        ("CpG", "cpg_cpg_island", "CpGIsland"),
        ("Snp", "snp_chromosome", "Chromosome"),
        ("Snp", "snp_genes", "Gene"),
        ("CpGIsland", "cpg_island_chromosome", "Chromosome"),
        ("CpGIsland", "cpg_island_cpgs", "CpG"),
        ("CpGIsland", "cpg_island_genes", "Gene"),
        ("Pathway", "pathway_genes", "Gene")
    )

    def __init__(self, session, store_type="RQL"):
        """ Initialize the MetaGen class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        can_read: bool (optional, default True)
            set the read permission to the imported data.
        can_update: bool (optional, default True)
            set the update permission to the imported data.
        store_type: str (optional, default 'RQL')
            Must be in ['RQL', 'SQL', 'MASSIVE'].
            'RQL' to use session, 'SQL' to use SQLGenObjectStore, or 'MASSIVE'
            to use MassiveObjectStore.
        piws_security_model: bool (optional, default True)
            if True apply the PIWS security model.

        """
        # Inheritance
        super(MetaGen, self).__init__(
            session=session,
            can_read=True,
            can_update=True,
            store_type=store_type,
            piws_security_model=False)

        self.STORE_TYPES = {"RQL", "MASSIVE"}
        if store_type not in self.STORE_TYPES:
            raise ValueError("store_type not handled: {}, possible values: {}"
                             .format(store_type, self.STORE_TYPES))

        # Pathways are across chromosomes, but import is done chromosome by
        # chromosome, we need to keep the mapping <pathway name> -> entity ID
        # to make relations with genes, and to known which pathways have
        # already been inserted without making request (too slow).
        self.eid_of_pathway = dict()

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def commit_without_finishing(self):
        """
        Commit changes but do not finish. Used to flush/commit regularly, it
        helps with detecting errors more rapidly and it can help with the
        RAM consumption (depending on the choice of store_type).
        """
        if self.store_type == "MASSIVE":
            self.store.flush()
            self.store.commit()
        elif self.store_type == "RQL":
            self.session.commit()
        else:
            raise ValueError("store_type not handled: %s." % self.store_type)

    def import_data(self, chromosome_name, genes, gene_pathways, cpg_islands,
                    cpgs, snps):
        """ Method that import one chromsome data in the database.

        Parameters
        ----------
        chromosome_name: str
            the chromosome name that will be inserted.
        genes: list of list
            [[gene_id, chromosome, start, end, hgnc_name, gene_type], ...]
        cpg_islands: list of list
            [[chromosome, start, end], ...]
        cpgs: list of list
            [[cg_id, chromosome, position, related_genesn cpg_island_id], ...]
        snps: list of list
            [[rs_id, chromsome, start, end, maf, related_genes], ...]

        .. note::

            Below the schema used to insert the MetaGen data:

            |

            .. image:: ../schemas/bioresource.png
                :width: 600px
                :align: center
                :alt: schema
        """

        print("Chromosome %s" % chromosome_name)

        #######################################################################
        # Insert the chromosome
        #######################################################################

        if not isinstance(chromosome_name, basestring):
            chromosome_name = str(chromosome_name)
        chromosome_entity, is_created = self._get_or_create_unique_entity(
            rql="Any X Where X is Chromosome, X name '{0}'".format(
                chromosome_name),
            entity_name="Chromosome",
            identifier=unicode(self._md5_sum(chromosome_name)),
            name=unicode(chromosome_name))
        chromosome_eid = chromosome_entity.eid

        assert is_created
        self.commit_without_finishing()

        #######################################################################
        # Insert the genes and related pathways
        #######################################################################

        # Keep gene eids to make relations with CpGs and SNPs
        # Map <gene_id> -> <gene eid>
        eid_of_gene = dict()

        nb_genes = len(genes)
        for cnt, gene_struct in enumerate(genes, start=1):

            # Unpack
            (gene_id, chrom, start, end, hgnc_name, gene_type,
                related_pathways) = gene_struct
            assert chrom == chromosome_name

            # Create entity
            gene_entity, is_created = self._get_or_create_unique_entity(
                rql="Any X Where X is Gene, X gene_id '{0}'".format(gene_id),
                entity_name="Gene",
                hgnc_name=unicode(hgnc_name),
                gene_id=unicode(gene_id),
                start_position=start,
                end_position=end,
                gene_type=unicode(gene_type))
            gene_eid = gene_entity.eid
            eid_of_gene[gene_id] = gene_eid
            assert is_created

            # Create relations to chromosome
            self._set_unique_relation(gene_eid, "gene_chromosome",
                                      chromosome_eid, check_unicity=False)
            self._set_unique_relation(chromosome_eid, "chromosome_genes",
                                      gene_eid, check_unicity=False)

            # Handle related pathways
            for pathway_name in related_pathways:

                # If pathway has not been inserted: create pathway entity
                if pathway_name not in self.eid_of_pathway:
                    pathway_entity, is_created = (
                        self._get_or_create_unique_entity(
                            rql=("Any X Where X is Pathway, X name '%s'"
                                 % pathway_name),
                            entity_name="Pathway",
                            name=unicode(pathway_name),
                            uri=unicode(gene_pathways[pathway_name])))
                    assert is_created

                    # Keep mapping: <pathway name> -> <eid>
                    self.eid_of_pathway[pathway_name] = pathway_entity.eid

                # Relate pathway to gene
                pathway_eid = self.eid_of_pathway[pathway_name]
                self._set_unique_relation(gene_eid, "gene_pathways",
                                          pathway_eid)
                self._set_unique_relation(pathway_eid, "pathway_genes",
                                          gene_eid)

            # Progress
            if cnt % 10 == 0 or cnt == nb_genes:
                self._progress_bar(
                    cnt / float(nb_genes),
                    title="(genes) %i/%i [%s]" % (cnt, nb_genes, hgnc_name),
                    bar_length=40)

        print()  # new line after last progress bar update

        self.commit_without_finishing()

        #######################################################################
        # Insert CpGIslands (Genomic region with many CpGs)
        #######################################################################

        # Keep CpG island eids to make relations with CpGs
        # Map <CpG island id> -> <eid>
        eid_of_cpg_island = dict()

        nb_cpg_islands = len(cpg_islands)

        for cnt, cpg_island_struct in enumerate(cpg_islands, start=1):

            # Unpack
            chrom, start, end, related_genes = cpg_island_struct
            assert chrom == chromosome_name
            cpg_island_id = "chr%s:%i:%i" % (chrom, start, end)

            # Create entity
            cpg_island_entity, is_created = self._get_or_create_unique_entity(
                rql=("Any X Where X is CpGIsland, "
                     "X cpg_island_id '{0}'".format(cpg_island_id)),
                entity_name="CpGIsland",
                cpg_island_id=unicode(cpg_island_id),
                start_position=start,
                end_position=end)
            cpg_island_eid = cpg_island_entity.eid
            eid_of_cpg_island[cpg_island_id] = cpg_island_eid

            # Create relations to chromosome
            assert is_created
            self._set_unique_relation(cpg_island_eid, "cpg_island_chromosome",
                                      chromosome_eid, check_unicity=False)
            self._set_unique_relation(chromosome_eid, "chromosome_cpg_islands",
                                      cpg_island_eid, check_unicity=False)
            # Create relations to genes
            for gene_id in related_genes:
                gene_eid = eid_of_gene[gene_id]
                self._set_unique_relation(cpg_island_eid, "cpg_island_genes",
                                          gene_eid, check_unicity=False)
                self._set_unique_relation(gene_eid, "gene_cpg_islands",
                                          cpg_island_eid, check_unicity=False)

            # Progress
            if cnt % 100 == 0 or cnt == nb_cpg_islands:
                self._progress_bar(
                    cnt / float(nb_cpg_islands),
                    title="(CpG islands) %i/%i [%s]" % (cnt, nb_cpg_islands,
                                                        cpg_island_id),
                    bar_length=40)

        print()  # new line after last progress bar update

        self.commit_without_finishing()

        #######################################################################
        # Insert CpGs (methylation loci)
        #######################################################################

        nb_cpgs = len(cpgs)
        for cnt, cpg_struct in enumerate(cpgs, start=1):

            # Unpack
            cg_id, chrom, position, related_genes, cpg_island_id = cpg_struct
            assert chrom == chromosome_name

            # Create entity
            cpg_entity, is_created = self._get_or_create_unique_entity(
                rql="Any X Where X is CpG, X cg_id '{0}'".format(cg_id),
                entity_name="CpG",
                cg_id=unicode(cg_id),
                position=position)
            cpg_eid = cpg_entity.eid

            # Create relations to chromosome
            assert is_created
            self._set_unique_relation(cpg_eid, "cpg_chromosome",
                                      chromosome_eid, check_unicity=False)
            self._set_unique_relation(chromosome_eid, "chromosome_cpgs",
                                      cpg_eid, check_unicity=False)
            # Create relations to CpGIsland, if a link exists
            if cpg_island_id is not None:
                cpg_island_eid = eid_of_cpg_island[cpg_island_id]
                self._set_unique_relation(cpg_eid, "cpg_cpg_island",
                                          cpg_island_eid, check_unicity=False)
            # Create relations to genes
            for gene_id in related_genes:
                gene_eid = eid_of_gene[gene_id]
                self._set_unique_relation(gene_eid, "gene_cpgs", cpg_eid,
                                          check_unicity=False)
                self._set_unique_relation(cpg_eid, "cpg_genes", gene_eid,
                                          check_unicity=False)

            # Progress
            if cnt % 100 == 0 or cnt == nb_cpgs:
                self._progress_bar(
                    cnt / float(nb_cpgs),
                    title="(CpGs) %i/%i [%s]" % (cnt, nb_cpgs, cg_id),
                    bar_length=40)

            # Regularly flush and/or commit for RAM consumption
            if cnt % 10000 == 0 or cnt == nb_cpgs:
                self.commit_without_finishing()

        print()  # new line after last progress bar update

        #######################################################################
        # Insert all the SNPs
        #######################################################################

        nb_snps = len(snps)
        for cnt, snp_struct in enumerate(snps, start=1):

            # Unpack
            rs_id, chrom, pos, maf, related_genes = snp_struct
            assert chrom == chromosome_name

            # Create entity
            snp_entity, is_created = self._get_or_create_unique_entity(
                rql="Any X Where X is Snp, X rs_id '{0}'".format(rs_id),
                entity_name="Snp",
                rs_id=unicode(rs_id),
                position=pos,
                maf=maf)
            snp_eid = snp_entity.eid

            # Create relations to chromosome
            assert is_created
            self._set_unique_relation(snp_eid, "snp_chromosome",
                                      chromosome_eid, check_unicity=False)
            self._set_unique_relation(chromosome_eid, "chromosome_snps",
                                      snp_eid, check_unicity=False)
            # Create relations to genes
            for gene_id in related_genes:
                gene_eid = eid_of_gene[gene_id]
                self._set_unique_relation(gene_eid, "gene_snps", snp_eid,
                                          check_unicity=False)
                self._set_unique_relation(snp_eid, "snp_genes", gene_eid,
                                          check_unicity=False)

            # Progress
            if cnt % 100 == 0 or cnt == nb_snps:
                self._progress_bar(
                    cnt / float(nb_snps),
                    title="(SNPs) %i/%i [%s]" % (cnt, nb_snps, rs_id),
                    bar_length=40)

            # Regularly flush and/or commit for RAM consumption
            if cnt % 10000 == 0 or cnt == nb_snps:
                self.commit_without_finishing()

        print()  # new line after last progress bar update
