"""
This module contains all the global methods to be automatically added to a new
AdveneContext.
Note that those method must import every module they need _inside_ their body in
order to prevent cyclic references.
"""

def absolute_url(target, context):

    import advene.model.annotation
    import advene.model.content
    import advene.model.fragment
    import advene.model.package
    import advene.model.query
    import advene.model.schema
    import advene.model.view

    def _abs_url(target):
        if isinstance(target, advene.model.annotation.Annotation):
            return '/annotations/%s' % target.getId()
        elif isinstance(target, advene.model.annotation.Relation):
            return '/relations/%s' % target.getId()
        elif isinstance(target, advene.model.package.Package):
            return ''
        elif isinstance(target, advene.model.query.Query):
            return '/queries/%s' % target.getId()
        elif isinstance(target, advene.model.schema.Schema):
            return '/schemas/%s' % target.getId()
        elif isinstance(target, advene.model.schema.AnnotationType):
            return '/schemas/%s/annotationTypes/%s' % \
                                    (target.getSchema().getId(), target.getId())
        elif isinstance(target, advene.model.schema.RelationType):
            return '/schemas/%s/relationTypes/%s' % \
                                    (target.getSchema().getId(), target.getId())
        elif isinstance(target, advene.model.view.View):
            return '/views/%s' % target.getId()
        else:
            return None

    path = _abs_url(target)

    if path is None:
        if context is None:
            return None
        resolved_stack = context.locals['__resolved_stack'].value()
        if resolved_stack is None or len (resolved_stack) == 0:
            return None
        suffix = [resolved_stack[0][0]]
        for i in resolved_stack[1:]:
            name, obj = i
            path = _abs_url (obj.value())
            if path is not None:
                path = "%s/%s" % (path, "/".join (suffix))
                break
            else:
                suffix.insert (0, name)
       
    if path is not None and context is not None:
        options = context.globals['options'].value()
        if options.has_key('package_url'):
            path = '%s%s' % (options['package_url'], path)
    return path

def isa (target, context):
    """
    Return an object such that target/isa/[viewable_class],
    target/isa/[viewable_type] and target/isa/[viewable_class]/[viewble_type]
    are true for the correct values of viewable_class and viewable_type.
    Note that for annotations and relations, viewable_type must be the QName
    for of the type URI.
    Note that for contents, viewable_type can be a two part path, corresponding
    to the usual mime-type writing. The star ('*') character, however, is not
    supported. For example, if c1 has type 'text/*' and c2 has type
    'text/plain', the following will evaluate to True: c1/isa/text,
    c2/isa/text, c1/isa/text/html; the following will of course evaluate to 
    False: c2/isa/text/html.
    
    """
    class my_dict (dict):
        def __init__ (self, values={}, default=False):
            dict.__init__(self)
            self.__default = default
            for k,v in values.iteritems():
                self[k]=v
                
        def has_key (self, key):
            return True
        
        def __getitem__ (self, key):
            if dict.has_key (self, key):
                return dict.__getitem__ (self, key)
            else:
                return self.__default
            
        def merge (self, dico):
            for k,v in dico.iteritems():
                self[k]=v

    try:
        viewable_class = target.getViewableClass()
    except AttributeError:
        return my_dict({'unknown':True})
    
    r = my_dict ({viewable_class:True}) 
    if viewable_class == 'content':
        t1, t2 = target.getMimetype ().split ('/')
        vt1 = my_dict ({t2:True})
        mimetype_dict = my_dict ({t1:vt1})
        r[viewable_class] = mimetype_dict
        r.merge (mimetype_dict)
    elif viewable_class in ('annotation', 'relation'):
        viewable_type = target.getType ().getId ()
        d1 = my_dict ({viewable_type:True})
        r[viewable_class] = d1
        r.merge (d1)
    elif viewable_class == 'list':
        viewable_type = target.getViewableType ()
        list_dict = ({viewable_type:True})
        r[viewable_class] = list_dict
        r.merge (list_dict)

    return r
        
def meta(target, context):
    """
    Function to be used as a TALES global method, in order to give acess
    to meta attributes.
    This function assumes that the 'options' of the TALES context have a
    dictionnary named 'namespace_prefix', whose keys are prefices and whose
    values are corresponding namespace URIs.
    The use of this function is (assuming that here is a Metaed object):
    here/meta/dc/version
    for example (where prefix 'dc' has been mapped to the Dublin Core 
    namespace URI in 'namespace_prefix'.
    """
    
    import advene.model._impl
        
    class MetaNameWrapper(object):
        def __init__(self, target, namespace_uri):
            self.__target = target
            self.__namespace_uri = namespace_uri
    
        def has_key(self, key):
            return (self[key] is not None)
    
        def __getitem__(self, key):
            return self.__target.getMetaData(self.__namespace_uri, key)

    class MetaNSWrapper(object):
        def __init__(self, target, context):
            self.__target = target
            options = context.globals['options'].value()
            self.__ns_dict = options.get('namespace_prefix', {})
    
        def has_key(self, key):
            return key in self.__ns_dict
    
        def __getitem__(self, key):
            if self.has_key(key):
                return MetaNameWrapper(self.__target, self.__ns_dict[key])
            else:
                return None

        def keys(self):
            return self.__ns_dict.keys()
        
    if isinstance (target, advene.model._impl.Metaed):
        r = MetaNSWrapper (target, context)
        return r
    else:
        return None

