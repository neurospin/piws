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

# Cubicweb import
from cubicweb import Binary
from cubicweb.server.utils import crypt_password

# Piws import
from .base import Base


class CWUsers(Base):
    """ This class enables us to add new users in CW and associate this user to
    one or multiple groups.
    """
    # Define the relations involved
    relations = [
        ("CWUser", "in_group", "CWGroup")
    ]

    def __init__(self, session, users):
        """ Initialize the CWUsers class.

        Parameters
        ----------
        session: Session (mandatory)
            a cubicweb session.
        users: dict (mandatory)
            the user names as keys and a dict with the group_names, login and
            password.

        Notes
        -----
        Here is an example of the definition of the 'users' parameter:

        ::

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
        super(CWUsers, self).__init__(
            session=session,
            can_read=True,
            can_update=True,
            use_store=False,
            piws_security_model=False)

        # Class parameters
        self.users = users

    ###########################################################################
    #   Public Methods
    ###########################################################################

    def import_data(self):
        """ Method that import the users in cw.

        .. note::

            This procedure create a user as a 'CWUser' entity which is related
            to different groups through the 'in_group' relation.

            |

            .. image:: ../schemas/users.png
                :width: 500px
                :align: center
                :alt: schema

        .. warning::

            This procedure expect that the 'CWGroup' of interest are already
            created.
        """
        # Get the activated State entity
        rql = "Any X Where X is State, X name 'activated'"
        rset = self.session.execute(rql)
        if rset.rowcount != 1:
            logging.error(
                "Can't insert users, no activated State entity detected.")
            raise Exception("Can't insert users, no activated State entity "
                            "detected.")
        state_eid = rset[0][0]

        # Go through the goup names
        nb_of_users = float(len(self.users))
        maxsize = max([len(name) for name in self.users])
        cnt_user = 1.
        for user_name, user_item in self.users.iteritems():

            # Print a progress bar
            self._progress_bar(
                cnt_user / nb_of_users,
                title="{0}(users)".format(user_name),
                bar_length=40, maxsize=maxsize + 7)
            cnt_user += 1.

            # Create the user
            crypted = crypt_password(user_item["password"])
            user_entity, is_created = self._get_or_create_unique_entity(
                rql=("Any X Where X is CWUser, X login "
                     "'{0}'".format(user_item["login"])),
                check_unicity=True,
                entity_name="CWUser",
                login=unicode(user_item["login"]),
                upassword=Binary(crypted))

            # If the user is created, add relation with the State entity
            if is_created:
                self._set_unique_relation(user_entity.eid,
                        "in_state", state_eid, check_unicity=False)

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

        print  # new line after last progress bar update
