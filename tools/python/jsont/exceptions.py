"""
Exceptions that can occur while using trans transformations
"""
import jsonspec.pointer as jsonptr

class JSONTransformException(Exception):
    """
    An error that can occur while transforming JSON data.  This is the 
    base exception for all exceptions resulting from the transforms module.
    """

    def __init__(self, message, cause=None):
        """
        construct the exception, providing a message

        :argument str message:      an explantation of the error condition.
        :argument Exception cause:  the exception representing the underlying 
                                      cause of the exception.  If None, there 
                                      was no such underlying cause.
        """
        super(Exception, self).__init__(message)
        self.cause = cause

class TransformConfigException(JSONTransformException):
    """
    An exception resulting while processing the transform configuration 
    (i.e. the stylesheet) in preparation for its application to the 
    input data.
    """

    def __init__(self, message, name=None, cause=None):
        """
        construct the exception, providing a message

        :argument str message: an explanation of what went wrong
        :argument str name:  the name of the transform where the exception
                             occured.  If None, the exception is not known
                             or not specific to a particular transform.
        :argument Exception cause:  the exception representing the underlying 
                                      cause of the exception.  If None, there 
                                      was no such underlying cause.

        :argument input:    the JSON data that was being transformed
        :argument context:  the context at the point of the exception
        """
        super(TransformConfigException, self).__init__(message, cause)
        self.transform = name

    @classmethod
    def make_message(cls, name, why):
        """
        build an exception message based on an underlying exception cause.

        :argument Exception cause:  the exception representing the underlying 
                                      cause of the exception.  
        :argument str name:  the name of the transform being applied when
                             the exception occured.  This is incorporated into
                             the message only when the basemsg is not provided
        :argument str why:  a base explanation to combine with the message
                                from the underlying cause.  
        """
        msg = ""
        if name: msg += name + " "
        msg += "transform config error"
        if why: msg += ": " + why
        return msg

class TransformNotFound(TransformConfigException):
    """
    an exception indicating that a template could not be resolved
    """
    def __init__(self, name=None, message=None):
        if not message:
            message = "Named transform could not be found"
            if name:
                message += ': ' + name
        super(TransformNotFound, self).__init__(message, name)


class TransformDisabled(TransformConfigException):
    """
    an exception indicating that a template is currently (marked as) disabled
    """
    def __init__(self, name=None, message=None):
        if not message:
            message = "Transform is currently disabled"
            if name:
                message += ': ' + name
        super(TransformDisabled, self).__init__(message, name)


class TransformConfigParamError(TransformConfigException):
    """
    a transform configuration exception due to an error in a particular 
    parameter.
    """

    def __init__(self, param, name=None, message=None):
        if not message:
            message = TransformConfigException.make_message(name, 
                                         "problem with "+ param + " parameter")
        super(TransformConfigParamError, self).__init__(message, name)
        self.param = param

class MissingTransformData(TransformConfigParamError):
    """
    an exception indicating that an invalid transform request because
    it was missing critical configuration or input data.  
    """

    def __init__(self, param=None, name=None, message=None):
        """
        create the exception, noting the parameter that was missing.  This 
        may be either be transform configuration property or an argument
        to the function-form of the transform.

        :argument str param: the name of the missing configuration parameter
        :argument str name:  the name of the transform were the exception
                             occured.  If None, the transform name is unknown
                             or not applicable.
        :argument str message: an explanation of what went wrong; if not 
                            provided, one is generated based on param, name.
        """
        if not message:
            message = TransformConfigException.make_message(
                name, "missing parameter: " + param)
        super(MissingTransformData, self).__init__(param, name, message)

class TransformConfigTypeError(TransformConfigParamError):
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
                if need: message += "need %s" % need
                if need and got:  message += ", "
                if got:  message += "got %s." % got

        super(TransformConfigTypeError, self).__init__(param, name, message)
        self.typeneeded = need
        self.typegot = got

class StringTemplateSyntaxError(TransformConfigException):
    """
    an exception indicating an error in the tranform token syntax within
    a string template.
    """

    def __init__(self, message=None, template=None, name=None):
        msg = "Syntax error in string template"
        if name: msg += " ({0})".format(name)
        if message:
            message = msg + ": " + message
        else:
            message = msg
        if template:
            message += ": " + repr(template)
        super(StringTemplateSyntaxError, self).__init__(message, name)
        self.template = template

