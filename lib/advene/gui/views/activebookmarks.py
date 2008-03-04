#
# Advene: Annotate Digital Videos, Exchange on the NEt
# Copyright (C) 2008 Olivier Aubert <olivier.aubert@liris.cnrs.fr>
#
# Advene is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Advene is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Advene; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

#"""Module displaying active time bookmarks."""

from gettext import gettext as _
import gtk
import gobject

# Advene part
import advene.core.config as config
from advene.gui.util import get_pixmap_button, dialog
from advene.gui.views import AdhocView
from advene.gui.edit.timeadjustment import TimeAdjustment
from advene.model.annotation import Annotation
from advene.model.fragment import MillisecondFragment
import advene.util.helper as helper

name="ActiveBookmarks view plugin"

def register(controller):
    controller.register_viewclass(ActiveBookmarks)

class ActiveBookmarks(AdhocView):
    """ActiveBookmarks are another way to create annotations.

    First, a time bookmark is set and associated with some text. This
    represents an incomplete annotation (the end bound is missing). Once
    the end bound is set, the triplet (t1, t2, content) is used to create
    an annotation. If no destination type was specified, then a new
    annotation type is created."""
    view_name = _("ActiveBookmarks")
    view_id = 'activebookmarks'
    tooltip= _("ActiveBookmarks")
    def __init__(self, controller=None, parameters=None, type=None):
        super(ActiveBookmarks, self).__init__(controller=controller)
        self.close_on_package_load = False
        self.contextual_actions = (
            (_("Clear"), self.clear),
            )
        self.options={
            'snapshot_width': 60,
            }
        self.controller=controller
        # self.data is a list of ActiveBookmark objects
        self.data=[]
        opt, arg = self.load_parameters(parameters)
        self.options.update(opt)
        # FIXME: think about serialization...
        #h=[ long(v) for (n, v) in arg if n == 'timestamp' ]
        #if h:
        #    self.history=h
        #for n, v in arg:
        #    if n == 'comment':
        #       t, c = v.split(':', 1)
        #       self.comments[long(t)]=c
        self.mainbox=gtk.VBox()
        self.widget=self.build_widget()
        self.type = type
        self.refresh()

    def get_type(self):
        if hasattr(self, 'chosen_type_selector'):
            return self.chosen_type_selector.get_current_element()
        else:
            return None

    def set_type(self, t):
        if hasattr(self, 'chosen_type_selector'):
            self.chosen_type_selector.set_current_element(t)
    type=property(get_type, set_type)

    def register_callback (self, controller=None):
        self.loop_id=gobject.timeout_add(1000, self.check_contents)

    def unregister_callback(self, controller=None):
        gobject.source_remove(self.loop_id)

    def get_save_arguments(self):
        # FIXME: save arguments
        #return self.options, ([ ('timestamp', t) for t in self.history ]
        return self.options, []

    def refresh(self, *p):
        self.mainbox.foreach(self.mainbox.remove)
        for w in self.data:
            self.mainbox.pack_start(w.widget, expand=False)
        self.mainbox.show_all()
        return True

    def remove(self, w):
        """Remove the given widget from mainbox.
        """
        self.data.remove(w)
        w.widget.destroy()
        return True

    def clear(self, *p):
        del self.data[:]
        self.mainbox.foreach(self.mainbox.remove)
        return True

    def append(self, t):
        b=ActiveBookmark(controller=self.controller, begin=t, end=None, content=None, close_cb=self.remove, type=self.type)
        self.data.append(b)
        self.mainbox.pack_start(b.widget, expand=False)
        b.widget.show_all()
        return True

    def check_contents(self, *p):
        """Check that annotation contents are in sync.
        """
        for wid in self.data:
            if wid.annotation is not None and wid.content != wid.annotation.content.data:
                # Mismatch in contents -> update the annotation
                wid.annotation.content.data=wid.content
                self.controller.notify('AnnotationEditEnd', annotation=wid.annotation)
        return True
                
    def update_annotation (self, annotation=None, event=None):
        l=[w for w in self.data if w.annotation == annotation ]
        if l:
            wid=l[0]
        else:
            return True
        if event == 'AnnotationEditEnd':
            # The annotation was updated. Check if an update is necessary
            if wid.begin != annotation.fragment.begin:
                wid.begin=annotation.fragment.begin
            if wid.end != annotation.fragment.end:
                wid.end=annotation.fragment.end
            if wid.content != annotation.content.data:
                wid.content=annotation.content.data
        elif event == 'AnnotationDelete':
            if wid.begin is not None and wid.end is not None:
                # Neither bound is None -> the annotation was deleted
                # (not just invalidated)
                self.remove(wid)
        return True

    def build_widget(self):
        v=gtk.VBox()
        hb=gtk.HBox()
        hb.set_homogeneous(False)

        def bookmark_current_time(b):
            p=self.controller.player
            if p.status in (p.PlayingStatus, p.PauseStatus):
                v=p.current_position_value
                # Make a snapshot
                self.controller.update_snapshot(v)
                self.append(v)
                return True

        tb=gtk.Toolbar()
        tb.set_style(gtk.TOOLBAR_ICONS)

        i=gtk.Image()
        i.set_from_file(config.data.advenefile( ( 'pixmaps', 'set-to-now.png') ))
        b=gtk.ToolButton(icon_widget=i)
        b.set_tooltip(self.controller.gui.tooltips, _("Insert a bookmark for the current video time"))
        b.connect("clicked", bookmark_current_time)
        tb.insert(b, -1)

        i=gtk.ToolItem()
        types=[ (at, self.controller.get_title(at)) for at in self.controller.package.annotationTypes ]
        types.sort(key=lambda a: a[0])
        sel=dialog.list_selector_widget(members=types)
        i.add(sel)
        self.chosen_type_selector=sel
        tb.insert(i, -1)

        hb.add(tb)
        v.pack_start(hb, expand=False)
        sw=gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.add_with_viewport(self.mainbox)
        self.scrollwindow=sw

        def mainbox_drag_received(widget, context, x, y, selection, targetType, time):
            if targetType == config.data.target_type['timestamp']:
                position=long(selection.data)
                self.append(position)
                return True
            else:
                print "Unknown target type for drop: %d" % targetType
                return False

        self.mainbox.drag_dest_set(gtk.DEST_DEFAULT_MOTION |
                                   gtk.DEST_DEFAULT_HIGHLIGHT |
                                   gtk.DEST_DEFAULT_ALL,
                                   config.data.drag_type['timestamp'],
                                   gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_COPY)
        self.mainbox.connect("drag_data_received", mainbox_drag_received)
        v.add(sw)        
        return v

