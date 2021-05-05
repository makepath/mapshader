import re


TREATMENTS = {
    re.compile(r'(?<=cmap=)(\[.*\])'): 'mapshader.colors.colors',
}


def parameter_treatment(app, objtype, name, obj, options, args, retann):
    '''
    Treat the object signature, replacing the regex matching with a new
    text.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        The Sphinx application object.
    objtype : str
        The type of the object which the docstring belongs to (one of
        ``"module"``, ``"class"``, ``"exception"``, ``"function"``,
        ``"method"``, ``"attribute"``).
    name : str
        The fully qualified name of the object.
    obj : any
        The object itself.
    options : dict
        The options given to the directive: an object with attributes
        ``inherited_members``, ``undoc_members``, ``show_inheritance``
        and ``noindex`` that are true if the flag option of same name
        was given to the auto directive.
    args : str
        The object signature, as a string of the form
        ``"(parameter_1, parameter_2)"``, or ``None`` if introspection
        didn't succeed and signature wasn't specified in the directive.
    retann : str
        The function return annotation as a string of the form
        ``" -> annotation"``, or ``None`` if there is no return annotation.

    Returns
    -------
    args : str
        The treated object signature.
    retann : str
        The input function return annotation.

    References
    ----------
        - sphinx: https://github.com/sphinx-doc/sphinx/blob/b237e78f9c233170f271c326bf46b7fb3b103858/doc/usage/extensions/autodoc.rst # noqa
    '''
    if objtype not in ('function', 'method', 'class'):
        return

    if args is None:
        return

    for regex, new_text in TREATMENTS.items():
        args = regex.sub(new_text, args)

    return args, retann

def setup(app):
    app.connect('autodoc-process-signature', parameter_treatment)
