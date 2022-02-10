from jsonschema import validate, exceptions


def verifyMetadataForUpload(metadata):
    # code from irodsapi/dataset.py
    """Verify a metadata against the schemas and return them

    Parameters
    ----------
    metadata : iRODS metadata

    Return
    ------
    error or None
    """
    metadataSingleValue = [
        'identifier',
        'title',
        'publicationYear',
        'resourceType',
        'resourceTypeGeneral',
        'CustomMetadata',
        'scope',
        'format']
    metadataMultiValue = [
        'creator',
        'publisher',
        'owner',
        'contributor',
        'relatedIdentifier',
        'rights',
        'rightsURI',
        'rightsIdentifier',
        'CustomMetadataSchema',
        'AlternateIdentifier',
        'RelatedSoftware',
        'description']
    if metadata is not None:
        schemas = metadata.get("CustomMetadataSchema", None)
        custom = metadata.get("CustomMetadata", None)
        if custom is not None or schemas is not None:
            for idx, schema in enumerate(schemas):
                try:
                    validate(instance=custom, schema=schema)
                except exceptions.ValidationError:
                    return (
                        "CustonMetadata not validated by schema " +
                        str(idx))
        for x in metadataSingleValue:
            val = metadata.get(x, None)
            if val is not None and not isinstance(val, str):
                return "Metadata " + x + " is not a string"
        for x in metadataMultiValue:
            val = metadata.get(x, None)
            if val is not None and not isinstance(val, list):
                return "Metadata " + x + " is not an array"

        ais = metadata.get("AlternateIdentifier", None)
        if ais is not None:
            for ai in ais:
                if not isinstance(ai, list) or len(ai) != 2:
                    return (
                        "Metadata AlternateIdentifier should be an array of pairs of strings")
                if not isinstance(ai[0], str) or not isinstance(ai[1], str):
                    return (
                        "Metadata AlternateIdentifier should be an array of pairs of strings")
    return None