class ActiveBookmark(object):
    def __init__(self, controller=None, begin=None, end=None, content=None, close_cb=None, type=None):
        self.controller=controller 
        self.annotation=None
        self.type=type
        self.widgets={}
        self.widget=self.build_widget()
        self.content=content
        self.begin=begin
        self.end=end
        self.close_cb=close_cb

    def set_begin(self, v):
        self.widgets['begin'].value=v
        self.widgets['begin'].update()
    def get_begin(self):
        return self.widgets['begin'].value
    begin=property(get_begin, set_begin)

    def set_end(self, v):
        self.widgets['end'].value=v
        self.widgets['end'].update()
    def get_end(self):
        return self.widgets['end'].value
    end=property(get_end, set_end)

    def set_content(self, v):
        if v is None:
            v=''
        self.widgets['content'].get_buffer().set_text(v)
    def get_content(self):
        b=self.widgets['content'].get_buffer()
        return b.get_text(*b.get_bounds())
    content=property(get_content, set_content)
    
    def build_widget(self):

        def drag_sent(widget, context, selection, targetType, eventTime):
            if targetType == config.data.target_type['timestamp']:
                selection.set(selection.target, 8, str(self.begin))
                return True
            else:
                print "Unknown target type for drag: %d" % targetType
                return False

        f=gtk.Frame()

        def close(b):
            if self.close_cb is not None:
                self.close_cb(self)
            return True
        b=get_pixmap_button('small_close.png', close)
        b.set_relief(gtk.RELIEF_NONE)
        f.set_label_widget(b)

        box=gtk.HBox()

        def check_annotation(v):
            if 'end' not in self.widgets:
                # We are initializing
                return True
            if self.begin is None or self.end is None:
                if self.annotation is not None:
                    # Remove the annotation
                    self.controller.delete_element(self.annotation)
                    self.annotation=None
            else:
                # Both times are valid.
                if self.annotation is None:
                    # Create the annotation
                    id_=self.controller.package._idgenerator.get_id(Annotation)
                    # Check the type
                    if self.type is None:
                        # First try the Text-annotation type. If it
                        # does not exist, create an appropriate type.
                        at=helper.get_id(self.controller.package.annotationTypes, 'annotation')
                        if at is None:
                            at=helper.get_id(self.controller.package.annotationTypes, 'active_bookmark')
                        if at is None:
                            # Create a new 'active_bookmark' type
                            schema=helper.get_id(self.controller.package.schemas, 'simple-text')
                            if schema is None and self.controller.package.schemas:
                                # Fallback on the first schema
                                schema=self.controller.package.schemas[0]
                            if schema is None:
                                self.log(_("Error: cannot find an appropriate schema to create the Active-bookmark type."))
                                return True
                            at=schema.createAnnotationType(ident='active_bookmark')
                            at.author=config.data.userid
                            at.date=self.controller.get_timestamp()
                            at.title=_("Active bookmark")
                            at.mimetype='text/plain'
                            at.setMetaData(config.data.namespace, 'color', self.controller.package._color_palette.next())
                            at.setMetaData(config.data.namespace, 'item_color', 'here/tag_color')
                            schema.annotationTypes.append(at)
                            self.controller.notify('AnnotationTypeCreate', annotationtype=at)

                        if at is None:
                            return True
                        self.type=at
                    el=self.controller.package.createAnnotation(
                        ident=id_,
                        type=self.type,
                        author=config.data.userid,
                        date=self.controller.get_timestamp(),
                        fragment=MillisecondFragment(begin=long(self.begin),
                                                     end=long(self.end)))
                    el.content.data=self.content
                    self.controller.package.annotations.append(el)
                    self.annotation=el
                    self.controller.notify('AnnotationCreate', annotation=el)
                else:
                    # Update the annotation
                    self.annotation.fragment.begin=self.begin
                    self.annotation.fragment.end=self.end
                    self.controller.notify('AnnotationEditEnd', annotation=self.annotation)
            return True

        self.widgets['begin']=OptionalTimeAdjustment(value=None, controller=self.controller, callback=check_annotation)
        self.widgets['end']=OptionalTimeAdjustment(value=None, controller=self.controller, callback=check_annotation)
        self.widgets['content']=gtk.TextView()
        self.widgets['content'].widget=self.widgets['content']
        self.widgets['content'].set_size_request(120, -1)
        box.pack_start(self.widgets['begin'].widget, expand=True)
        box.pack_start(self.widgets['content'].widget, expand=False)
        box.pack_start(self.widgets['end'].widget, expand=True)

        f.add(box)
        f.show_all()
        return f

