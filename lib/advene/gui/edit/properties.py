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
"""Generic properties editor widget.
"""

import gtk
import pango

class EditWidget(gtk.VBox):
    """Configuration edit widget.

    Adapted from (GPL) gdesklets code.
    """
    CHANGE_ENTRY = 0
    CHANGE_OPTION = 1
    CHANGE_SPIN = 2
    CHANGE_CHECKBOX = 3
    CHANGE_FILE = 4

    def __init__(self, set_config, get_config):

        # functions for setting / getting configuration values
        self.__set_config = set_config
        self.__get_config = get_config

        # name of the configurator
        self.__name = ""

        # the number of widget lines
        self.__lines = 0


        gtk.VBox.__init__(self)
        self.set_border_width(12)
        self.show()

        self.__table = gtk.Table(1, 2)
        self.__table.show()
        self.add(self.__table)

        self.__tooltips = gtk.Tooltips()


    #
    # Adds a line of widgets to the configurator. The line can be indented.
    #
    def __add_line(self, indent, w1, w2 = None):

        self.__lines += 1
        self.__table.resize(self.__lines, 2)

        if (indent): x, y = 12, 3
        else: x, y = 0, 3

        if (w2):
            self.__table.attach(w1, 0, 1, self.__lines - 1, self.__lines,
                                gtk.FILL, 0, x, y)
            self.__table.attach(w2, 1, 2, self.__lines - 1, self.__lines,
                                gtk.EXPAND | gtk.FILL, 0, 0, y)

        else:
            self.__table.attach(w1, 0, 2, self.__lines - 1, self.__lines,
                                gtk.EXPAND | gtk.FILL, 0, x, y)



    #
    # Reacts on changing a setting.
    #
    def __on_change(self, src, *args):

        property, mode = args[-2:]
        args = args[:-2]

        if (mode == self.CHANGE_ENTRY):
            value = src.get_text()

        elif (mode == self.CHANGE_OPTION):
            value = src.get_model()[src.get_active()][1]

        elif (mode == self.CHANGE_CHECKBOX):
            value = src.get_active()

        elif (mode == self.CHANGE_SPIN):
            value = src.get_value_as_int()

        elif (mode == self.CHANGE_FILE):
            file = src.get_full_path(file_must_exist = True)
            print "FILE:", file

        self.__set_config(property, value)

    #
    # Sets/returns the name of this configurator. That name will appear in the
    # notebook tab.
    #
    def set_name(self, name): self.__name = name
    def get_name(self): return self.__name

    def add_title(self, label):

        lbl = gtk.Label("")
        lbl.set_markup("<b>" + label + "</b>")
        lbl.show()
        align = gtk.Alignment()
        align.show()
        align.add(lbl)

        self.__add_line(0, align)

    def add_checkbox(self, label, property, help):

        check = gtk.CheckButton(label)
        check.show()

        self.__tooltips.set_tip(check, help)
        self.__add_line(1, check)

        value = self.__get_config(property)
        check.set_active(value)
        check.connect("toggled", self.__on_change, property,
                      self.CHANGE_CHECKBOX)



    def add_entry(self, label, property, help, passwd = 0):

        lbl = gtk.Label(label)
        lbl.show()
        entry = gtk.Entry()
        entry.show()
        align = gtk.Alignment()
        align.show()
        align.add(lbl)

        if (passwd):
            entry.set_visibility(False)
            entry.set_invisible_char(unichr(0x2022))

        self.__tooltips.set_tip(entry, help)
        self.__add_line(1, align, entry)

        value = self.__get_config(property)
        entry.set_text(value)
        entry.connect("changed", self.__on_change, property,
                      self.CHANGE_ENTRY)



    def add_spin(self, label, property, help, low, up):

        lbl = gtk.Label(label)
        lbl.show()

        align = gtk.Alignment()
        align.show()
        align.add(lbl)

        adjustment = gtk.Adjustment(0, int(low), int(up), 1, 1, 0)
        spin_button = gtk.SpinButton(adjustment, 1, 0)
        spin_button.set_numeric(True)
        spin_button.show()

        value = self.__get_config(property)

        self.__tooltips.set_tip(spin_button, help)
        self.__add_line(1, align, spin_button)

        spin_button.set_value(value)
        spin_button.connect("value-changed", self.__on_change, property,
                            self.CHANGE_SPIN)



    def add_option(self, label, property, help, options):

        lbl = gtk.Label(label)
        lbl.show()

        align = gtk.Alignment()
        align.show()
        align.add(lbl)

        value = self.__get_config(property)

        store=gtk.ListStore(str, object)
        active_iter=None
        for k, v in options.iteritems():
            i=store.append( ( k, v ) )
            if v == value:
                active_iter=i

        if active_iter is None:
            active_iter = store.get_iter_first()

        combo = gtk.ComboBox(store)
        cell = gtk.CellRendererText()
        combo.pack_start(cell, True)
        combo.add_attribute(cell, 'text', 0)
        combo.set_active_iter(active_iter)

        combo.connect("changed", self.__on_change, property, self.CHANGE_OPTION)

        self.__tooltips.set_tip(combo, help)
        self.__add_line(1, align, combo)

    def add_file_selector(self, label, property, help):

        def open_filedialog(self, on_ok, entry):
            def fd_hide(src, fselector): fselector.destroy()
            d = gtk.FileSelection()
            d.show()
            d.ok_button.connect("clicked", on_ok, d, entry)
            d.cancel_button.connect("clicked", fd_hide, d)

        def on_ok(src, fselector, entry):
            fname = fselector.get_filename()
            entry.set_text(fname)
            fselector.destroy()

        lbl = gtk.Label(label)
        lbl.show()
        align = gtk.Alignment()
        align.show()
        align.add(lbl)

        hbox = gtk.HBox()
        hbox.show()
        entry = gtk.Entry()
        entry.show()
        hbox.pack_start(entry, True, True, 0)

        btn = gtk.Button(stock = gtk.STOCK_OPEN)
        btn.show()
        hbox.pack_end(btn, True, True, 4)

        btn.connect("clicked", open_filedialog, on_ok, entry)

        value = self.__get_config(property)
        entry.set_text(value)
        entry.connect("changed", self.__on_change, property,
                      self.CHANGE_ENTRY)

        self.__tooltips.set_tip(entry, help)
        self.__tooltips.set_tip(btn, help)
        self.__add_line(1, align, hbox)

def test():
    val = {
        'string': 'String',
        'option': 'fee',
        'filename': '/tmp',
        }
    def set_config(name, value):
        val[name] = value
            
    def get_config(name):
        return val[name]

    ew=EditWidget(set_config, get_config)
    ew.set_name("Test")
    ew.add_title("Main values")
    ew.add_entry("Name", "string", "Enter a valid name")
    ew.add_option("Option", 'option', "Choose the option", {"Fee": "fee",
                                                            "Fi": "fi",
                                                            "Fo": "fo",
                                                            "Fum": "fum" })
    ew.add_file_selector("File", 'filename', "Select a filename")

    w=gtk.Window()
    w.add(ew)
    w.show_all()
    gtk.main()
        
if __name__ == '__main__':
    test()
