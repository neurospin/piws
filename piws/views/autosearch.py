##########################################################################
# NSAp - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# CW import
from cgi import parse_qs
from cubicweb.web.views.forms import FieldsForm
from cubicweb.view import View
from cubicweb.web.views.baseviews import NullView
from cubicweb.web import formfields
from cubicweb.web import formwidgets
from cubicweb.web import RequestError
from cubicweb.web import Redirect

#rschema = form._cw.vreg.schema['done_in'].rdef('Ticket', 'Version')


class AutoSearchForm(FieldsForm):
    """ The authorized form fields are defined in the global parameter
    'DECLARED_FIELDS' that can be found in the
    'rql_upload.views.formfields.formfields' module.
    """
    __regid__ = "auto-search-form"

    form_buttons = [
        formwidgets.SubmitButton(label="> continue", cwaction="apply")]
        #formwidgets.Button(label=u"Filter entity parameters", cwaction="apply")]
    auorsearch_rql = formfields.StringField(
        name="rql", label="rql", required=False, value="")


class AutoSearch(View):
    """ Class to generate rql request graphically.
    """
    __regid__ = "auto-search"
    _exclusion_attribute_list = ["eid", "description", "creation_date",
                                 "modification_date", "cwuri"]
    _exclusion_relation_list = ["created_by", "owned_by", "is", "is_instance_of",
                                "cw_source", "container_etype",
                                "container_parent"]
    _start_entities = ["Subject", "Scan", "ProcessingRun", "QuestionnaireRun",
                       "GenomicMeasure"]

    def call(self, **kwargs):
        """ Create the selection page.
        """
        # Get url parameters
        path = self._cw.relative_path()
        if "?" in path:
            path, param = path.split("?", 1)
            kwargs.update(parse_qs(param))
        #self.w(unicode(kwargs))

        # List all the entities: get a dict with entity names as keys.
        # The 'entity_schema' is class of type
        # 'cubicweb.schema.CubicWebEntitySchema'
        entities = {}
        for entity in self._cw.session.repo.schema.entities():
            entities[entity.type] = {
                "entity_schema": entity,
                "subject_attributes": [
                    r for r in entity.subject_relations() if r.final],
                "subject_relations": [
                    r for r in entity.subject_relations() if not r.final],
                "object_relations": [
                    r for r in entity.object_relations() if not r.final]
            }

        # Create a form
        form = self._cw.vreg["forms"].select(
            "auto-search-form", self._cw, action="", form_name="AutoSearch")

        # Create a combobox to choose the entity of interest
        if "_filter" not in kwargs:

            # Starting point from the class parameter
            if "_linked_entities" not in kwargs:
                entity_selector = formfields.StringField(
                    name="entity_selector", label="entity_selector",
                    required=True, choices=self._start_entities)
                form.append_field(entity_selector)
            else:
                linked_entites = kwargs["_linked_entities"][0].split(",")
                entity_selector = formfields.StringField(
                    name="entity_selector", label="entity_selector",
                    required=True, choices=linked_entites)
                form.append_field(entity_selector)

        # Filter the entity attributes
        else:
            ename = self.split_entity_field(kwargs["_entity"][0])[0]
            eattributes = entities[ename]["subject_attributes"]
            for attrib in eattributes:

                # Consider only attribute of interset
                if attrib.type not in self._exclusion_attribute_list:

                    # Get the attribute type
                    field_type = None
                    for (cwsubject, cwobject), props in attrib.rdefs.items():
                        if cwsubject.type == kwargs["_entity"][0]:
                            field_type = cwobject.type
                            break
                    if field_type is None:
                        self.w(u"<p class='label label-danger'>Can't find the '{0}' "
                                "'{1}' attribute type.</p>".format(
                                    kwargs["_entity"], attrib.type))

                    # Create the fields to add filter on the entity attributes
                    filter_field = formfields.StringField(
                        name=attrib.type, required=False,
                        label="{0} [{1}]".format(attrib.type, field_type))
                    form.append_field(filter_field)

        # Form processings
        try:
            posted = form.process_posted()
            #for field_name, field_value in posted.iteritems():
            #    print field_name, field_value

            # Redirection to the created CWUpload entity
            if "_filter" in kwargs:

                # Find the entities directly connected to the current entity
                ename = self.split_entity_field(kwargs["_entity"][0])[0]
                all_relations = entities[ename]["subject_relations"]
                all_relations.extend(entities[ename]["object_relations"])
                linked_entities = []
                for relation in all_relations:

                    # Consider only relation of interest
                    if relation.type not in self._exclusion_relation_list:

                        # Get the targets and associated relation type: subject
                        # or object
                        for (cwsubject, cwobject), props in relation.rdefs.items():
                            if cwsubject.type == ename and cwobject.type != ename:
                                linked_entities.append(">{0}[{1}]".format(
                                    cwobject.type, relation.type))
                            if cwobject.type == ename and cwsubject.type != ename:
                                linked_entities.append("<{0}[{1}]".format(
                                    cwsubject.type, relation.type))

                # Build the new entity selection url
                autosearch_url = self._cw.build_url(
                    vid="auto-search", __message=u"Select a new entity.",
                    _rql=self._cw.form["rql"],
                    _linked_entities=",".join(set(linked_entities)))
            else:
                ename = self.split_entity_field(self._cw.form["entity_selector"])[0]
                autosearch_url = self._cw.build_url(
                    vid="auto-search", _filter=u"True",
                    __message=(u"Add filter rules on the '{0}' entity "
                                "attributes.".format(ename)),
                    _rql=self._cw.form["rql"], _entity=ename)
            raise Redirect(autosearch_url)
        except RequestError as error:
            self.w(u"<p class='label label-danger'>{0}</p>".format(error))

        # Form rendering
        self.w(u'<h1 class="panel-title">Build your selection</h1>')
        form.render(w=self.w, formvalues=self._cw.form)

    def split_entity_field(self, efield):
        """ The expected synthax is (><)entity_name[relation_name]
        """
        if efield[0] in [">", "<"]:
            ename, rname = efield[1: -1].split("[")
            if efield[0] == ">":
                return ename, rname, "subject"
            else:
                return ename, rname, "object"
        else:
            return efield, None, None

    def update_rql():
        """ Update the rql request based on the form values.
        """
