#! /usr/bin/env python
##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Cubicweb import
from cubicweb.web.views.primary import PrimaryView

# Cubes import
from cubes.brainomics.views.primary import BrainomicsPrimaryView
from cubes.piws.views.components import RelationBox


class PiwsPrimaryView(PrimaryView):
    __regid__ = "primary"
    title = _("primary")
    show_attr_label = True
    show_rel_label = True
    rsection = None
    display_ctrl = None
    main_related_section = True
    allowed_relations = ["subject"]

    def summary(self, entity):
        """ Add method for 3.20 compatibility.
        """
        return

    def render_entity_attributes(self, entity):
        """ Renders all attributes and relations in the 'attributes' section. 
        """
        # Get the entity associated documentation name if available
        if hasattr(entity, "label"):
            tooltip_name = entity.label
        else:
            tooltip_name = None

        # Select only entity attributes
        display_attributes = []
        for rschema, _, role, dispctrl in self._section_def(entity, "attributes"):
            if rschema.final and rschema.type != "identifier":
                value = entity.cw_attr_cache.get(rschema.type)
                if value is not None and value != "":
                    display_attributes.append((rschema, role, dispctrl, value))

        # Display the selected attributes in a table and add a documentation
        # item if available
        if display_attributes:
            self.w(u"<table class='table cw-table-primary-entity'>")
            for rschema, role, dispctrl, value in display_attributes:
                label = self._rel_label(entity, rschema, role, dispctrl)
                self.render_attribute(label, value, table=True)
            if tooltip_name is not None:
                tiphref = self._cw.build_url("view", vid="piws-documentation",
                                             tooltip_name=tooltip_name, _notemplate=True)
                tipbutton = (
                    "<a href='{0}' target=_blank class='btn btn-warning' "
                    "type='button'>Doc &#9735;</a>".format(
                        tiphref))
                self.render_attribute("documentation", tipbutton, table=True)
            self.w(u"</table>")

    def _prepare_side_boxes(self, entity):
        """ Create the right relation boxes to display.

        In the case of 'FileSet' object, go directly to the associated
        'FileEntires'.
        """
        sideboxes = []
        boxesreg = self._cw.vreg["ctxcomponents"]
        defaultlimit = self._cw.property_value("navigation.related-limit")
        for rschema, tschemas, role, dispctrl in self._section_def(
                entity, "sideboxes"):

            # Filter relation box to display
            if role not in self.allowed_relations:
                continue

            # Construct rql depending on entity role
            if role == "subject":
                rql = "Any X WHERE E eid '{0}', E {1} X".format(
                    entity.eid, rschema.type)
            else:
                rql = "Any X WHERE E eid '{0}', X {1} E".format(
                    entity.eid, rschema.type)

            # Get the current rset
            rset = self._relation_rset(entity, rschema, role, dispctrl,
                                       limit=defaultlimit)
            if not rset:
                continue

            # Construct the box label
            if role == "subject":
                source_etype = entity.cw_etype
                target_etype = getattr(entity, rschema.type)[0].cw_etype
            else:
                source_etype = getattr(entity, "reverse_" + rschema.type)[0].cw_etype
                target_etype = entity.cw_etype
            label = (u"{0} <a class='btn btn-info' href='#' "
                     "data-toggle='tooltip' title='{2}'>&#8594;</a> "
                     "{1}".format(source_etype, target_etype, rschema.type))

            # FileSet special case
            if target_etype == "FileSet":
                rql += ", X file_entries F"
                pos = rql.find("X")
                rql = rql[:pos] + "F" + rql[pos + 1:]
                label += (
                    u"<a class='btn btn-info' href='#' data-toggle='tooltip' "
                    "title='file_entries'>&#8594;</a> ExternalFile")
                inner_rset = []
                for fs_entity in rset.entities():
                    inner_rset.append(fs_entity.file_entries)
                rset = inner_rset


            # Construct the relation box
            box = boxesreg.select("relationbox", self._cw, rset=rset, rql=rql,
                                  title=label, dispctrl=dispctrl,
                                  context="incontext")
            sideboxes.append(box)

        # XXX since we've two sorted list, it may be worth using bisect
        def get_order(x):
            if "order" in x.cw_property_defs:
                return x.cw_propval("order")
            # default to 9999 so view boxes occurs after component boxes
            return x.cw_extra_kwargs.get("dispctrl", {}).get("order", 9999)

        return sorted(sideboxes, key=get_order)


def registration_callback(vreg):
    """ Update  primary views
    """
    vreg.register_and_replace(PiwsPrimaryView, BrainomicsPrimaryView)
