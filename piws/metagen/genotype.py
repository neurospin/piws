##########################################################################
# NSAp - Copyright (C) CEA, 2017
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Standard import
import getpass
from collections import namedtuple

# Third-party import
from pysnptools.snpreader import Bed
from cwbrowser.cw_connection import CWInstanceConnection


DEFAULT_METAGEN_URL = "http://mart.intra.cea.fr/metagen_hg38_dbsnp149"


def connect_metagen_server(login=None, password=None,
                           metagen_url=DEFAULT_METAGEN_URL):
    """
    Create a connection to a Metagen server. The login and password are
    requested interactively if not provided.
    """
    if login is None:
        login = raw_input("\nMetagen login: ")
    if password is None:
        password = getpass.getpass("Metagen password: ")
    metagen_connection = CWInstanceConnection(url=metagen_url,
                                              login=login,
                                              password=password)
    return metagen_connection


def metagen_get_genes(metagen_connection=None,
                      metagen_url=DEFAULT_METAGEN_URL,
                      timeout=10,
                      nb_tries=3):
    """
    Get all the gene names by requesting the Metagen server.

    The user can provide a Metagen connection, otherwise it is created by
    interactively requesting a login and a password.

    Parameters
    ----------
    metagen_connection: CWInstanceConnection, default None
        A connection to the Metagen server. Created if not passed.
    metagen_url: str, default module url
        Url of the Metagen server. Ignored if a connection to the Metagen
        server is passed.
    timeout: int, default 10
        Max time in seconds to wait for a response from Metagen.
    nb_tries: int, default 3
        If the server failed to answer, retry nb_tries-1 times.

    Return
    ------
    hgnc_name, chromosome: list
    """
    # If not passed, create a connection to the Metagen server
    if metagen_connection is None:
        metagen_connection = connect_metagen_server(metagen_url=metagen_url)

    rql = ("Any GN, CN Where G is Gene, G hgnc_name GN, G gene_chromosome C, "
           "C name CN")
    rset = metagen_connection.execute(rql, timeout=timeout, nb_tries=nb_tries)

    # Return genes as namedtuples to simplify usage
    Gene = namedtuple("Gene", ["hgnc_name", "chromosome"])
    genes = [Gene(name, chrom) for name, chrom in rset]

    return genes


def metagen_get_snps_of_gene(gene_name,
                             metagen_connection=None,
                             metagen_url=DEFAULT_METAGEN_URL,
                             timeout=10,
                             nb_tries=3):
    """
    Get SNP IDs and associated metadata (chromosome and positions) associated
    to a gene by requesting the Metagen server.

    The user can provide a Metagen connection, otherwise it is created by
    interactively requesting a login and a password.

    Parameters
    ----------
    gene_name: str
        Gene HGNC name.
    metagen_connection: CWInstanceConnection, default None
        A connection to the Metagen server. Created if not passed.
    metagen_url: str, default module url
        Url of the Metagen server. Ignored if a connection to the Metagen
        server is passed.
    timeout: int, default 10
        Max time in seconds to wait for a response from Metagen.
    nb_tries: int, default 3
        If the server failed to answer, retry nb_tries-1 times.

    Return
    ------
    snp_ids, chromosomes, bp_positions: list
    """
    # If not passed, create a connection to the Metagen server
    if metagen_connection is None:
        metagen_connection = connect_metagen_server(metagen_url=metagen_url)

    rql = ("Any SID, CN, POS Where G is Gene, G hgnc_name '%s', "
           "G gene_snps S, S rs_id SID, S snp_chromosome C, "
           "C name CN, S position POS") % gene_name
    rset = metagen_connection.execute(rql, timeout=timeout, nb_tries=nb_tries)

    # Return SNPs as namedtuples to simplify usage
    Snp = namedtuple("Snp", ["rs_id", "chromosome", "position"])
    snps = [Snp(rs_id, chrom, pos) for rs_id, chrom, pos in rset]

    # Sort by genomic position
    snps.sort(key=lambda snp: snp.position)

    return snps