class OptionalTimeAdjustment(object):
    """TimeAdjustment able to handle None values.
    """
    def __init__(self, value=None, controller=None, callback=None):
        self.controller=controller
        self.callback=callback
        self.widgets={}
        self.widget=self.build_widget()
        self.value=value

    def set_value(self, v):
        self._value=v
        if v is not None:
            self.widgets['nonempty'].value=v
            self.widgets['nonempty'].update()
        self.update()
        self.callback(v)

    def get_value(self):
        if self._value is not None:
            # Grab the value from TimeAdjustment
            self._value=self.widgets['nonempty'].value
        return self._value
    value=property(get_value, set_value, doc="Current time value. May be None.")

    def update(self):
        if self.value is None:
            self.widgets['empty'].widget.show()
            self.widgets['nonempty'].widget.hide()
        else:
            self.widgets['empty'].widget.hide()
            self.widgets['nonempty'].widget.show()

    def build_widget(self):
        def set_time(b):
            self.value=self.controller.player.current_position_value
            return True
        box=gtk.HBox()

        empty=get_pixmap_button('set-to-now.png', set_time)
        self.widgets['empty']=empty
        empty.widget=empty
        
        def drag_received(widget, context, x, y, selection, targetType, time):
            if targetType == config.data.target_type['timestamp']:
                self.value=long(selection.data)
                return True
            elif targetType == config.data.target_type['annotation']:
                source=self.controller.package.annotations.get(unicode(selection.data, 'utf8'))
                self.value=source.fragment.begin
            else:
                print "Unknown target type for drop: %d" % targetType
                return False
        empty.drag_dest_set(gtk.DEST_DEFAULT_MOTION |
                            gtk.DEST_DEFAULT_HIGHLIGHT |
                            gtk.DEST_DEFAULT_ALL,
                            config.data.drag_type['annotation']
                            + config.data.drag_type['timestamp'],
                            gtk.gdk.ACTION_LINK | gtk.gdk.ACTION_COPY)
        empty.connect('drag_data_received', drag_received)

        def value_changed(v):
            self.value=v
            return True
        ta=TimeAdjustment(value=0, controller=self.controller, compact=True, callback=value_changed)
        self.widgets['nonempty']=ta
        # Add a close() button
        hb=ta.widget.get_children()[-1]
        def set_to_none(b):
            self.value=None
            return True
        b=get_pixmap_button('small_close.png', set_to_none)
        b.set_relief(gtk.RELIEF_NONE)
        b.show_all()
        hb.pack_start(b, expand=False)

        for n in ('empty', 'nonempty'):
            box.pack_start(self.widgets[n].widget, expand=False)
            self.widgets[n].widget.hide()
        box.set_no_show_all(True)
        box.show()
        return box