class TransformApplicationException(JSONTransformException):
    """
    an exception that occurs while trying to apply a transform to the input
    data.

    If the due_to() constructor is helpful for constructing a message that 
    relates to an underlying cause represented by another Exception.
    """

    def __init__(self, message, input=None,context=None, name=None,cause=None):
        """
        construct the exception, providing an explanation.

        :argument str message: an explanation of what went wrong
        :argument input:    the JSON data that was being transformed
        :argument context:  the context at the point of the exception
        :argument str name:  the name of the transform being applied when
                             the exception occured.  If None, the exception 
                             is not known or not specific to a particular 
                             transform.
        :argument Exception cause:  the exception representing the underlying 
                                      cause of the exception.  If None, there 
                                      was no such underlying cause.
        """
        super(TransformApplicationException, self).__init__(message, cause)
        self.transform = name
        self.input = input
        self.context = context

    @classmethod
    def make_message(cls, name, why, basemsg=None):
        """
        build an exception message based on an underlying exception cause.

        :argument Exception cause:  the exception representing the underlying 
                                      cause of the exception.  
        :argument str name:  the name of the transform being applied when
                             the exception occured.  This is incorporated into
                             the message only when the basemsg is not provided
        :argument str why:  a base explanation to combine with the message
                                from the underlying cause.  
        :argument str basemsg:  a base explanation to combine with the message
                                from the underlying cause.  If None, a generic
                                default based on the name is used. 
        """
        if not basemsg:
            basemsg = "Failed to apply "
            if name: basemsg += name + " "
            basemsg += "transform"
        msg = basemsg
        if why: msg += ": " + why
        return msg

    @classmethod
    def make_message_from_cause(cls, cause, name=None, basemsg=None):
        """
        build an exception message based on an underlying exception cause.

        :argument Exception cause:  the exception representing the underlying 
                                      cause of the exception.  
        :argument str name:  the name of the transform being applied when
                             the exception occured.  This is incorporated into
                             the message only when the basemsg is not provided
        :argument str basemsg:  a base explanation to combine with the message
                                from the underlying cause.  If None, a generic
                                default is used. 
        """
        return cls.make_message(name, repr(cause), basemsg)

    @classmethod
    def due_to(cls, cause, input=None, context=None, name=None, basemsg=None):
        """
        construct an exception that is mainly due to an underlying problem.

        :argument Exception cause:  the exception representing the underlying 
                                      cause of the exception.  
        :argument str basemsg:  a base explanation to combine with the message
                                from the underlying cause.  If None, a generic
                                default is used. 
        """
        msg = cls.make_message_from_cause(cause, name, basemsg)
        return TransformApplicationException(msg, input, context, name, cause)

class DataExtractionError(TransformApplicationException):
    """
    an exception indication an error while attempting to extract data 
    from the transform input.
    """

    def __init__(self, message, select=None, input=None, context=None, 
                 name=None, cause=None):
        """
        construct the exception, providing an explanation.

        :argument str message: an explanation of what went wrong
        :argument input:    the JSON data that was being transformed
        :argument context:  the context at the point of the exception
        :argument str name:  the name of the transform being applied when
                             the exception occured.  If None, the exception 
                             is not known or not specific to a particular 
                             transform.
        :argument Exception cause:  the exception representing the underlying 
                                      cause of the exception.  If None, there 
                                      was no such underlying cause.
        """
        super(TransformApplicationException, self).__init__(message, cause)
        self.select = select

    @classmethod
    def due_to(cls, cause, select, input=None, context=None, name=None):
        """
        construct an exception that is mainly due to an underlying problem.

        :argument Exception cause:  the exception representing the underlying 
                                      cause of the exception.  
        :argument str basemsg:  a base explanation to combine with the message
                                from the underlying cause.  If None, a generic
                                default is used. 
        """
        basemsg = ""
        if name: basemsg += name + ' transform: '
        basemsg += "problem extracting data with '" + select + "'"
        msg = cls.make_message_from_cause(cause, basemsg=basemsg)
        return DataExtractionError(msg, select, input, context, name, cause)

class DataPointerError(DataExtractionError):
    """
    an error indicating a failure extracting data due to a problem with the
    data pointer itself.  Typically, this is because the pointer does not 
    follow the proper syntax.
    """

    @classmethod
    def due_to(cls, cause, dp, orig=None):
        """
        construct an exception that is mainly due to an underlying problem.

        :argument Exception cause:  the exception representing the underlying 
                                      cause of the exception.  
        :argument dp:  the (normalized) data pointer
        :argument orig:  the unnormalized data pointer, if known
        """
        causemsg = str(cause)
        if isinstance(cause, jsonptr.ParseError):
            causemsg = "did not normalize to useable JSON pointer"
        msg = "Problem using data pointer"
        if orig:
            msg += ", '"+str(orig)+"'"
        msg += ": {0}: {1}".format(causemsg, str(dp))
        return DataPointerError(msg, cause=cause)
        

class TransformInputTypeError(TransformApplicationException):
    """
    an exception indicating a transform could not be applied because the 
    input data has the wrong (JSON data structure) type.
    """
    def __init__(self, need=None, got=None, name=None, 
                 input=None, context=None, message=None):
        if not message:
            msg = ""
            if name: msg += name + " "
            msg += "wrong input data type"
            if need or got:
                msg += ": "
                if need: msg += "need %s " % need
                if need and got:  msg += ", "
                if got:  msg += "got %s." % got
            message = \
                TransformApplicationException.make_message(name, msg)

        super(TransformInputTypeError, self).__init__(message, input, context, 
                                                      name)
        self.typeneeded = need
        self.typegot = got

