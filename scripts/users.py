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
import logging

# Neurospinweb import
from cubes.neurospinweb.scripts.base import Base


class Users(Base):
    """ This class enables us to add new users in CW and associate this user to
    one or multiple groups.
    """
    def __init__(self, session, users, use_store=True):
        """ Initialize the Users class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        users: dict (mandatory)
            the user names as keys and a dict with the group_names, login and
            password.
        use_store: bool (optional, default True)    
            if True use an SQLGenObjectStore, otherwise the session.

        Notes
        -----
        Here is an axemple of the definiton of the 'users' parameter:

        users = {
            "user1": {
                "login": "user1",
                "password": "user1",
                "group_names": ["group_v0", "users"]
            },
            "user2": {
                "login": "user2",
                "password": "user2",
                "group_names": ["group_v1", "users"]
            },
            "user3": {
                "login": "user3",
                "password": "user3",
                "group_names": ["group_v0v1", "users"]
            }
        }
        """
        # Inheritance
        super(Users, self).__init__(session, use_store)

        # Class parameters
        self.users = users

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import the users in cw.
        """
        # Go through the goup names
        nb_of_users = float(len(self.users))
        cnt_user = 1.
        for user_name, user_item in self.users.iteritems():

            # Print a progress bar
            self._progress_bar(
                cnt_user / nb_of_users,
                title="Import {0}:".format(user_name),
                bar_length=40)
            cnt_user += 1.

            # Create the user
            user_entity, _ = self._get_or_create_unique_entity(
                rql=("Any X Where X is CWUser, X login "
                     "'{0}'".format(user_item["login"])),
                check_unicity=True,
                entity_name="CWUser",
                login=unicode(user_item["login"]),
                upassword=unicode(user_item["password"]))

            # Go through group names
            for group_name in user_item["group_names"]:

                # Check if the group exists
                rql = "Any X Where X is CWGroup, X name '{0}'".format(group_name)

                # Execute the rql request
                rset = self.session.execute(rql)

                # The request returns some data -> do nothing
                if rset.rowcount != 1:
                    logging.error(
                        "Can't insert user '{0}' in group '{1}', got {2} "
                        "matches.".format(user_name, group_name, rset.rowcount))
                    continue

                # Get the group entity
                group_eid = rset[0][0]
                # > add relation with the user
                self._set_unique_relation(user_entity.eid,
                        "in_group", group_eid, check_unicity=True)
