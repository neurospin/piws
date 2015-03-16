#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os
import sys
import hashlib
import pygraphviz as pgv

# Cubicweb import
from cubicweb.dataimport import SQLGenObjectStore


class Base(object):
    """ This class enables us to add new entities and relations in CW.

    Attributes
    ----------
    relations: list of 3-uplet (mandatory)
        all the relations involved in schema we want to document.

    Notes
    -----
    Here is an example of the definition of the 'relations' parameter:

    ::

        relations = [
            ("CWUser", "in_group", "CWGroup")
        ]
    """
    relations = []
    assessment_relations = [
        ("Assessment", "related_study", "Study"),
        ("Subject", "concerned_by", "Assessment"),
        ("Assessment", "concerns", "Subject"),
        ("Center", "holds", "Assessment"),
        ("CWGroup", "can_read", "Assessment"),
        ("CWGroup", "can_update", "Assessment")
    ]
    fileset_relations = [
        ["ParentEntitiyName", "results_files", "FileSet"],
        ("FileSet", "in_assessment", "Assessment"),
        ("FileSet", "file_entries", "ExternalFile"),
        ("ExternalFile", "in_assessment", "Assessment") 
    ]

    def __init__(self, session, use_store=True):
        """ Initialize the SeniorData class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        list_group_names: list of str (mandatory)
            the name of the different groups
        use_store: bool (optional, default True)    
            if True use an SQLGenObjectStore, otherwise the session.
        """
        # CW parameters
        self.use_store = use_store
        self.session = session
        if self.use_store:
            self.store = SQLGenObjectStore(self.session)
            self.relate_method = self.store.relate
            self.create_entity_method = self.store.create_entity
        else:
            self.relate_method = self.session.add_relation
            self.create_entity_method = self.session.create_entity

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def cleanup(self):
        """ Method to cleanup temporary items and to commit changes.
        """
        # Send the new entities to the db
        if self.use_store:
            self.store.flush() 

    def import_data(self):
        """ Method that import the data in cw.
        """
        raise NotImplementedError("This method has to be defined in child "
                                  "class.")

    ###########################################################################
    #   Private Methods
    ###########################################################################

    def schema(self, outfname, text_font="sans-serif",
               node_text_size=12):
        """ Create a view of the schema described in a python structure.

        Parameters
        ----------
        outfname: str (mandatory)
            the path to the output file where the graph will be saved. The
            directory containing this file must be created.
        text_font: str (optional, default 'sans-serif')
            the font used to display the text in the final image.
        node_text_size: int (optional, default 12)
            the text size.      
        """
        # Create a graph
        graph = pgv.AGraph(strict=False, directed=True, rankdir="LR",
                           overlap=False)

        # Get all the entity names involved
        entities = set()
        for link in self.relations:
            entities.add(link[0])
            entities.add(link[2])

        # Go through all the entities and create a graphic table
        for entity_name in entities:
            attributes = ("cw authorized attributes")
            graph.add_node(entity_name, style="filled", fillcolor="blue",
                           fontcolor="white", fontsize=node_text_size,
                           fontname=text_font,
                           label=entity_name + "|" + attributes,
                           shape="Mrecord")

        # Relate the entities
        for link in self.relations:
            graph.add_edge(link[0], link[2], label=link[1])

        # Save the graph
        graph.draw(outfname, prog="dot")

    def _md5_sum(self, path):
        """ Create a md5 sum of a path.

        Parameters
        ----------
        path: str (madatory)
            a string to hash.

        Returns
        -------
        out: str
            the input hashed string.
        """
        m = hashlib.md5()
        m.update(path)
        return m.hexdigest()

    def _progress_bar(self, ratio, title="", bar_length=40):
        """ Method to generate a progress bar.

        Parameters
        ----------
        ratio: float (mandatory 0<ratio<1)
            float describing the current processing status.
        title: str (optional)
            a title to identify the progress bar.
        bar_length: int (optional)
            the length of the bar that will be ploted.
        """
        progress = int(ratio * 100.)
        block = int(round(bar_length * ratio))
        text = "\r{2} in Progress: [{0}] {1}%".format(
            "=" * block + " " * (bar_length - block), progress, title)
        sys.stdout.write(text)
        sys.stdout.flush()

    ###########################################################################
    #   Private Insertion Methods
    ###########################################################################

    def _set_unique_relation(self, source_eid, relation_name, detination_eid,
                             check_unicity=True, subjtype=None):
        """ Method to create a new unique relation.

        First check that the relation do not exists if 'check_unicity' is True.

        Parameters
        ----------
        source_eid: int (madatory)
            the CW identifier of the object entity in the relation.
        relation_name: str (madatory)
            the relation name.
        detination_eid: int (madatory)
            the CW identifier of the subject entity in the relation.
        check_unicity: bool (optional)
            if True check if the relation already exists in the data base.
        subjtype: str (optional)
            give the subject etype for inlined relation when using a store.
        """
        # With unicity contrain
        if check_unicity:

            # First build the rql request
            rql = "Any X Where X eid '{0}', X {1} Y, Y eid '{2}'".format(
                source_eid, relation_name, detination_eid)

            # Execute the rql request
            rset = self.session.execute(rql)

            # The request returns some data -> do nothing
            if rset.rowcount == 0:
                self.relate_method(source_eid, relation_name, detination_eid,
                                   subjtype=subjtype)

        # Without unicity constrain
        else:
            self.relate_method(source_eid, relation_name, detination_eid,
                               subjtype=subjtype)

    def _get_or_create_unique_entity(self, rql, entity_name, check_unicity=True,
                                     *args, **kwargs):
        """ Method to create a new unique entity.

        First check that the entity do not exists by executing the rql request
        if 'check_unicity' is True.

        Parameters
        ----------
        rql: str (madatory)
            the rql request to check unicity.
        entity_name: str (madatory)
            the name of the entity we want to create.
        check_unicity: bool (optional)
            if True check if the entity already exists in the data base.

        Returns
        -------
        entity: CW entity
            the requested entity.
        is_created: bool
            return True if the entity has been created, False otherwise.
        """
        # Initilize output prameter
        is_created = False

        # With unicity contrain
        if check_unicity:
            # First execute the rql request
            rset = self.session.execute(rql)

            # The request returns some data, get the unique entity
            if rset.rowcount > 0:
                if rset.rowcount > 1:
                    raise Exception("The database is corrupted, please "
                                    "investigate.")
                entity = rset.get_entity(0, 0)
            # Create a new unique entity
            else:
                entity = self.create_entity_method(entity_name, **kwargs)
                is_created = True
        # Without unicity constrain
        else:
            entity = self.create_entity_method(entity_name, **kwargs)
            is_created = True

        return entity, is_created

    def _create_assessment(self, assessment_struct, subject_eid, study_eid,
                           center_eid, groups):
        """ Create an assessment and its associated relations.

        The groups that can access the 'in_assessment' linked entities are
        generated dynamically from the assessment identifiers:

            * we '_' split the string and create a group with the first retuned
              item and the concatenation of the two first items.
            * the permissions 'can_read', 'can_update' relate the assessments
              with the corresponding groups.
        """ 
        # Create the assessment
        assessment_id = assessment_struct["identifier"]
        assessment_entity, is_created = self._get_or_create_unique_entity(
            rql=("Any X Where X is Assessment, X identifier "
                 "'{0}'".format(assessment_id)),
            check_unicity=True,
            entity_name="Assessment",
            **assessment_struct)
        assessment_eid = assessment_entity.eid
        self.inserted_assessments[assessment_id] = assessment_eid

        # If we just create the assessment, relate the entity
        if is_created:
            # > add relation with the study
            self._set_unique_relation(
                assessment_eid, "related_study", study_eid, check_unicity=False,
                subjtype="Assessment")
            # > add relation with the subject
            if subject_eid is not None:
                self._set_unique_relation(
                    subject_eid, "concerned_by", assessment_eid,
                    check_unicity=False)
                self._set_unique_relation(
                    assessment_eid, "concerns", subject_eid,
                    check_unicity=False, subjtype="Assessment")
            # > add relation with the center
            self._set_unique_relation(
                center_eid, "holds", assessment_eid, check_unicity=False)

            # Set the permissions
            # Create/get the related assessment groups
            assessment_id = assessment_id.split("_")
            related_groups = [
                assessment_id[0],
                "_".join(assessment_id[:2])
            ]
            for group_name in related_groups:

                # Check the group is created
                if group_name in groups:
                    group_eid = groups[group_name]
                else:
                    raise ValueError(
                        "Please create first the group '{0}'.".format(group_name))

                # > add relation with group
                if self.can_read:
                    self._set_unique_relation(
                        group_eid, "can_read", assessment_eid)
                if self.can_update:
                    self._set_unique_relation(
                        group_eid, "can_update", assessment_eid)
    
        return assessment_eid   

    def _import_file_set(self, fset_struct, extfiles, parent_eid,
                         assessment_eid):
        """ Add the file set attached to a parent entity.
        """
        # Create the file set
        fset_entity, _ = self._get_or_create_unique_entity(
            rql="",
            check_unicity=False,
            entity_name="FileSet",
            **fset_struct)
        # > add relation with the parent
        self._set_unique_relation(parent_eid,
            "results_files", fset_entity.eid,
            check_unicity=False)
        # > add relation with the assessment
        self._set_unique_relation(fset_entity.eid,
            "in_assessment", assessment_eid,
            check_unicity=False, subjtype="FileSet")

        # Create the external files
        for extfile_struct in extfiles:
            file_entity, _ = self._get_or_create_unique_entity(
                rql="",
                check_unicity=False,
                entity_name="ExternalFile",
                **extfile_struct)
            # > add relation with the file set
            self._set_unique_relation(fset_entity.eid,
                "file_entries", file_entity.eid,
                check_unicity=False) 
            # > add relation with the assessment
            self._set_unique_relation(file_entity.eid,
                "in_assessment", assessment_eid,
                check_unicity=False, subjtype="ExternalFile")   
