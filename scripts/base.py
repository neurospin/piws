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

# Cubicweb import
from cubicweb.dataimport import SQLGenObjectStore


class Base(object):
    """ This class enables us to add new entities and relations in CW.
    """
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
