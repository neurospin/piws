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
from packaging import version
from argparse import Namespace

# Cubicweb import
import cubicweb
from cubicweb.dataimport import SQLGenObjectStore
from logilab.common.decorators import monkeypatch

# In higher cubiweb version pass the kwargs to the 'add_relation' method in the
# 'prepare_insert_relation' method.
cw_version = version.parse(cubicweb.__version__)
if cw_version >= version.parse("3.21.0"):

    from cubicweb.dataimport.stores import NoHookRQLObjectStore


    @monkeypatch(NoHookRQLObjectStore)
    def prepare_insert_relation(self, eid_from, rtype, eid_to, **kwargs):
        """ Insert into the database a  relation ``rtype`` between entities
        with eids ``eid_from`` and ``eid_to``.
        """
        assert not rtype.startswith("reverse_")
        rschema = self._rschema(rtype)
        self._add_relation(self._cnx, eid_from, rtype, eid_to, rschema.inlined,
                           **kwargs)
        if rschema.symmetric:
            self._add_relation(self._cnx, eid_to, rtype, eid_from,
                               rschema.inlined, **kwargs)
        self._nb_inserted_relations += 1



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
        ("Assessment", "study", "Study"),
        ("Study", "assessments", "Assessment"),
        ("Subject", "assessments", "Assessment"),
        ("Assessment", "subjects", "Subject"),
        ("Center", "assessments", "Assessment"),
        ("Assessment", "center", "Center"),
        ("CWGroup", "can_read", "Assessment"),
        ("CWGroup", "can_update", "Assessment"),
        ("Assessment", "device", "Device"),
        ("Device", "device_assessments", "Assessment")
    ]
    fileset_relations = [
        ["ParentEntitiyName", "filesets", "FileSet"],
        ("FileSet", "in_assessment", "Assessment"),
        ("FileSet", "external_files", "ExternalFile"),
        ("ExternalFile", "fileset", "FileSet"),
        ("ExternalFile", "in_assessment", "Assessment")
    ]
    device_relations = fileset_relations + [
        ("Device", "center", "Center")
    ]
    device_relations[0][0] = "Device"

    def __init__(self, session, can_read=True, can_update=False,
                 store_type="RQL", piws_security_model=True):
        """ Initialize the SeniorData class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        can_read: bool (optional, default True)
            set the read permission to the imported data.
        can_update: bool (optional, default False)
            set the update permission to the imported data.
        store_type: str (optional, default 'RQL')
            Must be in ['RQL', 'SQL', 'MASSIVE'].
            'RQL' to use session, 'SQL' to use SQLGenObjectStore, or 'MASSIVE'
            to use MassiveObjectStore.
        piws_security_model: bool (optional, default True)
            if True apply the PIWS security model.
        """
        # Check input parameters
        if store_type not in ["RQL", "SQL", "MASSIVE"]:
            raise Exception("Store type must be in ['RQL', 'SQL', 'Massive'].")

        # Massive store is supported for CW version > 3.24
        if store_type == "MASSIVE":
            if cw_version < version.parse("3.24.0"):
                raise ValueError("Massive store not supported for CW version "
                                 "{0}.".format(cw_version))
            else:
                from cubicweb.dataimport.massive_store import MassiveObjectStore

        # CW parameters
        self.can_read = can_read
        self.can_update = can_update
        self.store_type = store_type
        self.session = session
        if self.store_type == "SQL":
            self.store = SQLGenObjectStore(self.session)
            if cw_version >= version.parse("3.21.0"):
                self.relate_method = self.store.prepare_insert_relation
            else:
                self.relate_method = self.store.relate
            if cw_version >= version.parse("3.21.0"):
                self.create_entity_method = self.prepare_insert_entity
            else:
                self.create_entity_method = self.store.create_entity
        elif self.store_type == "MASSIVE":
            self.store = MassiveObjectStore(self.session)
            self.relate_method = self.store.prepare_insert_relation
            self.create_entity_method = self.prepare_insert_entity
        else:
            self.relate_method = self.session.add_relation
            self.create_entity_method = self.session.create_entity
        self.piws_security_model = piws_security_model

        # Speed up parameters
        self.inserted_assessments = {}
        self.inserted_devices = {}
        self.already_related_subjects = {}

    ###########################################################################
    #   Public Methods
    ###########################################################################
    def prepare_insert_entity(self, *args, **kwargs):
        """Returns a dummy CW object with only the eid specified.
        """
        entity = Namespace()
        entity.eid = self.store.prepare_insert_entity(*args, **kwargs)
        return entity

    def cleanup(self):
        """ Method to cleanup temporary items and to commit changes.
        """
        # Send the new entities to the db
        if self.store_type in ["SQL", "MASSIVE"]:
            self.store.flush()
            self.store.commit()
            if hasattr(self.store, "finish"):
                self.store.finish()
        else:
            self.session.commit()

    def import_data(self):
        """ Method that import the data in cw.
        """
        raise NotImplementedError("This method has to be defined in child "
                                  "class.")

    ###########################################################################
    #   Private Methods
    ###########################################################################

    @classmethod
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
        import pygraphviz

        # Create a graph
        graph = pygraphviz.AGraph(strict=False, directed=True,
                                  rankdir="LR", overlap=False)

        # Get all the entity names involved
        entities = set()
        for link in self.relations:
            entities.add(link[0])
            entities.add(link[2])

        # Go through all the entities and create a graphic table
        for entity_name in entities:
            attributes = ("CW authorized attributes")
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
        m.update(path.encode("utf-8"))
        return m.hexdigest()

    def _progress_bar(self, ratio, title="", bar_length=40, maxsize=20):
        """ Method to generate a progress bar.

        Parameters
        ----------
        ratio: float (mandatory 0<ratio<1)
            float describing the current processing status.
        title: str (optional)
            a title to identify the progress bar.
        bar_length: int (optional)
            the length of the bar that will be ploted.
        maxsize: int (optional)
            use to justify title.
        """
        progress = int(ratio * 100.)
        block = int(round(bar_length * ratio))
        title = title.ljust(maxsize, " ")
        text = "\r[{0}] {1}% {2}".format(
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
                if self.store_type == "SQL":
                    self.relate_method(source_eid, relation_name,
                                       detination_eid, subjtype=subjtype)
                else:
                    self.relate_method(source_eid, relation_name,
                                       detination_eid)

        # Without unicity constrain
        else:
            if self.store_type == "SQL":
                self.relate_method(source_eid, relation_name, detination_eid,
                                   subjtype=subjtype)
            else:
                self.relate_method(source_eid, relation_name, detination_eid)

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

    def _create_device(self, device_struct, center_eid, assessment_eid,
                       center_name):
        """ Create a device and its associated relations.
        """
        # Create the device
        device_id = device_struct["identifier"]
        extfiles = device_struct.pop("ExternalResources")
        device_entity, is_created = self._get_or_create_unique_entity(
            rql=("Any X Where X is Device, X identifier "
                 "'{0}'".format(device_id)),
            check_unicity=True,
            entity_name="Device",
            **device_struct)
        device_eid = device_entity.eid
        self.inserted_devices[device_id] = device_eid

        # If we just create the device, relate the entity
        if is_created:
            # > add relation with the center
            self._set_unique_relation(
                device_eid, "center", center_eid, check_unicity=False)
            # > add relation with the exam cards
            if len(extfiles) > 0:
                fset_struct = {
                    "identifier": device_id,
                    "name": u"{0} exam {1} card".format(
                        center_name, device_struct["manufacturer"])}
                self._import_file_set(fset_struct, extfiles, device_eid,
                                      assessment_eid)

        return device_eid

    def _create_assessment(self, assessment_struct, subject_eids, study_eid,
                           center_eid, groups):
        """ Create an assessment and its associated relations.

        The groups that can access the 'in_assessment' linked entities are
        generated dynamically from the assessment identifiers:

            * we '_' split the string and create a group with the first returned
              item and the concatenation of the two first items.
            * the permissions 'can_read', 'can_update' relate the assessments
              with the corresponding groups.
        """
        # Format inputs
        if not isinstance(subject_eids, list):
            subject_eids = [subject_eids]

        # Create the assessment
        assessment_id = assessment_struct["identifier"]
        if assessment_id in self.inserted_assessments:
            assessment_eid = self.inserted_assessments[assessment_id]
            is_created = False
        else:
            assessment_entity, is_created = self._get_or_create_unique_entity(
                rql=("Any X Where X is Assessment, X identifier "
                     "'{0}'".format(assessment_id)),
                check_unicity=True,
                entity_name="Assessment",
                **assessment_struct)
            assessment_eid = assessment_entity.eid
            self.inserted_assessments[assessment_id] = assessment_eid
            if is_created:
                self.already_related_subjects[assessment_eid] = []
            else:
                rql = ("Any S Where A is Assessment, A eid {}, "
                       "A subjects S".format(assessment_eid))
                self.already_related_subjects[assessment_eid] = [
                    row[0] for row in self.session.execute(rql)]

        # Add relation with the subject
        for subject_eid in subject_eids:
            if subject_eid not in self.already_related_subjects[assessment_eid]:
                self._set_unique_relation(
                    subject_eid, "assessments", assessment_eid,
                    check_unicity=False)
                self._set_unique_relation(
                    assessment_eid, "subjects", subject_eid,
                    check_unicity=False)
                self.already_related_subjects[assessment_eid].append(subject_eid)

        # If we just create the assessment, relate the entity
        if is_created:
            # > add relation with the study
            self._set_unique_relation(
                assessment_eid, "study", study_eid, check_unicity=False,
                subjtype="Assessment")
            self._set_unique_relation(
                study_eid, "assessments", assessment_eid, check_unicity=False,
                subjtype="Assessment")
            # > add relation with the center
            self._set_unique_relation(
                center_eid, "assessments", assessment_eid, check_unicity=False)
            self._set_unique_relation(
                assessment_eid, "center", center_eid, check_unicity=False)

            # Set the permissions
            # Create/get the related assessment groups
            if self.piws_security_model:

                for group_name in self._get_security_groups(assessment_id):

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
            else:
                for group_name in ("users", "guests"):
                    group_eid = groups[group_name]

                    # > add relation with group
                    if self.can_read:
                        self._set_unique_relation(
                            group_eid, "can_read", assessment_eid)
                    if self.can_update:
                        self._set_unique_relation(
                            group_eid, "can_update", assessment_eid)

        return assessment_eid, is_created

    def _get_security_groups(self, assessment_id):
        """ Get the groups that will be associated with this assemssment in
        the security model.
        """
        assessment_id_split = assessment_id.split("_")
        related_groups = [
            assessment_id_split[0],
            "_".join(assessment_id_split[:2])
        ]
        return related_groups

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
            "filesets", fset_entity.eid, check_unicity=False)
        self._set_unique_relation(fset_entity.eid,
            "containers", parent_eid, check_unicity=False)
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
                "external_files", file_entity.eid,
                check_unicity=False)
            self._set_unique_relation(file_entity.eid,
                "fileset", fset_entity.eid,
                check_unicity=False)
            # > add relation with the assessment
            self._set_unique_relation(file_entity.eid,
                "in_assessment", assessment_eid,
                check_unicity=False, subjtype="ExternalFile")
