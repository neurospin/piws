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

# Piws import
from .base import Base


class Groups(Base):
    """ This class enables us to add new user groups in CW.
    """
    def __init__(self, session, list_group_names, use_store=True):
        """ Initialize the Groups class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        list_group_names: list of str (mandatory)
            the name of the different groups.
        use_store: bool (optional, default True)
            if True use an SQLGenObjectStore, otherwise the session.
        """
        # Inheritance
        super(Groups, self).__init__(session, use_store)

        # Class parameters
        self.list_group_names = list_group_names

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import the groups in CW.

        .. note::

            This procedure create a 'CWGroup' entity for each input group
            name.
        """
        # Go through the goup names
        nb_of_groups = float(len(self.list_group_names))
        for cnt_group, goup_name in enumerate(self.list_group_names):

            # Print a progress bar
            self._progress_bar((cnt_group + 1) / nb_of_groups,
                               title="Import {0}:".format(goup_name),
                               bar_length=40)
            cnt_group += 1.

            # Create the group if necessary
            group_entity, _ = self._get_or_create_unique_entity(
                rql=("Any X Where X is CWGroup, X name "
                     "'{0}'".format(goup_name)),
                check_unicity=True,
                entity_name="CWGroup",
                name=unicode(goup_name))

        print  # new line after last progress bar update