def metagen_get_snps_of_genes(gene_names,
                              metagen_connection=None,
                              metagen_url=DEFAULT_METAGEN_URL,
                              timeout=10,
                              nb_tries=3):
    """
    Get IDs and associated metadata (position, chromosome) of SNPs associated
    to a list of genes by requesting the Metagen server.

    The user can provide a Metagen connection, otherwise it is created by
    interactively requesting a login and a password.

    Parameters
    ----------
    gene_names: list of str
        Gene names are the HGNC names.
    metagen_connection: CWInstanceConnection, default None
        A connection to the Metagen instance. Created if not passed.
    metagen_url: str, default module url
        Url of the Metagen server. Ignored if a connection to the Metagen
        server is passed.
    timeout: int, default 10
        Max time in seconds to wait for a response from Metagen.
    nb_tries: int, default 3
        If the server failed to answer, retry nb_tries-1 times.

    Return
    ------
    snps_of_gene; dict
        Map <gene HGNC name> -> list of SNPs.
        Each SNP is a namedtuple: (<rs_id>, <chromosome>, <pos>)
    """
    # If not passed, create a connection to the Metagen server
    if metagen_connection is None:
        metagen_connection = connect_metagen_server(metagen_url=metagen_url)

    # Remove redundancy
    gene_names = list(set(gene_names))

    # Dict mapping <gene HGNC name> -> list of snps
    # Each snp is given as a namedtuple: (<rs_id>, <chromosome>, <bp_pos>)
    snps_of_gene = dict()

    # For each gene, request the associated snps and the their metadata
    for gname in gene_names:
        snps = metagen_get_snps_of_gene(gene_name=gname,
                                        metagen_connection=metagen_connection,
                                        metagen_url=DEFAULT_METAGEN_URL,
                                        timeout=timeout,
                                        nb_tries=nb_tries)
        snps_of_gene[gname] = snps

    return snps_of_gene


def metagen_get_meta_of_snps(snp_ids,
                             metagen_connection=None,
                             metagen_url=DEFAULT_METAGEN_URL,
                             timeout=10,
                             nb_tries=3):
    """
    Get SNP metadata from rs IDs: chromosome, basepair position, related
    genes by requesting the Metagen server.

    Calling the metagen_meta_of_snp() funtion SNP by SNP could take long
    for thousands of variants, this function is optimized to request metadata
    of many SNPs at once.

    The user can provide a Metagen connection, otherwise it is created.

    Parameters
    ----------
    snp_ids: list of str
        List of SNP rs ids.
    metagen_connection: CWInstanceConnection, default None
        A connection to the Metagen instance. Created if not passed.
    metagen_url: str, default module url
        Url of the Metagen server. Ignored if a connection to the Metagen
        server is passed.
    timeout: int, default 10
        Max time in seconds to wait for a response from Metagen.
    nb_tries: int, default 3
        If the server failed to answer, retry nb_tries-1 times.

    Return
    ------
    meta_of_snp; dict
        Map <rs id> -> namedtuple("rs_id", "chromosome", "position", "maf",
                                  "genes").
    """
    # If not passed, create a connection to the Metagen server
    if metagen_connection is None:
        metagen_connection = connect_metagen_server(metagen_url=metagen_url)

    # Remove redundancy
    snp_ids = list(set(snp_ids))

    # Namedtuple to store SNP metadata
    Snp = namedtuple("Snp", ["rs_id", "chromosome", "position", "maf",
                     "genes"])

    # Dict mapping <rs id> -> Snp namedtuple
    meta_of_snp = dict()

    # Request metadata from Metagen: requesting N variants at a time
    # (one by one would take too long when there are many variants).
    # The requesting is done is 2 steps: request chrom, start and then
    # request associated genes, because not all SNPs are associated to genes.
    N = 5000
    common_kwargs = dict(timeout=timeout, nb_tries=nb_tries)
    for i in range(0, len(snp_ids), N):
        subset_snp_ids = snp_ids[i: i+N]
        # Note that we use a complicated "' ,'".join() in the RQL creation
        # instead of str(tuple()). When there is only one SNP id, str(tuple())
        # introduces a trailing comma which is not allowed in RQL
        rql_1 = ("Any SID, CN, SPOS, EPOS, MAF WHERE S is Snp, "
                 "S rs_id IN ('%s'), S rs_id SID, S snp_chromosome C, "
                 "C name CN, S position SPOS, "
                 "S maf MAF") % "' ,'".join(subset_snp_ids)
        rset_1 = metagen_connection.execute(rql_1, **common_kwargs)
        for rs_id, chrom, pos, maf in rset_1:
            meta_of_snp[rs_id] = Snp(rs_id=rs_id,
                                     chromosome=chrom,
                                     position=pos,
                                     maf=maf,
                                     genes=set())

        # Look for gene-SNP assocation
        rql_2 = ("Any SID, GN WHERE S is Snp, S rs_id IN ('%s'), S rs_id SID, "
                 "S snp_genes G, G hgnc_name GN") % "' ,'".join(subset_snp_ids)
        rset_2 = metagen_connection.execute(rql_2, **common_kwargs)
        for snp_id, gname in rset_2:
            meta_of_snp[snp_id].genes.add(gname)

    return meta_of_snp


