# -*- coding: utf-8 -*-

from . import OASpecSchema, SchemaField, SchemaObject

contact_object = OASpecSchema()
contact_object.name = SchemaField("string")
contact_object.url = SchemaField("string", fmt="url")
contact_object.email = SchemaField("string", fmt="email")

license_object = OASpecSchema()
license_object.name = SchemaField("string", req=True)
license_object.url = SchemaField("string", fmt="url")

info_object = OASpecSchema()
info_object.title = SchemaField("string", req=True)
info_object.description = SchemaField("string")
info_object.termsOfService = SchemaField("string", fmt="url")
info_object.contact = SchemaObject(contact_object)
info_object.license = SchemaObject(license_object)
info_object.version = SchemaField("string", req=True)
