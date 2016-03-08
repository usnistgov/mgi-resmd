"""
The std module's initial (default) context data.  The defaults are specified 
in this context module's file for documentation purposes (see # comments); 
however, values set within the stylesheet file (std/ss.json) will take 
precedence.
"""
p = 'std.'

def_context = {

    # The prefered line width to use when filling data into paragraphs by 
    # the fill transform
    #
    p+"fill.width": 75,

    # The prefered indentation amount to use when filling data into 
    # paragraphs by the fill transform
    # 
    p+"fill.indent": 0,
}

