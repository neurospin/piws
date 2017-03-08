##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import json
import types

# Cubicweb import
from cubicweb import _
from cubicweb.web.views.primary import PrimaryView
from cubicweb.predicates import is_instance
from cubicweb.web.views.primary import PrimaryView

# Cubes import
from cubes.piws.views.components import RelationBox


# Add summary method for 3.20 compatibility.
def summary(self, entity):
    return u""
PrimaryView.summary = types.MethodType(summary, PrimaryView)


class PIWSPrimaryView(PrimaryView):
    """ Default primary view rendering.
    """
    __regid__ = "primary"
    title = _("Primary")
    # Renders the attribute label next to the attribute value
    show_attr_label = True
    # Renders the relation label next to the relation value
    show_rel_label = True
    rsection = None
    display_ctrl = None
    # Renders the relations of the entity
    main_related_section = True
    allowed_relations = ["subject"]

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
            vid = dispctrl.get("vid", "reledit")
            if ((not self.main_related_section and not rschema.final) or
                    rschema.type == "identifier"):
                continue
            if rschema.final:
                value = entity.cw_attr_cache.get(rschema.type)
            elif vid == "reledit":
                if role in self.allowed_relations:
                    value = entity.view(
                        vid, rtype=rschema.type, role=role,
                        initargs={"dispctrl": dispctrl})
                else:
                    value = None
            else:
                value = None
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
                tiphref = self._cw.build_url(
                    "view", vid="piws-documentation",
                    tooltip_name=tooltip_name, _notemplate=True)
                tipbutton = (
                    "<a href='{0}' target=_blank class='btn btn-warning' "
                    "type='button'>Doc &#9735;</a>".format(
                        tiphref))
                self.render_attribute("documentation", tipbutton, table=True)
            self.w(u"</table>")

    def _prepare_side_boxes(self, entity):
        """ Create the right relation boxes to display.

        This is a common functionality to learn the schema by browsing the
        database content that will enalbe the users to phrase direct RQL to
        get their data.

        In the case of 'FileSet' object, go directly to the associated
        'ExternalResource' if only one 'FileSet' has been specified.
        """
        sideboxes = []
        boxesreg = self._cw.vreg["ctxcomponents"]
        defaultlimit = self._cw.property_value("navigation.related-limit")
        for rschema, tschemas, role, dispctrl in self._section_def(
                entity, "sideboxes"):

            # Filter relation box to display
            if role not in self.allowed_relations:
                continue

            # Get the current rset
            rset = self._relation_rset(entity, rschema, role, dispctrl,
                                       limit=defaultlimit)
            if not rset:
                continue

            # Construct the box label
            if role == "subject":
                source_etype = entity.cw_etype
                target_etypes = set()
                entities = getattr(entity, rschema.type)
                for e in entities:
                    target_etypes.add(e.cw_etype)
                if len(target_etypes) == 1:
                    target_etype = target_etypes.pop()
                else:
                    target_etype = " - ".join(list(target_etypes))
            else:
                source_etype = getattr(entity, "reverse_" + rschema.type)[0].cw_etype
                target_etype = entity.cw_etype
            label = (u"{0} <a class='btn btn-info active' href='#' "
                     "data-toggle='tooltip' title='{2}'>&#8594;</a> "
                     "{1}".format(source_etype, target_etype, rschema.type))

            if role == "subject":
                rql = "Any X WHERE E eid '{1}', E {2} X".format(
                    target_etype, entity.eid, rschema.type)
            else:
                rql = "Any X WHERE E eid '{1}', X {2} E".format(
                    target_etype, entity.eid, rschema.type)

            # FileSet special case
            if target_etype == "FileSet" and entity.cw_etype != "ExternalFile":
                entities = [e for e in rset.entities()]
                nb_fsets = len(entities)
                if nb_fsets == 1:
                    rql += ", X external_files F"
                    pos = rql.find("X")
                    rql = rql[:pos] + "F" + rql[pos + 1:]
                    label += (
                        u"<a class='btn btn-info active' href='#' "
                        "data-toggle='tooltip' "
                        "title='external_files'>&#8594;</a> ExternalFile")
                    inner_rset = []
                    for fs_entity in entities:
                        inner_rset.extend(fs_entity.external_files)
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


class PIWSFilePrimaryView(PIWSPrimaryView):
    """ Specific view for File entities where binary content has to be
    displayed.
    """
    __select__ = PIWSPrimaryView.__select__ & is_instance("File", "RestrictedFile")
    allowed_relations = ["subject", "object"]

    def render_entity_attributes(self, entity, separator=";"):
        """ Renders all attributes and relations in the 'attributes' section.
        Unwrap binary field.

        Parameters
        ----------
        separator: str (optional, default ';')
            the CSV cell separator.
        """
        super(PIWSPrimaryView, self).render_entity_attributes(entity)
        if "json" in entity.data_format:
            data = json.loads(entity.data.getvalue())
            data = unicode(json.dumps(data, indent=4))
        elif "comma-separated-values" in entity.data_format:
            rset = entity.data.getvalue().split("\n")
            labels = rset[0].split(separator)
            records = []
            for index, line in enumerate(rset[1:]):
                elements = line.split(separator)
                if len(elements) == len(labels):
                    elements.insert(0, str(index))
                    records.append(elements)

            self.wview("jtable-hugetable-clientside", None, "null",
                       labels=labels, records=records, csv_export=True,
                       title="", elts_to_sort="ID")
            return
        else:
            data = unicode(entity.data.getvalue())
        self.w(data.replace("\n", "<br/>").replace(" ", "&nbsp"))


def registration_callback(vreg):
    """ Update  primary views
    """
    vreg.register_and_replace(PIWSPrimaryView, PrimaryView)
    vreg.register(PIWSFilePrimaryView)