def load_plink_bed_bim_fam_dataset(path_dataset, snp_ids=None,
                                   subject_ids=None, count_A1=True):
    """
    Load a Plink bed/bim/fam dataset as a SnpData instance. Optionnally a
    specific list of snps or subjects can be extracted to avoid loading
    everything in memory.

    Parameters
    ----------
    path_dataset: str
        Path to the Plink bed/bim/fam dataset, with or without .bed extension.
    snp_ids: list/set of str, default None
        Snps that should be extracted if available in the dataset.
        By default None, all snps are loaded.
    subject_ids: list of str, default None
        Subjects that should be extracted if available in the dataset.
        By default None, all subjects are loaded.
    count_A1: bool, default True
        Genotypes are provided as allele counts, A1 if True else A2.

    Return
    ------
    snp_data: pysnptools object
        PLINK data loaded by the 'pysnptools' library.
    """

    # Load the metadata, without loading the genotypes
    snp_data = Bed(path_dataset, count_A1=count_A1)

    # If requested, filter on snp ids
    if snp_ids is not None:
        snp_ids = set(snp_ids)
        snp_bool_indexes = [(s in snp_ids) for s in snp_data.sid]
        snp_data = snp_data[:, snp_bool_indexes]

    # If requested, filter on subject ids
    if subject_ids is not None:
        subject_ids = set(subject_ids)
        subject_bool_indexes = [(s in subject_ids) for s in snp_data.iid[:, 1]]
        snp_data = snp_data[subject_bool_indexes, :]

    # Load the genotypes from the Plink dataset
    snp_data = snp_data.read()

    return snp_data


def genotype_measure(path_dataset, snp_ids=None, gene_names=None,
                     subject_ids=None, count_A1=True, path_log=None,
                     timeout=10, nb_tries=3, metagen_url=DEFAULT_METAGEN_URL):
    """
    Request genotype data from a Plink bed/bim/fam dataset. It can be done
    using high level attributes like genes. In that case the function requests
    the Metagen server to translate these high level attributes to a list of
    snp ids.

    Parameters
    ----------
    path_dataset: str
        Path to the Plink bed/bim/fam dataset, with or without .bed extension.
    snp_ids: list/set of str, default None
        Snps that should be extracted if available in the dataset.
        If both snp_ids and gene_names are None, all snps are loaded.
    gene_names: list/set of str, default None
        Names of genes for which the snps are requested.
        If both snp_ids and gene_names are None, all snps are loaded.
    subject_ids: list/set of str, default None
        Subjects that should be extracted if available in the dataset.
        By default None, all subjects are loaded.
    count_A1: bool, default True
        Genotypes are provided as allele counts, A1 if True else A2.
    path_log: str, default None
        TODO: code and documentation
    timeout: int, default 10
        Max time in seconds to wait for a response from Metagen.
    nb_tries: int, default 3
        If the server failed to answer, retry nb_tries-1 times.

    Return
    ------
    dataframe: Pandas MultiIndexed DataFrame
        Plink data and metadata.
    metagen_snps_of_gene: dict or None
        None if 'gene_names' was not passed. Otherwise returns a dict of the
        Metagen results. It maps <gene HGNC name> -> list of snps.
        Each snp is given as a namedtuple: (<rs_id>, <chromosome>, <bp_pos>).
        Note that there will probably be much more snps in the dict than in
        the dataframe, since the dataframe only contain snps available in the
        dataset.
    """
    if gene_names is not None:
        metagen_snps_of_gene = metagen_get_snps_of_genes(
            gene_names=gene_names,
            metagen_url=metagen_url,
            timeout=timeout,
            nb_tries=nb_tries)
        metagen_snp_ids = [snp.rs_id for snps in metagen_snps_of_gene.values()
                           for snp in snps]
        if len(metagen_snp_ids) == 0:
            raise ValueError("Metagen returned 0 snp for the requested genes.")
        else:
            snp_ids = (snp_ids or []) + metagen_snp_ids
    else:
        metagen_snps_of_gene = None

    # Load the genotypes
    dataframe = load_plink_bed_bim_fam_dataset(path_dataset=path_dataset,
                                               snp_ids=snp_ids,
                                               subject_ids=subject_ids,
                                               count_A1=count_A1)
    return dataframe, metagen_snps_of_gene
