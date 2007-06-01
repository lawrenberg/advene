#
# This file is part of Advene.
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
# along with Foobar; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
"""Dynamic montage module
"""

# Advene part
import advene.core.config as config
import advene.util.helper as helper
import advene.gui.util
from advene.gui.views import AdhocView
from advene.gui.widget import AnnotationWidget
import advene.gui.popup

from gettext import gettext as _

import gtk
import pango
import re

name="Montage view plugin"

def register(controller):
    controller.register_viewclass(Montage)

class Montage(AdhocView):
    view_name = _("Montage")
    view_id = 'montage'
    tooltip = _("Dynamic montage of annotations")
    def __init__(self, controller=None, parameters=None):
        self.close_on_package_load = False
        self.contextual_actions = (
#            (_("Save view"), self.save_view),
            (_("Clear"), self.clear),
            )
        self.options={
            }
        self.controller=controller

        self.scale=50.0

        if parameters:
            opt, arg = self.load_parameters(parameters)
            self.options.update(opt)

        # Needed by AnnotationWidget
        self.button_height = 20

        # In self.contents, we store the AnnotationWidgets We do not
        # store directly the annotations, since there may be multiple
        # occurrences of the same annotations, and we need to
        # differenciate them.
        self.contents=[]

        self.mainbox=None
        self.widget=self.build_widget()
        self.refresh()

    def get_save_arguments(self):
        return self.options, []

    def insert(self, annotation=None, position=None):
        def drag_sent(widget, context, selection, targetType, eventTime):
            # Override the standard AnnotationWidget drag_sent behaviour.
            if targetType == config.data.target_type['uri-list']:
                uri="advene:/adhoc/%d/%d" % (hash(self),
                                                  hash(widget))
                selection.set(selection.target, 8, uri)
                return True
            return False

        w=AnnotationWidget(annotation=annotation, container=self)
        w.connect("drag_data_get", drag_sent)
        if position is not None:
            self.contents.insert(position, w)
        else:
            self.contents.append(w)
        self.refresh()
        return True

    def unit2pixel(self, u):
        return long(u / self.scale)

    def pixel2unit(self, p):
        return long(p * self.scale)

    def refresh(self, *p):
        self.mainbox.foreach(self.mainbox.remove)
        self.append_dropzone(0)
        for i, a in enumerate(self.contents):
            self.append_repr(a)
            self.append_dropzone(i+1)
        self.mainbox.show_all()
        return True

    def clear(self, *p):
        del self.contents
        self.refresh()
        return True

    def get_element_color(self, element):
        """Return the gtk color for the given element.
        Return None if no color is defined.
        """
        color=self.controller.get_element_color(element)
        return advene.gui.util.name2color(color)

    def append_dropzone(self, i):
        """Append a dropzone for a given index.
        """
        def drag_received(widget, context, x, y, selection, targetType, time):
            if targetType == config.data.target_type['annotation']:
                ann=self.controller.package.annotations.get(selection.data)
                self.insert(ann, i)
                self.refresh()
                return True
            else:
                print "Unknown target type for drag: %d" % targetType
            return False

        b = gtk.Button()
        b.set_size_request(-1, self.button_height)
        b.index=i
        b.drag_dest_set(gtk.DEST_DEFAULT_MOTION |
                        gtk.DEST_DEFAULT_HIGHLIGHT |
                        gtk.DEST_DEFAULT_ALL,
                        config.data.drag_type['annotation'], gtk.gdk.ACTION_LINK)
        b.connect("drag_data_received", drag_received)

        self.mainbox.pack_start(b, expand=False, fill=False)
        return b

    def append_repr(self, w):
        self.mainbox.pack_start(w, expand=False, fill=False)
        w.update_widget()
        return w

    def build_widget(self):
        v=gtk.VBox()

        self.mainbox=gtk.HBox()

        def mainbox_drag_received(widget, context, x, y, selection, targetType, time):
            if targetType == config.data.target_type['annotation']:
                ann=self.controller.package.annotations.get(selection.data)
                self.insert(ann)
                self.refresh()
                return True
            else:
                print "Unknown target type for drag: %d" % targetType
            return False
        self.mainbox.drag_dest_set(gtk.DEST_DEFAULT_MOTION |
                        gtk.DEST_DEFAULT_HIGHLIGHT |
                        gtk.DEST_DEFAULT_ALL,
                        config.data.drag_type['annotation'], gtk.gdk.ACTION_LINK)
        self.mainbox.connect("drag_data_received", mainbox_drag_received)

        sw=gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
        sw.add_with_viewport(self.mainbox)
        self.scrollwindow=sw

        def remove_drag_received(widget, context, x, y, selection, targetType, time):
            if targetType == config.data.target_type['uri-list']:
                m=re.match('advene:/adhoc/%d/(.+)' % hash(self),
                           selection.data)
                if m:
                    h=long(m.group(1))
                    l=[ w for w in self.contents if hash(w) == h ]
                    if l:
                        # Found the element. Remove it.
                        self.contents.remove(l[0])
                        self.refresh()
                return True
            else:
                print "Unknown target type for drop: %d" % targetType
            return False

        v.pack_start(sw, expand=False)

        b=gtk.Button(stock=gtk.STOCK_REMOVE)
        self.controller.gui.tooltips.set_tip(b, _("Drop a position here to remove it from the list"))
        b.drag_dest_set(gtk.DEST_DEFAULT_MOTION |
                        gtk.DEST_DEFAULT_HIGHLIGHT |
                        gtk.DEST_DEFAULT_ALL,
                        config.data.drag_type['uri-list'], gtk.gdk.ACTION_LINK)
        b.connect("drag_data_received", remove_drag_received)
        v.pack_start(b, expand=False)

        return v
