"""
Exceptions that can occur while using trans transformations
"""

class TransformException(Exception):
    """
    An error that can occur while transforming JSON data
    """

    def __init__(self, message, name=None, input=None, context=None):
        """
        construct the exception, providing a message

        :argument str message: an explanation of what went wrong
        :argument str name:  the name of the transform were the exception
                             occured.  If None, the transform name is unknown
                             or not applicable.
        :argument input:    the JSON data that was being transformed
        :argument context:  the context at the point of the exception
        """
        super(TransformException, self).__init__(message)
        self.transform = name
        self.input = input
        self.context = context

class TransformStateException(TransformException):
    """
    an exception indicating that an unexpected state occurred that prevented
    the application of a transformation.  This exception typically wraps 
    another exception that was the underlying cause
    """

    def __init__(self, cause=None, message=None, name=None,
                 input=None, context=None):
        """
        construct the exception to wrap another one

        :argument exc cause: the underlying exception that halted the 
                             transformation
        :argument str message: an explanation of what went wrong
        :argument str name:  the name of the transform were the exception
                             occured.  If None, the transform name is unknown
                             or not applicable.
        :argument input:    the JSON data that was being transformed
        :argument context:  the context at the point of the exception
        """
        if not message:
            if name:
                message = "Internal failure in the %s transform: %s" % \
                          (name, repr(cause))
            elif cause:
                message = "Internal transform failure: " + repr(cause)
            else:
                message = "Unknown internal failure"

        super(TransformStateException, self).__init__(message, name,
                                                       input, context)
        self.cause = cause

class TransformConfigError(TransformException):
    """
    an exception indicating an invalid transform configuration.
    """

    def __init__(self, param=None, name=None, message=None, 
                 basemsg="transform invalid: invalid configuration"):
        """
        create the exception

        :argument str name:  the name of the transform were the exception
                             occured.  If None, the transform name is unknown
                             or not applicable.
        :argument str message: an explanation of what went wrong; if not 
                            provided, one is generated based on param, name.
        """
        if not message:
            message = ''
            if name: 
                message = name + " "
            message += basemsg
            if param:
                message += ": " + param

        super(TransformConfigError, self).__init__(message, name)
        self.param = param

class TransformNotFound(TransformConfigError):
    """
    an exception indicating that a template could not be resolved
    """
    def __init__(self, name=None, message=None):
        if not message:
            message = "Named transform could not be found"
            if name:
                message += ': ' + name
        super(TransformNotFound, self).__init__(name=name, message=message)

class MissingTransformData(TransformConfigError):
    """
    an exception indicating that an invalid transform request because
    it was missing critical configuration or input data.  
    """

    def __init__(self, param=None, name=None, message=None, 
                 basemsg="transform invalid: missing parameter"):
        """
        create the exception, noting the parameter that was missing

        :argument str name:  the name of the transform were the exception
                             occured.  If None, the transform name is unknown
                             or not applicable.
        :argument input:    the JSON data that was being transformed
        :argument context:  the context at the point of the exception
        :argument str message: an explanation of what went wrong; if not 
                            provided, one is generated based on param, name.
        """
        super(MissingTransformData, self).__init__(param, name, message,basemsg)

class StringTemplateSyntaxError(TransformConfigError):
    """
    an exception indicating that an invalid transform request because
    it was missing critical configuration or input data.  
    """

    def __init__(self, message=None, template=None, param=None, name=None):
        msg = "String template syntax error"
        if message:
            message = msg + ": " + message
        else:
            message = msg
        if template:
            if not isinstance(template, str):
                template = str(template)
            message += ": " + template
        super(StringTemplateSyntaxError, self).__init__(param, name, message)

class TransformConfigTypeError(TransformConfigError):
    """
    the type of a provided configuration property has the wrong type for the
    type of transform being generated.
    """
    def __init__(self, param=None, need=None, got=None, name=None, 
                 message=None):
        if not message:
            message = ""
            if name: message += name + " transform: "
            message += "Invalid type for "
            if param:  message += param + " "
            message += "parameter"
            if need or got:
                message += ": "
                if need: message += "need %s " % need
                if need and got:  message += ", "
                if got:  message += "got %s." % got

        super(TransformConfigTypeError, self).__init__(param, name, 
                                                       message=message)
        self.typeneeded = need
        self.typegot = got

class StylesheetContentError(TransformStateException):

    def __init__(self, message=None, cause=None, input=None, context=None):
        """
        construct the exception to wrap another one

        :argument exc cause: the underlying exception that halted the 
                             transformation
        :argument str message: an explanation of what went wrong
        :argument str name:  the name of the transform were the exception
                             occured.  If None, the transform name is unknown
                             or not applicable.
        :argument input:    the JSON data that was being transformed
        :argument context:  the context at the point of the exception
        """
        if not message:
            message = "Problem while parsing/using stylesheet: " + repr(cause)
        super(StylesheetContentError, self).__init__(message=message, 
                                                     cause=cause,
                                                     name=None, input=input,
                                                     context=context)

class TransformInputError(TransformException):
    """
    an exception indicating a transform could not be applied due to an 
    invalid condition in the input data.
    """
    def __init__(self, message, name=None, input=None, context=None):
        super(TransformInputError, self).__init__(message, name, input, context)

class TransformInputTypeError(TransformInputError):
    """
    an exception indicating a transform could not be applied because the 
    input data has the wrong (JSON data structure) type.
    """
    def __init__(self, need=None, got=None, name=None, 
                 input=None, context=None, message=None):
        if not message:
            message = ""
            if name: message += name + " "
            message += "Transform failed due to wrong input data type"
            if need or got:
                message += ": "
                if need: message += "need %s " % need
                if need and got:  message += ", "
                if got:  message += "got %s." % got

        super(TransformInputError, self).__init__(message, name, input, context)
        self.typeneeded = need
        self.typegot = got