def view(target, context):

    import advene.model.viewable
    import advene.model.exception
        
    class ViewWrapper (object):

        """
        Return a wrapper around a viewable (target), having the two following
        bevaviours:
         - it is a callable, running target.view() when invoked
         - it is a dictionnary, returning a callable running target.view(key)
           on __getitem__

        The reason why all returned objects are callable is to prevent view
        evaluation when not needed (e.g., in expressions like
        here/view/foo/absolute_url)
        """

        def __init__ (self, target, context):
            if not isinstance(target, advene.model.viewable.Viewable):
                raise advene.model.exception.AdveneException ("Trying to ViewWrap a non-Viewable object %s" % target)
            self._target = target
            self._context = context

        def __call__ (self):
            return self._target.view (context=self._context)
    
        def has_key (self, key):
            v = self._target._find_named_view (key, self._context)
            return v is not None

        def __getitem__ (self, key):
            #print "getitem %s" % key
            def render ():
                return self._target.view (view_id=key, context=self._context)
            return render

        def ids (self):
            """
            Returns the ids of views from the root package which are valid for
            this object.

            Note that such IDs may not work in every context in TALES.
            """
            return self._target.getValidViews()

        def keys (self):
            """
            Returns the ids of views from the root package which are valid for
            this object.

            Note that such IDs may not work in every context in TALES.
            """
            return self._target.getValidViews()

    if isinstance (target, advene.model.viewable.Viewable):
        return ViewWrapper (target, context)
    else:
        return None

def snapshot_url (target, context):
    import advene.model.annotation
    import advene.model.fragment
    import advene.model.exception
    
    begin=""
    if isinstance(target, advene.model.annotation.Annotation):
        begin = target.fragment.begin
    elif isinstance(target, advene.model.fragment.MillisecondFragment):
        begin = target.begin
    else:
        return None
    
    options = context.globals['options'].value()
    return "%s/options/snapshot/%s" % (options['package_url'],
                                       str(begin))

def formatted (target, context):
    import advene.model.fragment
    import advene.model.exception
    import time
    
    if not isinstance(target, advene.model.fragment.MillisecondFragment):
        return None
    
    res = {
        'begin': u'--:--:--.---',
        'end'  : u'--:--:--.---'
        }
    t =  target.begin
    res['begin'] = u"%s.%03d" % (time.strftime("%H:%M:%S", time.gmtime(t / 1000)), t % 1000)
    t =  target.end
    res['end'] = u"%s.%03d" % (time.strftime("%H:%M:%S", time.gmtime(t / 1000)), t % 1000)
    return res

def first (target, context):
    """
    Return the first element of =target=, which must obviously be a list-like
    object.
    """
    return target[0]

def last (target, context):
    """
    Return the last element of =target=, which must obviously be a list-like
    object.
    """
    return target[-1]

def rest (target, context):
    """
    Return all elements of target but the first. =target= must obvioulsly be a
    list-like, sliceable object.
    """
    return target[1:]

def parsed (target, context):
    """Parse the content being passed as target.

    This method parses the data of the content according to its
    mime-type. The most common parser is an XML parser (FIXME: not
    implemented yet). It applies on a content object:

    a.content.parsed.key1

    Simple structured data
    ======================
    
    This is a simple-minded format for structured information (waiting
    for a better solution based on XML):

    The structure of the data consists in 1 line per information:
    
    key1=value1
    key2=value2

    The values are on 1 line only. URL-style escape conventions are
    used (mostly to represent the linefeed as %0a).

    It returns a dict with key/values.

    XML data
    ========

    Not implemented yet.

    @return: a data structure
    """
    import advene.model.content
    
    content=target
    if not isinstance(target, advene.model.content.Content):
        return {}
    if content.mimetype is None or content.mimetype == 'text/plain':
        # If nothing is specified, assume text/plain and return a unique
        # dict with the key 'value'
        return { 'value': content.data }
    if content.mimetype == 'x-advene/structured':
        import urllib
        
        d={}
        # FIXME: check portability of \n in win32
        for l in content.data.split("\n"):
            if len(l) == 0:
                # Ignore empty lines
                pass
            if '=' in l:
                (k, v) = l.split('=', 1)
                d[k] = urllib.unquote(v)
            else:
                print "Syntax error in content: %d"
        return d
    # FIXME: implement XML parsing
    # Last fallback:
    return { 'value': content.data }
